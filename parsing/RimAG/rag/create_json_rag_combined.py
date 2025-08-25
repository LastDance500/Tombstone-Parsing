import json
import random
import re
import math
import requests
import time
import tqdm
from PIL import Image
from PIL.ExifTags import GPSTAGS
import os
from nltk.corpus import wordnet
# 如有需要，请取消下面两行注释以下载 WordNet 数据
# import nltk
# nltk.download('wordnet')

random.seed(42)

#############################
# Geo 相关函数
#############################

def haversine_distance(coord1, coord2):
    lat1, lon1 = map(math.radians, coord1)
    lat2, lon2 = map(math.radians, coord2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2) ** 2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2) ** 2
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
        latitude = lat[0] + lat[1]/60 + lat[2]/3600
        longitude = lon[0] + lon[1]/60 + lon[2]/3600
        if geotags.get('GPSLatitudeRef', 'N') != 'N':
            latitude = -latitude
        if geotags.get('GPSLongitudeRef', 'E') != 'E':
            longitude = -longitude
        return (latitude, longitude)
    except (TypeError, ValueError) as e:
        print(f"Coordinate conversion error: {e}")
        return None

def extract_geo_names(text):
    """
    从注释文本中提取形如 :nam "xxx" :geo "yyy" 的地名，
    返回所有匹配的名称列表（取 "xxx" 部分）。
    """
    pattern = r':nam\s*"([^"]+?)"\s*:geo\s*"([^"]+?)"'
    matches = re.findall(pattern, text, re.DOTALL | re.MULTILINE)
    geo_names = [match[0] for match in matches]
    return geo_names

def get_geocode(place_name, username, photo_coords):
    base_url = "http://api.geonames.org/searchJSON"
    params = {
        'q': place_name,
        'maxRows': 30,
        'username': username
    }
    while True:
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            if "status" in data and data["status"].get("value") == 19:
                print(f"GeoNames rate limit exceeded for '{place_name}'. Sleeping for 3600 seconds...")
                time.sleep(3600)
                continue
            break
        except requests.RequestException as e:
            print(f"GeoNames API request error for '{place_name}': {e}. Sleeping for 60 seconds and retrying.")
            time.sleep(60)
            continue
        except json.JSONDecodeError as e:
            print(f"GeoNames API JSON decode error for '{place_name}': {e}. Sleeping for 60 seconds and retrying.")
            time.sleep(60)
            continue

    results = data.get('geonames', [])
    if not results:
        return None

    if photo_coords:
        best_result = None
        min_distance = float('inf')
        for item in results:
            try:
                lat = float(item.get('lat', 0.0))
                lon = float(item.get('lng', 0.0))
                distance = haversine_distance(photo_coords, (lat, lon))
                if distance < min_distance:
                    min_distance = distance
                    best_result = item
            except Exception as e:
                print(f"Error processing GeoNames data for '{place_name}': {e}")
                continue
        if best_result:
            return best_result.get('geonameId')
        else:
            return None
    else:
        codes = [item.get('geonameId') for item in results if item.get('geonameId')]
        return codes if codes else None

#############################
# HISCO 相关函数
#############################

def extract_hco_names(text):
    """
    从注释文本中提取形如 :nam "xxx" :hco "yyy" 的职业名称，
    返回所有匹配中的名称部分（即 "xxx"）。
    """
    pattern = r':nam\s*"([^"]+?)"\s*:hco\s*"([^"]+?)"'
    matches = re.findall(pattern, text, re.DOTALL | re.MULTILINE)
    hco_names = [match[0] for match in matches]
    return hco_names

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
    如果 occupation_name 包含多个单词，则依次采用 1-gram、2-gram、3-gram 的连续子串进行搜索，
    收集所有子串的 HISCO 查询结果，并返回合并后的字典；
    如果只有一个单词，则直接查询。
    """
    tokens = occupation_name.split()
    results = {}
    if len(tokens) <= 1:
        return get_hisco_code(occupation_name)
    for n in [1, 2, 3]:
        if len(tokens) < n:
            continue
        for i in range(len(tokens) - n + 1):
            candidate = " ".join(tokens[i:i+n])
            candidate_result = get_hisco_code(candidate)
            if candidate_result:
                results.update(candidate_result)
    return results

#############################
# WordNet Synset 相关函数
#############################

def get_possible_synsets_with_definitions(synset_str, whitelist):
    """
    根据传入的 synset 字符串（例如 "widow.n.01"），利用 WordNet 搜索该词的所有候选 synset，
    过滤掉白名单中的项，并返回字典格式：{synset_name: definition, ...}
    """
    parts = synset_str.split('.')
    if len(parts) != 3:
        return {}
    lemma, pos, _ = parts
    if pos == 'n':
        wn_pos = wordnet.NOUN
    elif pos == 'v':
        wn_pos = wordnet.VERB
    elif pos in ['a', 's']:
        wn_pos = wordnet.ADJ
    elif pos == 'r':
        wn_pos = wordnet.ADV
    else:
        return {}
    candidate_synsets = wordnet.synsets(lemma, pos=wn_pos)
    synset_def_dict = {}
    for syn in candidate_synsets:
        synset_name = syn.name()  # 如 'widow.n.01'
        if synset_name not in whitelist:
            synset_def_dict[synset_name] = syn.definition()
    return synset_def_dict

def get_synset_candidates(text, whitelist):
    """
    利用正则表达式从文本中提取所有形如 widow.n.01 的 WordNet synset，
    对不在白名单中的候选，通过 WordNet 查找所有同义候选及其定义，
    返回字典格式，例如：
        { 'widow.n.01': 'definition1', 'widow.n.02': 'definition2', ... }
    """
    pattern = r'\b[a-z]+\.(?:n|v|a|r|s)\.\d{2}\b'
    found_synsets = set(re.findall(pattern, text))
    result = {}
    for syn in found_synsets:
        if syn not in whitelist:
            candidates = get_possible_synsets_with_definitions(syn, whitelist)
            result.update(candidates)
    return result

#############################
# 公共工具函数
#############################

def read_file(file_path):
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        return None
    return content

def extract_idx(annotation):
    m = re.search(r'\(t(\d{5})\s*/', annotation)
    if m:
        return f"t{m.group(1)}"
    else:
        return None

#############################
# 主处理逻辑（train 与 test）
#############################

def process_train(geonames_username, whitelist):
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
        # Geo 部分
        geo_names = extract_geo_names(annotation)
        # HISCO 部分
        hco_names = extract_hco_names(annotation)
        # WordNet Synset 部分
        synset_candidates = get_synset_candidates(annotation, whitelist)

        # 针对 geo：尝试读取图像的 EXIF 信息获取 GPS 坐标（如果有）
        filename = f"/Users/xiaozhang/code/multi-modal-PMB/tomb/tombreader/data/{idx}.jpg"
        photo_coords = None
        try:
            exif = get_exif(filename)
            geotags = get_geotagging(exif)
            photo_coords = get_coordinates(geotags)
            if photo_coords is None:
                print(f"GPS data for {filename} not found. Proceeding without distance filtering.")
        except FileNotFoundError:
            print(f"File {filename} not found. Proceeding without file...")
        except Exception as e:
            print(f"Error processing {filename}: {e}")

        geo_results = {}
        for name in geo_names:
            code = get_geocode(name, geonames_username, photo_coords)
            if code:
                geo_results[name] = code

        hco_results = {}
        for name in hco_names:
            code_dict = search_hisco_code(name)
            if code_dict:
                hco_results.update(code_dict)

        # 将三部分信息整合到同一个 prompt 中
        prompt = (
            f"<image>Generate a meaning representation in PENMAN format for this image of a tombstone. "
            f"The GeoNames that may be used are: {geo_results}. "
            f"The HISCO codes that may be used are: {hco_results}. "
            f"The candidate synsets that may be used are: {synset_candidates}."
        )

        entry = {
            "messages": [
                {"from": "human", "value": prompt},
                {"from": "gpt", "value": annotation},
            ],
            "images": [f"/projects/0/prjs0885/LLaMA-Factory/tombreader/data/{idx}.jpg"]
        }
        train_data.append(entry)

    try:
        with open('tomb_parsing_combined_train.json', 'w', encoding='utf-8') as json_file:
            json.dump(train_data, json_file, ensure_ascii=False, indent=4)
        print("Training data saved to tomb_parsing_combined_train.json.")
    except IOError as e:
        print(f"Error saving training data: {e}")

def process_test(geonames_username, whitelist):
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
        # Geo 部分
        geo_names = extract_geo_names(annotation)
        # HISCO 部分
        hco_names = extract_hco_names(annotation)
        # WordNet Synset 部分
        synset_candidates = get_synset_candidates(annotation, whitelist)

        filename = f"/Users/xiaozhang/code/multi-modal-PMB/tomb/tombreader/data/{idx}.jpg"
        photo_coords = None
        try:
            exif = get_exif(filename)
            geotags = get_geotagging(exif)
            photo_coords = get_coordinates(geotags)
            if photo_coords is None:
                print(f"GPS data for {filename} not found. Proceeding without distance filtering.")
        except FileNotFoundError:
            print(f"File {filename} not found. Proceeding without file...")
        except Exception as e:
            print(f"Error processing {filename}: {e}")

        geo_results = {}
        for name in geo_names:
            code = get_geocode(name, geonames_username, photo_coords)
            if code:
                geo_results[name] = code

        hco_results = {}
        for name in hco_names:
            code_dict = search_hisco_code(name)
            if code_dict:
                hco_results.update(code_dict)

        prompt = (
            f"<image>Generate a meaning representation in PENMAN format for this image of a tombstone. "
            f"The GeoNames that may be used are: {geo_results}. "
            f"The HISCO codes that may be used are: {hco_results}. "
            f"The candidate WordNet synsets that may be used are: {synset_candidates}."
        )
        entry = {
            "messages": [
                {"from": "human", "value": prompt},
                {"from": "gpt", "value": annotation},
            ],
            "images": [f"/projects/0/prjs0885/LLaMA-Factory/tombreader/data/{idx}.jpg"]
        }
        test_data.append(entry)

    try:
        with open('tomb_parsing_combined_test.json', 'w', encoding='utf-8') as json_file:
            json.dump(test_data, json_file, ensure_ascii=False, indent=4)
        print("Testing data saved to tomb_parsing_combined_test.json.")
    except IOError as e:
        print(f"Error saving testing data: {e}")


if __name__ == "__main__":
    mode = "test"
    geonames_username = "qmeng"
    whitelist = ['tombstone.n.01', 'male.n.02', 'husband.n.01', 'father.n.01',
                 'village.n.02', 'date.n.05', 'spouse.n.01', 'female.n.02',
                 'son.n.01', 'brother.n.01', 'measure.n.02', 'year.n.01',
                 'wife.n.01', 'mother.n.01', 'grandmother.n.01', 'widow.n.01',
                 'person.n.01', 'city.n.01', 'daughter.n.01', 'sister.n.01',
                 'aunt.n.01', 'grandfather.n.01', 'town.n.01', 'location.n.01',
                 'widower.n.01', 'law.n.01', 'hamlet.n.03', 'parent.n.01',
                 'commemorator.n.01', 'uncle.n.01', 'month.n.01',
                 'municipality.n.01', 'teacher.n.01', 'doctor.n.01',
                 'grandparent.n.01', 'principal.n.02', 'more.r.01', 'family.n.04',
                 'child.n.02', 'island.n.01', 'grandchild.n.01', 'memorial.n.01',
                 'cross.n.03']

    if mode == "train":
        process_train(geonames_username, whitelist)
    elif mode == "test":
        process_test(geonames_username, whitelist)
    else:
        print("Invalid mode. Please choose 'train' or 'test'.")
