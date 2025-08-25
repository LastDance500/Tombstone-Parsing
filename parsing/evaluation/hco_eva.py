import json
import re

def extract_hco_codes(penman_text):
    """
    使用正则表达式从复杂嵌套的 PENMAN notation 文本中提取所有 hco code。
    """
    # 更新正则表达式以匹配可能的嵌套结构
    pattern = r'\:hco\s*"(\d+)"'
    matches = re.findall(pattern, penman_text)
    # 返回所有匹配的 hco codes
    codes = set(matches)
    return codes

def compute_f1_scores(jsonl_file):
    """
    读取 jsonl 文件，每行一个 JSON 对象，要求对象中有 "gold" 和 "predict" 字段，
    分别包含 gold penman 和预测 penman。对每个样本，提取其中的 hco code，
    然后计算 micro 和 macro F1 分数。
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
            gold_text = obj.get("label", "")
            pred_text = obj.get("predict", "")

            gold_codes = extract_hco_codes(gold_text)
            pred_codes = extract_hco_codes(pred_text)

            # 计算样本内的 TP, FP, FN
            tp = len(gold_codes & pred_codes)
            fp = len(pred_codes - gold_codes)
            fn = len(gold_codes - pred_codes)

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
