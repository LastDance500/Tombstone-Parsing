import json
import re

def extract_dates(penman_text):
    """
    利用正则表达式从 penman notation 文本中提取所有 date 信息。
    例如，对于以下片段：
         :dob (x5 / date.n.05
                  :dom "12"
                  :moy "10"
                  :yoc "1926")
    返回的集合中包含 "12-10-1926"（这里使用 日-月-年 格式）。
    """
    pattern = r':(dob|dod)\s*\([^)]*?:dom\s*"([^"]+)"\s*:moy\s*"([^"]+)"\s*:yoc\s*"([^"]+)"'
    matches = re.findall(pattern, penman_text, re.DOTALL | re.MULTILINE)
    # 对于每个匹配，构造 "dom-moy-yoc" 的日期字符串
    dates = set(f"{m[1]}-{m[2]}-{m[3]}" for m in matches)
    return dates

def compute_f1_scores(jsonl_file):
    """
    读取 jsonl 文件，每行一个 JSON 对象，要求对象中有 "label" 和 "predict" 字段，
    分别包含 gold penman 和预测 penman。对每个样本，提取其中的 date 信息，
    然后计算 micro 和 macro F1 分数（多标签的计算方式）。
    """
    micro_TP = 0
    micro_FP = 0
    micro_FN = 0
    f1_list = []
    total_samples = 0

    with open(jsonl_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                continue

            # 提取 gold 和预测的 penman 文本
            gold_text = obj.get("label", "")
            pred_text = obj.get("predict", "")

            # 提取日期信息
            gold_dates = extract_dates(gold_text)
            pred_dates = extract_dates(pred_text)

            # 计算每个样本内的 TP, FP, FN
            tp = len(gold_dates & pred_dates)
            fp = len(pred_dates - gold_dates)
            fn = len(gold_dates - pred_dates)

            micro_TP += tp
            micro_FP += fp
            micro_FN += fn

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0
            f1_list.append(f1)
            total_samples += 1

    micro_precision = micro_TP / (micro_TP + micro_FP) if (micro_TP + micro_FP) > 0 else 0
    micro_recall = micro_TP / (micro_TP + micro_FN) if (micro_TP + micro_FN) > 0 else 0
    micro_f1 = (2 * micro_precision * micro_recall / (micro_precision + micro_recall)) if (micro_precision + micro_recall) > 0 else 0
    macro_f1 = sum(f1_list) / total_samples if total_samples > 0 else 0

    return micro_precision, micro_recall, micro_f1, macro_f1

if __name__ == "__main__":
    jsonl_file = "generated_predictions.jsonl"
    micro_precision, micro_recall, micro_f1, macro_f1 = compute_f1_scores(jsonl_file)
    print("Micro precision: {:.4f}, Micro recall: {:.4f}, Micro F1: {:.4f}".format(micro_precision, micro_recall, micro_f1))
    print("Macro F1: {:.4f}".format(macro_f1))
