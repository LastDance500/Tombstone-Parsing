import json
import random
import re
import math
import requests
import time
from PIL import Image
from PIL.ExifTags import GPSTAGS

random.seed(42)

def haversine_distance(coord1, coord2):
    lat1, lon1 = map(math.radians, coord1)
    lat2, lon2 = map(math.radians, coord2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon / 2)**2
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
    gps_info = exif.get(34853)  # GPS 信息通常存储在 tag 34853 下
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
            # 判断是否触发访问限制（状态值 19 表示超限，根据实际情况调整）
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
        if codes:
            return codes[0]
        else:
            return None

def read_file(file_path):
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        return None
    return content

def process_test_update(username):
    test_file = "/Users/xiaozhang/code/multi-modal-PMB/tomb/geo_search/first_step_test.txt"
    test_content = read_file(test_file)
    if test_content is None:
        print("Error reading test file, terminating program.")
        return
    test_annotations = test_content.strip().split("\n\n")
    updated_annotations = []

    for i, annotation in enumerate(test_annotations):
        idx = extract_idx(annotation)
        if not idx:
            idx = f"t{i:05d}"
        filename = f"/Users/xiaozhang/code/multi-modal-PMB/tomb/tombreader/data/{idx}.jpg"
        try:
            exif = get_exif(filename)
            geotags = get_geotagging(exif)
            photo_coords = get_coordinates(geotags)
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            photo_coords = None

        def replace_geo(match):
            name = match.group(1)
            old_code = match.group(2)
            new_code = get_geocode(name, username, photo_coords)
            if new_code is None:
                new_code = old_code
            return f':nam "{name}" :geo "{new_code}"'

        updated_annotation = re.sub(r':nam\s*"([^"]+?)"\s*:geo\s*"([^"]+?)"', replace_geo, annotation, flags=re.DOTALL|re.MULTILINE)
        updated_annotations.append(updated_annotation)

    output_text = "\n\n".join(updated_annotations)
    output_file = "tomb_parsing_test_updated.txt"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"Updated test penman saved to {output_file}")
    except IOError as e:
        print(f"Error saving updated test penman: {e}")

if __name__ == "__main__":

    geonames_username = 'qmeng'
    process_test_update(geonames_username)
