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


def extract_geo_names(peman_text):
    pattern = r':nam\s*"([^"]+?)"\s*:geo\s*"([^"]+?)"'
    matches = re.findall(pattern, peman_text, re.DOTALL | re.MULTILINE)
    geo_names = [match[0] for match in matches]
    return geo_names

def extract_idx(annotation):
    m = re.search(r'\(t(\d{5})\s*/', annotation)
    if m:
        return f"t{m.group(1)}"
    else:
        return None

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

def read_file(file_path):
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        return None
    return content

def process_train(username):
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
        geo_names = extract_geo_names(annotation)

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

        place_code_dict = {}
        for name in geo_names:
            code = get_geocode(name, username, photo_coords)
            if code:
                place_code_dict[name] = code

        entry = {
            "messages": [
                {
                    "from": "human",
                    "value": f"<image>Generate a meaning representation in PENMAN format for this image of a tombstone. The GeoNames that may be used are: {place_code_dict}.",
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
        with open('tomb_parsing_second_train_geo.json', 'w', encoding='utf-8') as json_file:
            json.dump(train_data, json_file, ensure_ascii=False, indent=4)
        print("Training data saved to tomb_parsing_train_geo.json.")
    except IOError as e:
        print(f"Error saving training data: {e}")


def process_test(username):
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
        geo_names = extract_geo_names(annotation)

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

        place_code_dict = {}
        for name in geo_names:
            code = get_geocode(name, username, photo_coords)
            if code:
                place_code_dict[name] = code

        entry = {
            "messages": [
                {
                    "from": "human",
                    "value": f"<image>Generate a meaning representation in PENMAN format for this image of a tombstone. The GeoNames that may be used are: {place_code_dict}.",
                },
                {
                    "from": "gpt",
                    "value": annotation,
                },
            ],
            "images": [f"/projects/0/prjs0885/LLaMA-Factory/tombreader/data/{idx}.jpg"] # image path in your server
        }
        test_data.append(entry)

    try:
        with open('tomb_parsing_second_test_geo.json', 'w', encoding='utf-8') as json_file:
            json.dump(test_data, json_file, ensure_ascii=False, indent=4)
        print("Testing data saved to tomb_parsing_test_geo.json.")
    except IOError as e:
        print(f"Error saving testing data: {e}")


if __name__ == "__main__":
    mode = "test"
    geonames_username = 'xiaozhang'
    if mode == "train":
        process_train(geonames_username)
    elif mode == "test":
        process_test(geonames_username)
    else:
        print("Invalid mode. Please choose 'train' or 'test'.")
