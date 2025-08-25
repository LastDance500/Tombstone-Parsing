#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Alpha Blending Damage Overlays with Complex Mask Shapes

This script reads tombstone images from one folder and damage images from another.
Each damage image is pre-processed to generate a transparent background (assuming a fixed bg color,
e.g. white) so that only the damage details (e.g. cracks, mold, weathering) remain opaque.
Then, a complex mask is applied so that the damage patch obtains a rich, natural shape – for example,
cloud-like, slender stripe, or irregular boundaries.
For each tombstone, the script randomly selects one or more damage images (between min_overlays and max_overlays),
resizes them to a controlled size (between min_scale and max_scale relative to the tombstone dimensions),
and blends them onto the tombstone image using per-pixel alpha blending.
The overall blending weight is kept low so that the added noise is subtle while the damage details remain clearly visible.

Note: The same damage image may be chosen more than once, with each selection counting as an overlay.

Parameters:
  --tombstone_folder : Folder containing tombstone images.
  --damage_folder    : Folder containing damage images (cracks, mold, weathering).
  --output_folder    : Folder to save the resulting blended images.
  --min_overlays     : Minimum number of damage overlays per tombstone (default: 1).
  --max_overlays     : Maximum number of damage overlays per tombstone (default: 4).
  --min_scale        : Minimum scale factor for damage image relative to tombstone dimensions (default: 0.1).
  --max_scale        : Maximum scale factor for damage image relative to tombstone dimensions (default: 0.5).
  --alpha_min        : Minimum overall alpha blending value for damage (default: 0.5).
  --alpha_max        : Maximum overall alpha blending value for damage (default: 0.8).
  --mask_mode        : Mode for mask generation: "cloud", "stripe", "irregular" or "random" (default: random).
"""

import os
import cv2
import random
import argparse
import numpy as np

random.seed(42)


def create_transparent_overlay(damage_img, bg_color=(255, 255, 255), threshold=30, object_alpha=255):
    """
    Convert a damage image (e.g. cracks, mold, weathering) to BGRA, making pixels close to bg_color transparent.
    """
    damage_bgra = cv2.cvtColor(damage_img, cv2.COLOR_BGR2BGRA)
    diff = cv2.absdiff(damage_img, np.uint8(bg_color))
    diff_sum = np.sum(diff, axis=2)
    alpha_mask = np.where(diff_sum < threshold, 0, object_alpha).astype(np.uint8)
    damage_bgra[:, :, 3] = alpha_mask
    return damage_bgra


def create_irregular_mask(h, w, perturbation=0.5, blur_kernel=(9, 9)):
    """
    Generate an irregular mask using an elliptical base with smoothed random perturbations.
    """
    center_x, center_y = w / 2, h / 2
    a = (w / 2) * random.uniform(0.5, 0.7)
    b = (h / 2) * random.uniform(0.5, 0.7)
    angles = np.linspace(0, 2 * np.pi, num=360, endpoint=False)
    variations = np.random.uniform(-perturbation, perturbation, size=angles.shape)
    kernel_size = 15
    kernel = np.ones(kernel_size) / kernel_size
    smooth_variations = np.convolve(variations, kernel, mode='same')
    r_base = 1 / np.sqrt((np.cos(angles) / a) ** 2 + (np.sin(angles) / b) ** 2)
    effective_radii = r_base * (1 + smooth_variations)
    y_indices, x_indices = np.indices((h, w))
    x_coords = x_indices - center_x
    y_coords = y_indices - center_y
    distances = np.sqrt(x_coords ** 2 + y_coords ** 2)
    angles_pixel = np.arctan2(y_coords, x_coords)
    angles_pixel[angles_pixel < 0] += 2 * np.pi
    effective_radii_pixel = np.interp(angles_pixel.flatten(), angles, effective_radii).reshape(h, w)
    mask = np.zeros((h, w), dtype=np.uint8)
    mask[distances <= effective_radii_pixel] = 255
    mask = cv2.GaussianBlur(mask, blur_kernel, 0)
    return mask


def create_cloud_mask(h, w, blur_kernel=(31, 31), threshold=128):
    """
    Generate a cloud-like mask using random noise, Gaussian blur, and thresholding.
    """
    noise = np.random.rand(h, w)
    noise_img = (noise * 255).astype(np.uint8)
    blurred = cv2.GaussianBlur(noise_img, blur_kernel, 0)
    # Threshold to create cloud-like patches
    ret, cloud_mask = cv2.threshold(blurred, threshold, 255, cv2.THRESH_BINARY)
    # Optionally, further blur to smooth the boundaries
    cloud_mask = cv2.GaussianBlur(cloud_mask, (15, 15), 0)
    return cloud_mask


def create_stripe_mask(h, w, thickness_range=(5, 15), blur_kernel=(15, 15)):
    """
    Generate a slender stripe mask by drawing a random line, dilating it, and blurring.
    """
    mask = np.zeros((h, w), dtype=np.uint8)
    pt1 = (random.randint(0, w - 1), random.randint(0, h - 1))
    angle = random.uniform(0, 2 * np.pi)
    length = random.randint(min(h, w) // 2, min(h, w))
    pt2 = (int(pt1[0] + length * np.cos(angle)), int(pt1[1] + length * np.sin(angle)))
    thickness = random.randint(*thickness_range)
    cv2.line(mask, pt1, pt2, 255, thickness=thickness)
    mask = cv2.GaussianBlur(mask, blur_kernel, 0)
    return mask


def create_complex_mask(h, w, mode="random"):
    """
    Generate a complex mask according to the specified mode.
    Modes:
      - "cloud": cloud-like mask using noise.
      - "stripe": slender stripe mask.
      - "irregular": irregular elliptical mask with perturbations.
      - "random": randomly choose one of the above.
    """
    if mode == "random":
        mode = random.choice(["cloud", "stripe", "irregular"])
    if mode == "cloud":
        return create_cloud_mask(h, w)
    elif mode == "stripe":
        return create_stripe_mask(h, w)
    elif mode == "irregular":
        return create_irregular_mask(h, w)
    else:
        # Fallback to irregular
        return create_irregular_mask(h, w)


def apply_complex_mask(damage_bgra, mask_mode="random"):
    """
    Apply a complex mask to the damage image.
    The generated mask (with values 0-255) multiplies the existing alpha channel.

    Parameters:
      damage_bgra : Input damage image in BGRA format.
      mask_mode   : Mode for mask generation ("cloud", "stripe", "irregular", or "random").

    Returns:
      The BGRA damage image with modified alpha channel.
    """
    h, w, _ = damage_bgra.shape
    complex_mask = create_complex_mask(h, w, mode=mask_mode)
    complex_mask = complex_mask.astype(np.float32) / 255.0
    current_alpha = damage_bgra[:, :, 3].astype(np.float32) / 255.0
    new_alpha = np.clip(current_alpha * complex_mask, 0, 1)
    damage_bgra[:, :, 3] = (new_alpha * 255).astype(np.uint8)
    return damage_bgra


def blend_damage_patch(tombstone_img, damage_img, overall_alpha):
    """
    Blend a damage patch (with transparency) onto the tombstone image using per-pixel alpha blending.
    """
    th, tw, _ = tombstone_img.shape
    ph, pw, _ = damage_img.shape
    x = random.randint(0, th - ph)
    y = random.randint(0, tw - pw)
    roi = tombstone_img[x:x + ph, y:y + pw].astype(np.float32)
    damage_bgr = damage_img[:, :, :3].astype(np.float32)
    damage_alpha = (damage_img[:, :, 3].astype(np.float32) / 255.0) * overall_alpha
    damage_alpha = np.expand_dims(damage_alpha, axis=2)
    blended = (1 - damage_alpha) * roi + damage_alpha * damage_bgr
    tombstone_img[x:x + ph, y:y + pw] = blended.astype(np.uint8)
    return tombstone_img


def process_images(tombstone_folder, damage_folder, output_folder, min_overlays, max_overlays,
                   min_scale, max_scale, alpha_min, alpha_max, mask_mode):
    """
    Process all tombstone images by randomly overlaying pre-processed damage patches.
    The same damage image may be reused.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
    tombstone_files = [f for f in os.listdir(tombstone_folder) if f.lower().endswith(image_extensions)]
    damage_files = [f for f in os.listdir(damage_folder) if f.lower().endswith(image_extensions)]
    if not damage_files:
        print("No damage images found in the damage folder.")
        return
    for t_file in tombstone_files:
        t_path = os.path.join(tombstone_folder, t_file)
        tombstone_img = cv2.imread(t_path)
        if tombstone_img is None:
            print(f"Unable to read tombstone image: {t_path}")
            continue
        num_overlays = random.randint(min_overlays, max_overlays)
        for _ in range(num_overlays):
            damage_file = random.choice(damage_files)
            d_path = os.path.join(damage_folder, damage_file)
            damage_img = cv2.imread(d_path)
            if damage_img is None:
                print(f"Unable to read damage image: {d_path}")
                continue
            # Create transparent damage image (remove fixed background)
            damage_img = create_transparent_overlay(damage_img, bg_color=(255, 255, 255), threshold=30,
                                                    object_alpha=255)
            # Apply complex mask (cloud, stripe, or irregular) for rich shapes
            damage_img = apply_complex_mask(damage_img, mask_mode=mask_mode)
            th_img, tw_img, _ = tombstone_img.shape
            scale_factor = random.uniform(min_scale, max_scale)
            new_w = int(tw_img * scale_factor)
            new_h = int(th_img * scale_factor)
            damage_resized = cv2.resize(damage_img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            overall_alpha = random.uniform(alpha_min, alpha_max)
            tombstone_img = blend_damage_patch(tombstone_img, damage_resized, overall_alpha)
        output_path = os.path.join(output_folder, t_file)
        cv2.imwrite(output_path, tombstone_img)
        print(f"Processed {t_file} with {num_overlays} overlay(s) -> {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Blend damage images (with complex natural transparent masks) onto tombstone images using alpha blending."
    )
    parser.add_argument("--tombstone_folder", type=str, default="../images", help="Folder containing tombstone images")
    parser.add_argument("--damage_folder", type=str, default="../noises",
                        help="Folder containing damage images (cracks, mold, weathering)")
    parser.add_argument("--output_folder", type=str, default="../noised_images_3",
                        help="Folder to save the blended images")
    parser.add_argument("--min_overlays", type=int, default=2,
                        help="Minimum number of damage overlays per tombstone image (default: 2)")
    parser.add_argument("--max_overlays", type=int, default=5,
                        help="Maximum number of damage overlays per tombstone image (default: 4)")
    parser.add_argument("--min_scale", type=float, default=0.5,
                        help="Minimum scale factor for damage image relative to tombstone image (default: 0.1)")
    parser.add_argument("--max_scale", type=float, default=0.8,
                        help="Maximum scale factor for damage image relative to tombstone image (default: 0.5)")
    parser.add_argument("--alpha_min", type=float, default=0.6,
                        help="Minimum overall alpha value for blending (default: 0.5)")
    parser.add_argument("--alpha_max", type=float, default=0.8,
                        help="Maximum overall alpha value for blending (default: 0.8)")
    parser.add_argument("--mask_mode", type=str, default="random",
                        help='Mask generation mode: "cloud", "stripe", "irregular", or "random" (default: random)')
    args = parser.parse_args()
    process_images(args.tombstone_folder, args.damage_folder, args.output_folder,
                   args.min_overlays, args.max_overlays, args.min_scale, args.max_scale,
                   args.alpha_min, args.alpha_max, args.mask_mode)


if __name__ == "__main__":
    main()
