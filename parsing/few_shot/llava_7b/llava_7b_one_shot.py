import json
import os
import torch
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor, pipeline
from qwen_vl_utils import process_vision_info

# Set seed for reproducibility
torch.manual_seed(1234)

# Select device dynamically
device = "cuda" if torch.cuda.is_available() else "cpu"

# ===== Qwen2.5-VL 模型及其 processor（用于 mode="qwen"） =====
model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2.5-VL-7B-Instruct",
    torch_dtype="auto",
    device_map="auto"
)
model.eval()

min_pixels = 256 * 28 * 28
max_pixels = 1280 * 28 * 28
processor = AutoProcessor.from_pretrained("Qwen/Qwen2.5-VL-7B-Instruct", min_pixels=min_pixels, max_pixels=max_pixels)

# ===== llava 模型 pipeline（用于 mode="llava"） =====
llava_pipe = pipeline("image-text-to-text", model="llava-hf/llava-v1.6-mistral-7b-hf")

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
"""


def process_image(image_path, amr_text,
                  mode="qwen",
                  one_shot_path="/gpfs/work4/0/prjs0885/Tombstone-Parsing/data/split/train_images/t00004.jpg"):
    """
    根据指定的 mode 调用 Qwen2.5-VL 或 llava 模型对输入图像进行处理生成 AMR 表示。

    参数:
      image_path: 目标图像路径（或者 URL）
      amr_text: 用于提示的 AMR 示例文本
      mode: "qwen" 使用 Qwen2.5-VL 模型；"llava" 使用 llava pipeline
      one_shot_path: 参考图像路径（在 Qwen 模式下作为 one-shot 示例，在 llava 模式下会作为 URL 字段传入）

    返回:
      生成的 AMR 表示文本。
    """
    if mode == "qwen":
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": one_shot_path,
                    },
                    {
                        "type": "image",
                        "image": image_path,  # Can be a local path or URL
                    },
                    {
                        "type": "text",
                        "text": (
                            "Below are one example of a meaning representation in PENMAN format for a tombstone in the first image:\n"
                            f"{amr_text}\n\n"
                            f"Generate a meaning representation in PENMAN format for the tombstone in the second image ({os.path.basename(image_path).strip()})."
                            " Don't give any other text or explanations."
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

    elif mode == "llava":
        # 构造与 llava 示例类似的消息格式。注意 llava pipeline 期望图像字段使用 "url" 键。
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "url": one_shot_path,  # 如果是本地文件，请确保 llava 模型支持本地路径，或者改为 URL
                    },
                    {
                        "type": "image",
                        "url": image_path,
                    },
                    {
                        "type": "text",
                        "text": (
                            "Below is one example of a meaning representation in PENMAN format for a tombstone in the first image:\n"
                            f"{amr_text}\n\n"
                            f"Generate a meaning representation in PENMAN format for the tombstone in the second image ({os.path.basename(image_path).strip()})."
                            " Don't give any other text or explanations."
                        ),
                    },
                ],
            }
        ]
        # 调用 llava pipeline 进行生成
        out = llava_pipe(text=messages, max_new_tokens=512)
        # 返回生成的文本（假设返回格式与示例一致）
        return out[0]['generated_text']

    else:
        raise ValueError("Unsupported mode. Choose either 'qwen' or 'llava'.")


def process_folder(folder_path, amr_text, output_json_path, mode="qwen",
                   one_shot_path="/gpfs/work4/0/prjs0885/Tombstone-Parsing/data/split/train_images/t00004.jpg"):

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
                file_name.lower().endswith(('.png', '.jpg', '.jpeg'))  # 仅处理图像文件
                and file_name not in results  # 跳过已处理文件
        ):
            try:
                print(f"Processing ({idx}/{total_files}): {file_name}")
                response = process_image(file_path, amr_text, mode=mode, one_shot_path=one_shot_path)
                results[file_name] = response
            except Exception as e:
                print(f"Error processing {file_name}: {e}")
                results[file_name] = {"error": str(e)}

            # 每处理完一个文件就保存一次结果
            with open(output_json_path, "w", encoding="utf-8") as json_file:
                json.dump(results, json_file, ensure_ascii=False, indent=4)

            print(f"Saved progress: {file_name} processed.")

    print(f"Processing complete. Results saved to {output_json_path}")


# ==================== 示例用法 ====================
folder_path = "/gpfs/work4/0/prjs0885/Tombstone-Parsing/data/split/test_images"
output_json_path = "llava_7b_one_shot.json"

# 若使用 Qwen2.5-VL 模型：
# process_folder(folder_path, amr, output_json_path, mode="qwen")

# 若使用 llava 模型：
process_folder(folder_path, amr, output_json_path, mode="llava")
