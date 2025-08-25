import json
import random
import shutil
import os

random.seed(42)

with open("../annotation/tombs_grounded.txt", encoding="utf-8") as f:
    lines = f.read()

data = lines.split("\n\n")
index = [f"t{i:05d}" for i in range(len(data))]

combined = list(zip(index, data))
random.shuffle(combined)

index, data = zip(*combined)

train_data = []
for i in range(600):
    idx = index[i]
    d = data[i]
    train_data.append({
        "messages": [
            {
                "from": "human",
                "value": "<image>Generate a meaning representation in PENMAN format for this image of a tombstone.",
            },
            {
                "from": "gpt",
                "value": f"{d}",
            },
        ],
        "images": [
            f"/projects/0/prjs0885/LLaMA-Factory/tombreader/data/{idx}.jpg",
        ]
    })

train_file_path = 'tomb_parsing_train.json'
with open(train_file_path, 'w') as json_file:
    json.dump(train_data, json_file)

test_data = []
for i in range(600, len(data)):
    idx = index[i]
    d = data[i]
    test_data.append({
        "messages": [
            {
                "from": "human",
                "value": "<image>Generate a meaning representation in PENMAN format for this image of a tombstone.",
            },
            {
                "from": "gpt",
                "value": f"{d}",
            },
        ],
        "images": [
            f"/projects/0/prjs0885/LLaMA-Factory/tombreader/data/{idx}.jpg",
        ]
    })

test_file_path = 'tomb_parsing_test.json'
with open(test_file_path, 'w') as json_file:
    json.dump(test_data, json_file)

source_dir = "../images"
train_dest_dir = "train_images"
test_dest_dir = "test_images"

os.makedirs(train_dest_dir, exist_ok=True)
os.makedirs(test_dest_dir, exist_ok=True)

for i in range(600):
    idx = index[i]
    src_file = os.path.join(source_dir, f"{idx}.jpg")
    dst_file = os.path.join(train_dest_dir, f"{idx}.jpg")
    if os.path.exists(src_file):
        shutil.copy(src_file, dst_file)
    else:
        print(f"Train image {src_file} not found!")

for i in range(600, len(data)):
    idx = index[i]
    src_file = os.path.join(source_dir, f"{idx}.jpg")
    dst_file = os.path.join(test_dest_dir, f"{idx}.jpg")
    if os.path.exists(src_file):
        shutil.copy(src_file, dst_file)
    else:
        print(f"Test image {src_file} not found!")
