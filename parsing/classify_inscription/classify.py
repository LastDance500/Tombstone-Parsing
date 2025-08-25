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
    "Qwen/Qwen2.5-VL-72B-Instruct",
    torch_dtype="auto",
    device_map="auto"
)
model.eval()

min_pixels = 256 * 28 * 28
max_pixels = 1280 * 28 * 28
processor = AutoProcessor.from_pretrained("Qwen/Qwen2.5-VL-72B-Instruct", min_pixels=min_pixels, max_pixels=max_pixels)


def process_image(image_path):

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
                        f"Please provide a structured linguistic analysis of the tombstone {image_path}. "
                        "Strictly follow the format below and do not include any explanations or additional text:\n\n"
                        "1. Language (e.g., Dutch, English, etc.):\n"
                        "2. Font Style (e.g., Times New Roman, Serif, Sans-serif, etc.):\n"
                        "3. Complex Coreference to someone (Yes or No， Only answer 'Yes' if there is ambiguous or multi-step reference between entities, beyond simple possessives like 'our father'):\n"
                        "4. Rhetorical Devices (Yes or No):\n"
                        "5. Syntactic Complexity (Yes or No):\n"
                        "6. Figurative Language (Yes or No):\n"
                        "7. Pronouns (Yes or No):\n"
                        "8. Abbreviated Names (but not person names) (Yes or No):\n"
                        "9. Multiple Persons Names (Yes or No):\n"
                    ),
                },
            ],
        }
    ]

    # Prepare inputs for inference
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
    # Load existing results if the JSON file already exists
    if os.path.exists(output_json_path):
        with open(output_json_path, "r", encoding="utf-8") as json_file:
            results = json.load(json_file)
    else:
        results = {}

    total_files = len([f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
    processed_files = len(results)
    print(f"Total files to process: {total_files}")
    print(f"Already processed files: {processed_files}")

    for idx, file_name in enumerate(os.listdir(folder_path), start=1):
        file_path = os.path.join(folder_path, file_name)
        if (
                file_name.lower().endswith(('.png', '.jpg', '.jpeg'))  # Only process image files
                and file_name not in results  # Skip already processed files
        ):
            try:
                print(f"Processing ({idx}/{total_files}): {file_name}")
                response = process_image(file_path)
                results[file_name] = response
            except Exception as e:
                print(f"Error processing {file_name}: {e}")
                results[file_name] = {"error": str(e)}

            # Incremental save after processing each file
            with open(output_json_path, "w", encoding="utf-8") as json_file:
                json.dump(results, json_file, ensure_ascii=False, indent=4)

            print(f"Saved progress: {file_name} processed.")

    print(f"Processing complete. Results saved to {output_json_path}")


# Example usage
folder_path = "/gpfs/work4/0/prjs0885/Tombstone-Parsing/data/split/test_images"
output_json_path = "qwen_72b_answer_new_2.json"

process_folder(folder_path, output_json_path)
