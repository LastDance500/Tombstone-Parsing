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
processor = AutoProcessor.from_pretrained("Qwen/Qwen2.5-VL-3B-Instruct", min_pixels=min_pixels, max_pixels=max_pixels)

# Example AMR representation
amr = """
(t00004 / tombstone.n.01
        :ent (x1 / female.n.02
                 :nam "TIETJE SPOELMAN"
                 :pob (x2 / city.n.01
                          :nam "GRONINGEN"
                          :geo "2755251")
                 :dob (x3 / date.n.05
                          :dom "27"
                          :moy "10"
                          :yoc "1912")
                 :pod x2
                 :dod (x4 / date.n.05
                          :dom "28"
                          :moy "07"
                          :yoc "1933")
                 :rol (x5 / daughter.n.01
                          :tgt (x6 / person.n.01
                                   :nam "JOHS. SPOELMAN")
                          :tgt (x7 / person.n.01
                                   :nam "F. SPOELMAN_PENNINGA")))
        :ent (x8 / male.n.02
                 :nam "JOHANNES SPOELMAN"
                 :equ x6
                 :pob (x9 / village.n.02
                          :nam "ROHEL"
                          :geo "2747984")
                 :dob (x10 / date.n.05
                           :dom "17"
                           :moy "04"
                           :yoc "1871")
                 :pod x2
                 :dod (x11 / date.n.05
                           :dom "14"
                           :moy "05"
                           :yoc "1935")
                 :rol (x12 / husband.n.01
                           :tgt x7))
        :ent (x13 / female.n.02
                  :nam "FROUKTJE PENNINGA"
                  :equ x7
                  :pob (x14 / village.n.02
                            :nam "VISVLIET"
                            :geo "2745471")
                  :dob (x15 / date.n.05
                            :dom "17"
                            :moy "10"
                            :yoc "1876")
                  :pod x2
                  :dod (x16 / date.n.05
                            :dom "28"
                            :moy "09"
                            :yoc "1963")
                  :rol (x17 / wife.n.01
                            :tgt x8)))

(t00007 / tombstone.n.01
        :ent (x1 / male.n.02
                 :rol (x2 / husband.n.01)
                 :rol (x3 / father.n.01)
                 :nam "PIETER AGEMA"
                 :dob (x4 / date.n.05
                          :dom "17"
                          :moy "09"
                          :yoc "1873")
                 :pob (x5 / village.n.02
                          :nam "KOLLUMERPOMP"
                          :geo "2752522")
                 :dod (x6 / date.n.05
                          :dom "08"
                          :moy "03"
                          :yoc "1940")
                 :pod (x7 / city.n.01
                          :nam "GRONINGEN"
                          :geo "2755251")
                 :rol (x8 / husband.n.01
                          :tgt (x9 / person.n.01
                                   :nam "L. ZIJLSTRA")))
        :ent (x10 / female.n.02
                  :rol (x11 / mother.n.01)
                  :nam "LEENTJE ZIJLSTRA"
                  :equ x9
                  :dob (x12 / date.n.05
                            :dom "11"
                            :moy "06"
                            :yoc "1879")
                  :pob (x13 / village.n.02
                            :nam "ZWAGERVEEN"
                            :geo "2743583")
                  :dod (x14 / date.n.05
                            :dom "05"
                            :moy "01"
                            :yoc "1972")
                  :pod (x15 / village.n.02
                            :nam "APPELSCHA"
                            :geo "2759698")))
                            
(t00010 / tombstone.n.01
        :ent (x1 / male.n.02
                 :nam "GERKE MIDDEL"
                 :dob (x2 / date.n.05
                          :dom "30"
                          :moy "08"
                          :yoc "1890")
                 :dod (x3 / date.n.05
                          :dom "14"
                          :moy "12"
                          :yoc "1935"))
        :ent (x4 / male.n.02
                 :rol (x5 / father.n.01)
                 :rol (x6 / grandfather.n.01)
                 :nam "ROELF MIDDEL"
                 :dob (x7 / date.n.05
                          :dom "04"
                          :moy "04"
                          :yoc "1865")
                 :dod (x8 / date.n.05
                          :dom "13"
                          :moy "10"
                          :yoc "1961")))
                          
(t00011 / tombstone.n.01
        :ent (x1 / male.n.02
                 :nam "LAMMERT LEERTOUWER"
                 :dob (x2 / date.n.05
                          :dom "01"
                          :moy "03"
                          :yoc "1877")
                 :dod (x3 / date.n.05
                          :dom "04"
                          :moy "12"
                          :yoc "1938")
                 :rol (x4 / husband.n.01
                          :tgt (x5 / female.n.02
                                   :nam "G. KROL")))
        :ent (x6 / female.n.02
                 :equ x5
                 :nam "GEESJE KROL"
                 :dob (x7 / date.n.05
                          :dom "08"
                          :moy "03"
                          :yoc "1876")
                 :dod (x8 / date.n.05
                          :dom "28"
                          :moy "09"
                          :yoc "1961")))
                          
(t00768 / tombstone.n.01
        :ent (x1 / male.n.02
                 :nam "WILLEM JOLING"
                 :pob (x2 / village.n.02
                          :nam "WEERDINGE"
                          :geo "2744927")
                 :dob (x3 / date.n.05
                          :dom "27"
                          :moy "06"
                          :yoc "1920")
                 :pod (x4 / location.n.01
                          :equ x2)
                 :dod (x5 / date.n.05
                          :dom "11"
                          :moy "05"
                          :yoc "1922")
                 :rol (x6 / son.n.01
                          :tgt (x7 / male.n.02
                                   :nam "HARM JOLING"
                                   :sfx "WZN")
                          :tgt (x8 / person.n.01
                                   :nam "J. SIKKEN"))))
"""

def process_image(image_path, amr_text):
    first_path = "/gpfs/work4/0/prjs0885/Tombstone-Parsing/data/split/train_images/t00004.jpg"
    second_path = "/gpfs/work4/0/prjs0885/Tombstone-Parsing/data/split/train_images/t00007.jpg"
    third_path = "/gpfs/work4/0/prjs0885/Tombstone-Parsing/data/split/train_images/t00010.jpg"
    fourth_path = "/gpfs/work4/0/prjs0885/Tombstone-Parsing/data/split/train_images/t00011.jpg"
    firth_path = "/gpfs/work4/0/prjs0885/Tombstone-Parsing/data/split/train_images/t00768.jpg"

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "image": first_path,  # one shot image
                },
                {
                    "type": "image",
                    "image": second_path,  # two shot image
                },
                {
                    "type": "image",
                    "image": third_path,  # third shot image
                },
                {
                    "type": "image",
                    "image": fourth_path,  # third shot image
                },
                {
                    "type": "image",
                    "image": firth_path,  # third shot image
                },
                {
                    "type": "image",
                    "image": image_path,  # Can be path or URL
                },

                {
                    "type": "text",
                    "text": (
                        "Below are five examples of meaning representations in PENMAN format for tombstones in the first five images seperately:\n"
                        f"{amr_text}\n\n"
                        f"Generate a meaning representation in PENMAN format for the tombstone in the fifth image ({os.path.basename(image_path).strip()})."
                        f"Following the structure and don't give any other text or explanations."
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


def process_folder(folder_path, amr_text, output_json_path):
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
                response = process_image(file_path, amr_text)
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
output_json_path = "qwen_3b_five_shot.json"

process_folder(folder_path, amr, output_json_path)
