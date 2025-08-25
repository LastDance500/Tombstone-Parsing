import json
import re
import math
import requests
import time
from PIL import Image
from PIL.ExifTags import GPSTAGS

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

# 分别对 :geo 和 :hco 字段进行替换

def replace_geo_codes(annotation, username):
    """
    查找形如 :nam "xxx" 后紧跟 :geo "旧代码" 的模式，
    并利用 place_name（xxx）调用 get_geocode 替换旧的 geo 代码。
    """
    pattern = r'(:nam\s*"([^"]+?)"\s*:geo\s*")([^"]+?)(")'
    def repl(match):
        # match.group(2) 为 name，group(3) 为旧的 geo 代码
        name = match.group(2)
        old_geo = match.group(3)
        new_geo = get_geocode(name, username, None)
        print(f"Replacing geo code for '{name}': {old_geo} -> {new_geo}")
        return f':nam "{name}" :geo "{new_geo}"'
    return re.sub(pattern, repl, annotation, flags=re.DOTALL | re.MULTILINE)

def replace_hco_codes(annotation, username):
    """
    查找形如 :nam "xxx" 后紧跟 :hco "旧代码" 的模式，
    并进行替换（这里示例中暂保持 hco 不变，或可添加新的替换逻辑）
    """
    pattern = r'(:nam\s*"([^"]+?)"\s*:hco\s*")([^"]+?)(")'
    def repl(match):
        name = match.group(2)
        old_hco = match.group(3)
        # 如果需要对 hco 进行新的替换，可以在此调用相应函数
        new_hco = old_hco  # 示例中保持原值
        print(f"Processing hco code for '{name}': remains {new_hco}")
        return f':nam "{name}" :hco "{new_hco}"'
    return re.sub(pattern, repl, annotation, flags=re.DOTALL | re.MULTILINE)

def process_annotations(file_path, username):
    content = read_file(file_path)
    if content is None:
        print("Error reading file, terminating program.")
        return

    annotations = content.strip().split("\n\n")
    updated_annotations = []

    for annotation in annotations:
        # 先替换 :geo 字段，再替换 :hco 字段
        annotation = replace_geo_codes(annotation, username)
        annotation = replace_hco_codes(annotation, username)
        updated_annotations.append(annotation)

    output_text = "\n\n".join(updated_annotations)
    output_file = "updated.txt"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"Updated annotations saved to {output_file}")
    except IOError as e:
        print(f"Error saving updated annotations: {e}")


if __name__ == "__main__":
    file_path = "first_step_test.txt"
    username = 'qmeng'
    process_annotations(file_path, username)
