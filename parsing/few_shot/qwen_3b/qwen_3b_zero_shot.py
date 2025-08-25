import json
import os
import torch
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info

# Set seed for reproducibility
torch.manual_seed(1234)

# Select device dynamically
device = "cuda" if torch.cuda.is_available() else "cpu"

# Load model and processor
model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2.5-VL-3B-Instruct",
    torch_dtype="auto",
    device_map="auto"
)
model.eval()

min_pixels = 256 * 28 * 28
max_pixels = 1280 * 28 * 28
processor = AutoProcessor.from_pretrained("Qwen/Qwen2-VL-3B-Instruct", min_pixels=min_pixels, max_pixels=max_pixels)

def process_image(image_path):
    # Prepare messages with image and text
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "image": image_path,
                },
                {
                    "type": "text",
                    "text": (
                        f"Generate a meaning representation in PENMAN format for this image of a tombstone."
                    ),
                },
            ],
        }
    ]

    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)

    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )
    inputs = inputs.to(device)

    # Generate response with controlled decoding parameters
    generated_ids = model.generate(
        **inputs,
        max_new_tokens=512,  # Increased max_new_tokens for AMR
        temperature=0.7,  # Lower temperature for more focused output
        top_p=0.9,  # Nucleus sampling for diversity
        repetition_penalty=1.2,  # Penalize repetition
    )
    generated_ids_trimmed = [
        out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    output_text = processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )

    return output_text[0]


def process_folder(folder_path, output_json_path):
    results = {}
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path) and file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
            try:
                print(f"Processing: {file_path}")
                response = process_image(file_path)
                results[file_name] = response
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                results[file_name] = {"error": str(e)}

    # Save results to a JSON file
    with open(output_json_path, "w", encoding="utf-8") as json_file:
        json.dump(results, json_file, ensure_ascii=False, indent=4)

    print(f"Results saved to {output_json_path}")


folder_path = "/gpfs/work4/0/prjs0885/Tombstone-Parsing/data/split/test_images"
output_json_path = "qwen_3b_zero_shot.json"

process_folder(folder_path, output_json_path)
