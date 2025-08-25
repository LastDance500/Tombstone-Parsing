import json
import random
import os
import re
import time
import tqdm
from nltk.corpus import wordnet

# 如有需要，请取消下面两行注释以下载 WordNet 数据
# import nltk
# nltk.download('wordnet')

random.seed(42)


#############################
# 文件处理相关函数
#############################

def read_file(file_path):
    """读取文件内容并返回字符串。"""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        return None
    return content


def extract_idx(annotation):
    """
    尝试从 annotation 文本中提取索引。
    例如，匹配 (t00000 / tombstone.n.01 ... 返回 "t00000"
    """
    m = re.search(r'\(t(\d{5})\s*/', annotation)
    if m:
        return f"t{m.group(1)}"
    else:
        return None


#############################
# WordNet synset 相关函数
#############################

def get_possible_synsets_with_definitions(synset_str, whitelist):
    """
    根据传入的 synset 字符串（例如 "widow.n.01"），
    利用 WordNet 搜索该词的所有候选 synset，
    过滤掉白名单中的项，并返回字典格式：{synset_name: definition, ...}
    """
    parts = synset_str.split('.')
    if len(parts) != 3:
        return {}
    lemma, pos, _ = parts
    # 将 pos 转换为 NLTK WordNet 的标识
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
        synset_name = syn.name()  # 例如 'widow.n.01'
        if synset_name not in whitelist:
            synset_def_dict[synset_name] = syn.definition()
    return synset_def_dict


def get_synset_candidates(penman_text, whitelist):
    """
    利用正则表达式从 penman 文本中提取所有 WordNet synset（例如 widow.n.01），
    然后对于不在白名单中的 synset，获取该词所有候选及其定义，
    最终返回一个字典，例如：
        {
            'widow.n.01': 'definition1',
            'widow.n.02': 'definition2',
            'widow.n.03': 'definition3'
        }
    """
    pattern = r'\b[a-z]+\.(?:n|v|a|r|s)\.\d{2}\b'
    found_synsets = set(re.findall(pattern, penman_text))
    result = {}
    for syn in found_synsets:
        if syn not in whitelist:
            candidates = get_possible_synsets_with_definitions(syn, whitelist)
            result.update(candidates)
    return result


#############################
# 主逻辑：train 与 test
#############################

def process_train(whitelist):
    train_file = "/Users/xiaozhang/code/multi-modal-PMB/tomb/tombreader/annotation/tombs_grounded.txt"
    train_content = read_file(train_file)
    if train_content is None:
        print("Error reading training file, terminating program.")
        return
    train_annotations = train_content.strip().split("\n\n")
    # 使用文件顺序生成索引（例如 t00000, t00001, ...）
    train_index = [f"t{i:05d}" for i in range(len(train_annotations))]
    train_data = []

    # 只处理前600条记录
    for i in tqdm.tqdm(range(min(600, len(train_annotations))), desc="Processing train data"):
        idx = train_index[i]
        annotation = train_annotations[i]
        # 提取 annotation 中所有不在白名单中的 synset 候选及其定义
        synset_candidates = get_synset_candidates(annotation, whitelist)

        entry = {
            "messages": [
                {
                    "from": "human",
                    "value": f"<image>Parsing this tombstone. The candidate synsets you may use are: {synset_candidates}.",
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
        with open('tomb_parsing_second_train_synset.json', 'w', encoding='utf-8') as json_file:
            json.dump(train_data, json_file, ensure_ascii=False, indent=4)
        print("Training data saved to tomb_parsing_train_synset.json.")
    except IOError as e:
        print(f"Error saving training data: {e}")


def process_test(whitelist):
    # 1. 从 first_step_test.txt 中提取测试数据的 index（顺序由文件中的记录决定）
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
            print("Warning: 未能从 first step 测试数据中提取 index，跳过一条记录。")

    # 2. 从 tombs_grounded.txt 中构建 index 到正确答案的映射
    grounded_file = "/Users/xiaozhang/code/multi-modal-PMB/tomb/tombreader/annotation/tombs_grounded.txt"
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

    # 3. 遍历 first_step_test.txt 中提取的 index 顺序，生成最终的测试数据
    test_data = []

    for idx in tqdm.tqdm(test_indices, desc="Processing test data"):
        if idx not in grounded_mapping:
            print(f"Index {idx} not found in grounded file. Skipping.")
            continue
        # 使用 tombs_grounded.txt 中对应 index 的正确答案
        annotation = grounded_mapping[idx]
        synset_candidates = get_synset_candidates(annotation, whitelist)

        entry = {
            "messages": [
                {
                    "from": "human",
                    "value": f"<image>Parsing this tombstone. The candidate synsets you may use are: {synset_candidates}.",
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
        with open('tomb_parsing_second_test_synset.json', 'w', encoding='utf-8') as json_file:
            json.dump(test_data, json_file, ensure_ascii=False, indent=4)
        print("Testing data saved to tomb_parsing_test_synset.json.")
    except IOError as e:
        print(f"Error saving testing data: {e}")


if __name__ == "__main__":
    mode = "train"  # 可选择 "train" 或 "test"

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
        process_train(whitelist)
    elif mode == "test":
        process_test(whitelist)
    else:
        print("Invalid mode. Please choose 'train' or 'test'.")
