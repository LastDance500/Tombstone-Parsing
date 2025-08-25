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


# generate first step test results to txt
with open("./first_step_test.txt", "w", encoding="utf-8") as f:
    for i, predict in enumerate(predicts):
        idx = f"t{i:05d}"
        gold_penman = gold_dict[idx]
        pred_penman = predict

        f.write(pred_penman + "\n\n")
