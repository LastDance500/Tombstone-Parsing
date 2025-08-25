import json
import random
import shutil
import os
import requests
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import math
import tqdm

random.seed(42)

def haversine_distance(coord1, coord2):
    """Calculate the distance between two geographical coordinates (in kilometers)."""
    lat1, lon1 = map(math.radians, coord1)
    lat2, lon2 = map(math.radians, coord2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Earth's radius in kilometers
    return c * r

def get_exif(filename):
    """Read EXIF data from an image file."""
    image = Image.open(filename)
    try:
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
    gps_info = exif.get(34853)  # GPS info is usually under tag 34853
    if gps_info:
        for (key, val) in GPSTAGS.items():
            if key in gps_info:
                geotagging[val] = gps_info[key]
    return geotagging

def get_coordinates(geotags):
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
            place_name = place_name
            p_name = item.get('name')
            geocode = item.get('geonameId')

            # Ensure lat and lon are floats, not strings
            lat = float(item.get('lat', 0.0))  # Default to 0.0 if missing or invalid
            lon = float(item.get('lng', 0.0))  # Default to 0.0 if missing or invalid

            place_coords = (lat, lon)
            distance = haversine_distance(photo_coords, place_coords)

            # Track the closest place
            if distance < min_distance:
                min_distance = distance
                closest_place = (p_name, geocode)

        except (KeyError, TypeError, ValueError) as e:
            print(f"Error processing GeoNames data: {e}")
            continue

    # Return the closest place if it's within max_distance
    if closest_place:
        return {place_name: closest_place[1]}

    return {}

def read_files():
    try:
        with open("../../../data/annotation/tombs_grounded.txt", encoding="utf-8") as f:
            lines = f.read()
    except FileNotFoundError:
        print("File '../../../data/annotation/tombs_grounded.txt' not found.")
        return None, None

    try:
        with open('../place_ocr/ocr_result.json', 'r', encoding='utf-8') as file:
            json_data = file.read()
        place_dict = json.loads(json_data)
    except FileNotFoundError:
        print("File '../place_ocr/ocr_result.json' not found.")
        return None, None
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        return None, None

    return lines, place_dict

def main():
    lines, place_dict = read_files()
    if lines is None or place_dict is None:
        print("Error reading files, terminating program.")
        return

    data = lines.strip().split("\n\n")
    index = [f"t{i:05d}" for i in range(len(data))]

    combined = list(zip(index, data))
    random.shuffle(combined)

    index, data = zip(*combined)

    train_data = []
    test_data = []
    total_entries = len(data)

    for i in tqdm.tqdm(range(total_entries)):
        idx = index[i]
        place_name = place_dict.get(f"{idx}.jpg")
        if not place_name:
            print(f"Place name for {idx}.jpg not found. Proceeding without place name...")

        filename = f"/Users/xiaozhang/code/multi-modal-PMB/tomb/tombreader/data/{idx}.jpg"
        try:
            exif = get_exif(filename)
            geotags = get_geotagging(exif)
            photo_coords = get_coordinates(geotags)
            if photo_coords is None:
                print(f"GPS data for {filename} not found. Proceeding without GPS data...")
        except FileNotFoundError:
            print(f"File {filename} not found. Proceeding without file...")
            continue
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue

        username = 'xiaozhang'
        place_code_dict = {}
        if place_name:
            # Split the place name by commas and treat each segment as a separate place name
            place_names = [p.strip() for p in place_name.split(',')]
            for p_name in place_names:
                place_result = get_geocodes(p_name, username, photo_coords)
                if place_result:
                    place_code_dict.update(place_result)

        d = data[i]
        entry = {
            "messages": [
                {
                    "from": "human",
                    "value": f"<image>Generate a meaning representation in PENMAN format for this image of a tombstone. The Geocodes that may be used are: {place_code_dict}.",
                },
                {
                    "from": "gpt",
                    "value": f"{d}",
                },
            ],
            "images": [
                f"/projects/0/prjs0885/LLaMA-Factory/tombreader/data/{idx}.jpg",
            ]
        }

        if i < 600:
            train_data.append(entry)
        else:
            test_data.append(entry)

    # Save the train and test data
    try:
        with open('tomb_parsing_train_geo.json', 'w', encoding='utf-8') as json_file:
            json.dump(train_data, json_file, ensure_ascii=False, indent=4)
        print("Training data saved.")
    except IOError as e:
        print(f"Error saving training data: {e}")

    try:
        with open('tomb_parsing_test_geo.json', 'w', encoding='utf-8') as json_file:
            json.dump(test_data, json_file, ensure_ascii=False, indent=4)
        print("Testing data saved.")
    except IOError as e:
        print(f"Error saving testing data: {e}")


if __name__ == "__main__":
    main()

