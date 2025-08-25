import json
import random
import re
import requests
import tqdm

random.seed(42)

def clean_occupation_string(occupation):
    """
    将括号外的内容和括号内的内容分开，并用逗号连接。
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
    API 返回示例:
    [
      {
        "score": 13.845567,
        "hisco": {
          "uri": "https://iisg.amsterdam/resource/hisco/code/hisco/14190",
          "major_group": "Professional, technical and related workers",
          ...
        },
        "standard": "ouderling",
        "original": "ouderling"
      }
    ]
    我们从 "hisco.uri" 中截取最后一段数字, 如 14190。
    返回字典: { occupation_name: "14190" }
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
        data = response.json()  # data 预期是一个 list
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

def read_files():
    try:
        with open("./annotation/tombs_grounded.txt", encoding="utf-8") as f:
            lines = f.read()
    except FileNotFoundError:
        print("File './annotation/tombs_grounded.txt' not found.")
        return None, None

    try:
        with open('./profession_ocr/ocr_result.json', 'r', encoding='utf-8') as file:
            occ_dict = json.load(file)
    except FileNotFoundError:
        print("File './profession_ocr/ocr_result.json' not found.")
        return None, None
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        return None, None

    return lines, occ_dict

def main():
    lines, occ_dict = read_files()
    if lines is None or occ_dict is None:
        print("Error reading files, terminating program.")
        return

    data_entries = lines.strip().split("\n\n")
    index_list = [f"t{i:05d}" for i in range(len(data_entries))]

    combined = list(zip(index_list, data_entries))
    random.shuffle(combined)
    index_list, data_entries = zip(*combined)

    train_data = []
    test_data = []
    total_entries = len(data_entries)

    for i in tqdm.tqdm(range(total_entries)):
        idx = index_list[i]
        text_content = data_entries[i]

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

        entry = {
            "messages": [
                {
                    "from": "human",
                    "value": (
                        f"<image>Generate a meaning representation in PENMAN format for this image of a tombstone."
                        f"The HISCO codes that may be used are: {hisco_dict}."
                    ),
                },
                {
                    "from": "gpt",
                    "value": f"{text_content}",
                },
            ],
            "images": [
                f"/path/to/data/{idx}.jpg",
            ]
        }

        if i < 600:
            train_data.append(entry)
        else:
            test_data.append(entry)

    try:
        with open('tomb_parsing_train_hisco.json', 'w', encoding='utf-8') as json_file:
            json.dump(train_data, json_file, ensure_ascii=False, indent=4)
        print("Training data saved to tomb_parsing_train_hisco.json.")
    except IOError as e:
        print(f"Error saving training data: {e}")

    try:
        with open('tomb_parsing_test_hisco.json', 'w', encoding='utf-8') as json_file:
            json.dump(test_data, json_file, ensure_ascii=False, indent=4)
        print("Testing data saved to tomb_parsing_test_hisco.json.")
    except IOError as e:
        print(f"Error saving testing data: {e}")


if __name__ == "__main__":
    main()
