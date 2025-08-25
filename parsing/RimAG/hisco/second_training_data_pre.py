import json
import random
import re
import math
import requests
import time
import tqdm
from PIL import Image
from PIL.ExifTags import GPSTAGS

random.seed(42)


def haversine_distance(coord1, coord2):
    lat1, lon1 = map(math.radians, coord1)
    lat2, lon2 = map(math.radians, coord2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371
    return c * r


def get_exif(filename):
    try:
        image = Image.open(filename)
        image.verify()
        exif = image._getexif()
    except (IOError, ValueError) as e:
        print(f"Error reading EXIF from {filename}: {e}")
        return None
    return exif


def get_geotagging(exif):
    if not exif:
        raise ValueError("No EXIF metadata found")
    geotagging = {}
    gps_info = exif.get(34853)
    if gps_info:
        for key, val in GPSTAGS.items():
            if key in gps_info:
                geotagging[val] = gps_info[key]
    return geotagging


def get_coordinates(geotags):
    if 'GPSLatitude' not in geotags or 'GPSLongitude' not in geotags:
        return None
    try:
        lat = [float(x) for x in geotags['GPSLatitude']]
        lon = [float(x) for x in geotags['GPSLongitude']]
        latitude = lat[0] + lat[1] / 60 + lat[2] / 3600
        longitude = lon[0] + lon[1] / 60 + lon[2] / 3600

        if geotags.get('GPSLatitudeRef', 'N') != 'N':
            latitude = -latitude
        if geotags.get('GPSLongitudeRef', 'E') != 'E':
            longitude = -longitude

        return (latitude, longitude)
    except (TypeError, ValueError) as e:
        print(f"Coordinate conversion error: {e}")
        return None


def extract_hco_names(peman_text):
    """
    从 tombstone 注释文本中提取职业名称。
    正则表达式匹配格式为 :nam "xxx" :hco "yyy"，返回的列表为所有匹配中的名称部分（即 "xxx"）。
    """
    pattern = r':nam\s*"([^"]+?)"\s*:hco\s*"([^"]+?)"'
    matches = re.findall(pattern, peman_text, re.DOTALL | re.MULTILINE)
    hco_names = [match[0] for match in matches]
    return hco_names


def extract_idx(annotation):
    m = re.search(r'\(t(\d{5})\s*/', annotation)
    if m:
        return f"t{m.group(1)}"
    else:
        return None


def get_hisco_code(occupation_name):
    """
    调用 HISCO API 查找职业对应的 HISCO 代码。
    从 hisco.uri 中截取最后一段数字，如 14190，并返回 {occupation_name: "14190"}。
    """
    base_url = "https://api.coret.org/hisco/lookup.php"
    params = {
        "q": occupation_name,
        "limit": 1,
        "pretty": 1
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"HISCO API request error: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"HISCO API response JSON decode error: {e}")
        return {}

    if not isinstance(data, list) or len(data) == 0:
        return {}

    first_item = data[0]
    hisco_obj = first_item.get("hisco")
    if not hisco_obj:
        return {}

    hisco_uri = hisco_obj.get("uri", "")
    if not hisco_uri:
        return {}

    hisco_code = hisco_uri.rsplit('/', 1)[-1]
    return {occupation_name: hisco_code}


def search_hisco_code(occupation_name):
    """
    优化 HISCO 搜索逻辑：
    如果 occupation_name 包含多个单词，则依次采用 1-gram、2-gram、3-gram 的连续子串进行搜索，
    收集所有子串的搜索结果，并返回合并后的字典。
    如果 occupation_name 只有一个单词，则直接查询。
    """
    tokens = occupation_name.split()
    results = {}
    if len(tokens) <= 1:
        return get_hisco_code(occupation_name)

    # 对于 1-gram, 2-gram, 3-gram 的连续子串均进行搜索，收集所有结果
    for n in [1, 2, 3]:
        if len(tokens) < n:
            continue
        for i in range(len(tokens) - n + 1):
            candidate = " ".join(tokens[i:i + n])
            candidate_result = get_hisco_code(candidate)
            if candidate_result:
                results.update(candidate_result)
    return results


def read_file(file_path):
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        return None
    return content


def process_train():
    train_file = "/Users/xiaozhang/code/Tombstone-Parsing/data/annotation/tombs_grounded.txt"
    train_content = read_file(train_file)
    if train_content is None:
        print("Error reading training file, terminating program.")
        return
    train_annotations = train_content.strip().split("\n\n")
    train_index = [f"t{i:05d}" for i in range(len(train_annotations))]
    train_data = []

    for i in tqdm.tqdm(range(min(600, len(train_annotations))), desc="Processing train data"):
        idx = train_index[i]
        annotation = train_annotations[i]
        hco_names = extract_hco_names(annotation)

        # 针对每个职业名称采用 n-gram 搜索逻辑，收集所有子串的结果
        occupation_code_dict = {}
        for name in hco_names:
            code_dict = search_hisco_code(name)
            if code_dict:
                occupation_code_dict.update(code_dict)

        entry = {
            "messages": [
                {
                    "from": "human",
                    "value": f"<image>Generate a meaning representation in PENMAN format for this image of a tombstone. The HISCO codes that may be used are: {occupation_code_dict}.",
                },
                {
                    "from": "gpt",
                    "value": annotation,
                },
            ],
            "images": [f"/projects/0/prjs0885/LLaMA-Factory/tombreader/data/{idx}.jpg"]
        }
        train_data.append(entry)

    try:
        with open('tomb_parsing_second_train_hisco.json', 'w', encoding='utf-8') as json_file:
            json.dump(train_data, json_file, ensure_ascii=False, indent=4)
        print("Training data saved to tomb_parsing_second_train_hisco.json.")
    except IOError as e:
        print(f"Error saving training data: {e}")


def process_test():
    first_step_file = "/Users/xiaozhang/code/multi-modal-PMB/tomb/geo_search/first_step_test.txt"
    first_step_content = read_file(first_step_file)
    if first_step_content is None:
        print("Error reading first step test file, terminating program.")
        return
    first_step_annotations = first_step_content.strip().split("\n\n")
    test_indices = []
    for annotation in first_step_annotations:
        idx = extract_idx(annotation)
        if idx:
            test_indices.append(idx)
        else:
            print("Warning: no index found")

    grounded_file = "/Users/xiaozhang/code/Tombstone-Parsing/data/annotation/tombs_grounded.txt"
    grounded_content = read_file(grounded_file)
    if grounded_content is None:
        print("Error reading grounded file, terminating program.")
        return
    grounded_annotations = grounded_content.strip().split("\n\n")
    grounded_mapping = {}
    for annotation in grounded_annotations:
        idx = extract_idx(annotation)
        if idx:
            grounded_mapping[idx] = annotation

    test_data = []

    for idx in tqdm.tqdm(test_indices, desc="Processing test data"):
        if idx not in grounded_mapping:
            print(f"Index {idx} not found in grounded file. Skipping.")
            continue

        annotation = grounded_mapping[idx]
        hco_names = extract_hco_names(annotation)

        filename = f"/Users/xiaozhang/code/multi-modal-PMB/tomb/tombreader/data/{idx}.jpg"
        try:
            exif = get_exif(filename)
            geotags = get_geotagging(exif)
            photo_coords = get_coordinates(geotags)
            if photo_coords is None:
                print(f"GPS data for {filename} not found. Proceeding without distance filtering.")
        except FileNotFoundError:
            print(f"File {filename} not found. Proceeding without file...")
            continue
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue

        occupation_code_dict = {}
        for name in hco_names:
            code_dict = search_hisco_code(name)
            if code_dict:
                occupation_code_dict.update(code_dict)

        entry = {
            "messages": [
                {
                    "from": "human",
                    "value": f"<image>Generate a meaning representation in PENMAN format for this image of a tombstone. The HISCO codes that may be used are: {occupation_code_dict}.",
                },
                {
                    "from": "gpt",
                    "value": annotation,
                },
            ],
            "images": [f"/projects/0/prjs0885/LLaMA-Factory/tombreader/data/{idx}.jpg"]
        }
        test_data.append(entry)

    try:
        with open('tomb_parsing_second_test_hisco.json', 'w', encoding='utf-8') as json_file:
            json.dump(test_data, json_file, ensure_ascii=False, indent=4)
        print("Testing data saved to tomb_parsing_second_test_hisco.json.")
    except IOError as e:
        print(f"Error saving testing data: {e}")


if __name__ == "__main__":
    mode = "test"
    if mode == "train":
        process_train()
    elif mode == "test":
        process_test()
    else:
        print("Invalid mode. Please choose 'train' or 'test'.")
