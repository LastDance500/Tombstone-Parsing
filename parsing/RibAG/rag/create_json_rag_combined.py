import json
import random
import re
import requests
import math
import tqdm
import os
import shutil
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import argparse

random.seed(42)

# ----------------------- Geo 相关函数 -----------------------

def haversine_distance(coord1, coord2):
    """计算两个地理坐标之间的距离（单位：公里）。"""
    lat1, lon1 = map(math.radians, coord1)
    lat2, lon2 = map(math.radians, coord2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # 地球半径，单位：公里
    return c * r

def get_exif(filename):
    """从图像文件中读取 EXIF 信息。"""
    try:
        image = Image.open(filename)
        image.verify()
        exif = image._getexif()
    except (IOError, ValueError) as e:
        print(f"Error reading EXIF from {filename}: {e}")
        return None
    return exif

def get_geotagging(exif):
    """从 EXIF 数据中提取 GPS 信息。"""
    if not exif:
        raise ValueError("No EXIF metadata found")
    geotagging = {}
    gps_info = exif.get(34853)  # GPS 信息通常存储在 tag 34853 下
    if gps_info:
        for key, val in GPSTAGS.items():
            if key in gps_info:
                geotagging[val] = gps_info[key]
    return geotagging

def get_coordinates(geotags):
    """将 GPS 信息转换为经纬度坐标。"""
    if 'GPSLatitude' not in geotags or 'GPSLongitude' not in geotags:
        return None
    try:
        lat = [float(coord) for coord in geotags['GPSLatitude']]
        lon = [float(coord) for coord in geotags['GPSLongitude']]
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

def get_geocodes(place_name, username, photo_coords, max_distance=10000):
    """
    调用 GeoNames API 获取地名对应的地理编码。
    返回格式为: {place_name: geocode}
    """
    base_url = "http://api.geonames.org/searchJSON"
    params = {
        'q': place_name,
        'maxRows': 30,
        'username': username
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"GeoNames API request error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"GeoNames API response JSON decode error: {e}")
        return None

    closest_place = None
    min_distance = float('inf')
    for item in data.get('geonames', []):
        try:
            p_name = item.get('name')
            geocode = item.get('geonameId')
            lat = float(item.get('lat', 0.0))
            lon = float(item.get('lng', 0.0))
            place_coords = (lat, lon)
            distance = haversine_distance(photo_coords, place_coords)
            if distance < min_distance:
                min_distance = distance
                closest_place = (p_name, geocode)
        except (KeyError, TypeError, ValueError) as e:
            print(f"Error processing GeoNames data: {e}")
            continue

    if closest_place and min_distance <= max_distance:
        return {place_name: closest_place[1]}
    return {}

# ----------------------- HISCO 相关函数 -----------------------

def clean_occupation_string(occupation):
    """
    将括号内外的内容分开，并用逗号连接。
    例如:
      "Echtgenote (Wife)" -> "Echtgenote, Wife"
      "Farmer (Bartender) (Singer)" -> "Farmer, Bartender, Singer"
    """
    inside_parentheses = re.findall(r'\(([^)]*)\)', occupation)
    outside_parentheses = re.sub(r'\(.*?\)', '', occupation).strip()
    parts = []
    if outside_parentheses:
        parts.append(outside_parentheses.strip())
    parts += [item.strip() for item in inside_parentheses if item.strip()]
    return ', '.join(parts)

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

# ----------------------- 文件读取函数 -----------------------

def read_files():
    """
    读取三个文件：
      1) tombs_grounded.txt —— 墓志铭文本数据
      2) place_ocr/ocr_result.json —— 地名 OCR 结果
      3) profession_ocr/ocr_result.json —— 职业 OCR 结果
    """
    try:
        with open("../../../data/annotation/tombs_grounded.txt", encoding="utf-8") as f:
            lines = f.read()
    except FileNotFoundError:
        print("File '../../../data/annotation/tombs_grounded.txt' not found.")
        return None, None, None

    try:
        with open('../place_ocr/ocr_result.json', 'r', encoding='utf-8') as file:
            place_dict = json.load(file)
    except FileNotFoundError:
        print("File '../place_ocr/ocr_result.json' not found.")
        place_dict = {}

    try:
        with open('../profession_ocr/ocr_result.json', 'r', encoding='utf-8') as file:
            occ_dict = json.load(file)
    except FileNotFoundError:
        print("File '../profession_ocr/ocr_result.json' not found.")
        occ_dict = {}

    return lines, place_dict, occ_dict

# ----------------------- 主函数 -----------------------

def main(dataset_mode):
    """
    dataset_mode 参数可选值:
      "train" - 只生成训练数据（前600条），不会生成测试数据；
      "test"  - 只生成测试数据（后续数据），不会生成训练数据；
      "both"  - 同时生成训练数据和测试数据。
    """
    lines, place_dict, occ_dict = read_files()
    if lines is None:
        print("Error reading files, terminating program.")
        return

    data_entries = lines.strip().split("\n\n")
    index_list = [f"t{i:05d}" for i in range(len(data_entries))]

    # 随机打乱顺序
    combined = list(zip(index_list, data_entries))
    random.shuffle(combined)
    index_list, data_entries = zip(*combined)

    train_data = []
    test_data = []
    total_entries = len(data_entries)

    for i in tqdm.tqdm(range(total_entries)):
        # 如果只生成训练数据，则跳过后600条；如果只生成测试数据，则跳过前600条
        if dataset_mode == "train" and i >= 600:
            continue
        if dataset_mode == "test" and i < 600:
            continue

        idx = index_list[i]
        text_content = data_entries[i]

        # ----------------- 处理 Geo 信息 -----------------
        place_name = place_dict.get(f"{idx}.jpg")
        place_code_dict = {}
        if place_name:
            # 如果存在多个地名，以逗号分割
            place_names = [p.strip() for p in place_name.split(',')]
        else:
            print(f"Place name for {idx}.jpg not found. Proceeding without place name...")
            place_names = []

        filename = f"/projects/0/prjs0885/LLaMA-Factory/tombreader/data/{idx}.jpg"
        try:
            exif = get_exif(filename)
            geotags = get_geotagging(exif)
            photo_coords = get_coordinates(geotags)
            if photo_coords is None:
                print(f"GPS data for {filename} not found. Proceeding without GPS data...")
        except FileNotFoundError:
            print(f"File {filename} not found. Proceeding without geo data...")
            photo_coords = None
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            photo_coords = None

        username = 'xiaozhang'
        if photo_coords and place_names:
            for p_name in place_names:
                place_result = get_geocodes(p_name, username, photo_coords)
                if place_result:
                    place_code_dict.update(place_result)

        # ----------------- 处理 HISCO 信息 -----------------
        occupation_info = occ_dict.get(f"{idx}.jpg")
        hisco_dict = {}
        if occupation_info:
            raw_occupations = occupation_info.split(',')
            for raw_occ in raw_occupations:
                raw_occ = raw_occ.strip()
                if not raw_occ:
                    continue
                occ_clean = clean_occupation_string(raw_occ)
                if not occ_clean:
                    continue
                hisco_result = get_hisco_code(occ_clean)
                hisco_dict.update(hisco_result)

        # ----------------- 构造最终 prompt -----------------
        prompt_message = (
            f"<image>Generate a meaning representation in PENMAN format for this image of a tombstone. "
            f"The Geocodes that may be used are: {place_code_dict}. "
            f"The HISCO codes that may be used are: {hisco_dict}."
        )

        entry = {
            "messages": [
                {
                    "from": "human",
                    "value": prompt_message,
                },
                {
                    "from": "gpt",
                    "value": text_content,
                },
            ],
            "images": [
                filename,
            ]
        }

        if dataset_mode == "both":
            if i < 600:
                train_data.append(entry)
            else:
                test_data.append(entry)
        elif dataset_mode == "train":
            train_data.append(entry)
        elif dataset_mode == "test":
            test_data.append(entry)

    if dataset_mode in ("train", "both"):
        try:
            with open('tomb_parsing_train_combined.json', 'w', encoding='utf-8') as json_file:
                json.dump(train_data, json_file, ensure_ascii=False, indent=4)
            print("Training data saved to tomb_parsing_train_combined.json.")
        except IOError as e:
            print(f"Error saving training data: {e}")

    if dataset_mode in ("test", "both"):
        try:
            with open('tomb_parsing_test_combined.json', 'w', encoding='utf-8') as json_file:
                json.dump(test_data, json_file, ensure_ascii=False, indent=4)
            print("Testing data saved to tomb_parsing_test_combined.json.")
        except IOError as e:
            print(f"Error saving testing data: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate train/test dataset for tomb parsing with geo and hisco information."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        choices=["train", "test", "both"],
        default="test",
        help="Specify which dataset to generate: 'train' for training data, 'test' for testing data, or 'both' for both datasets."
    )
    args = parser.parse_args()
    main(args.dataset)
