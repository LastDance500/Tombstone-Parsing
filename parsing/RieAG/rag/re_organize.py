from smatch import score_amr_pairs
import json
import re

# 初始化 labels 和 predicts
labels = []
predicts = []

def replace_numbers_in_triple(triple):
    pattern = re.compile(r'^([ab])\d+$')

    def replace_if_match(s):
        match = pattern.match(s)
        if match:
            return match.group(1) + '*'
        return s

    # 对三元组的每个元素都进行处理
    return (replace_if_match(triple[0]),
            replace_if_match(triple[1]),
            replace_if_match(triple[2]))

with open("generated_predictions.jsonl", "r", encoding="utf-8") as file:
    for line in file:
        data = json.loads(line)
        label_t_code = re.search(r"\(t\d+\b", data["label"])
        if label_t_code:
            label_t_code = label_t_code.group(0)
            data["predict"] = re.sub(r"\(t\d+\b", label_t_code, data["predict"], count=1)
        labels.append(data["label"])

        predicts.append(data["predict"])

gold_dict = {f"t{i:05d}": label for i, label in enumerate(labels)}

avg_f1 = 0
ill_form = 0
unmatched_stats = {}
geo_count = 0  # 初始化统计变量

# generate first step test results
# with open("/Users/xiaozhang/code/multi-modal-PMB/tomb/geo_search/first_step_test.txt", "w", encoding="utf-8") as f:
#     for i, predict in enumerate(predicts):
#         idx = f"t{i:05d}"
#         gold_penman = gold_dict[idx]
#         pred_penman = predict
#
#         f.write(pred_penman + "\n\n")



# rule-based search

import json


def update_jsonl_with_penman(jsonl_in, jsonl_out, updated_penman_file):
    # 读取更新后的 penman 注释（按 "\n\n" 分隔）
    with open(updated_penman_file, "r", encoding="utf-8") as f:
        penman_text = f.read()
    updated_penmans = [p.strip() for p in penman_text.strip().split("\n\n") if p.strip()]

    # 读取原始 jsonl 文件，每行是一个 JSON 对象
    with open(jsonl_in, "r", encoding="utf-8") as f:
        lines = f.readlines()

    num_penmans = len(updated_penmans)
    num_lines = len(lines)
    print(f"Number of updated penmans: {num_penmans}")
    print(f"Number of jsonl lines: {num_lines}")

    # 如果两者数量不匹配，输出警告并以较少的数量作为替换基数
    n = min(num_penmans, num_lines)
    if num_penmans != num_lines:
        print("Warning: 更新的 penman 注释数量与 jsonl 文件行数不匹配！将只更新前 {} 行。".format(n))

    updated_lines = []
    for i, line in enumerate(lines):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"JSON 解析错误，第 {i + 1} 行：{e}")
            updated_lines.append(line)
            continue

        # 如果有对应的更新 penman，则替换，否则保持原样
        if i < n:
            obj["predict"] = updated_penmans[i]
        updated_lines.append(json.dumps(obj, ensure_ascii=False))

    with open(jsonl_out, "w", encoding="utf-8") as f:
        for line in updated_lines:
            f.write(line + "\n")

    print(f"更新后的 jsonl 已保存到: {jsonl_out}")


jsonl_input = "generated_predictions.jsonl"  # 原始 jsonl 文件
jsonl_output = "generated_predictions_updated.jsonl"  # 输出更新后的文件
updated_penman_file = "updated.txt"  # 更新后的 penman 文件

update_jsonl_with_penman(jsonl_input, jsonl_output, updated_penman_file)

