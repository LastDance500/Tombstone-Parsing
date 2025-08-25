import argparse
import json
import re
from collections import defaultdict

from utils.smatch import score_amr_pairs
import amr
from utils.utils import *

def replace_numbers_in_triple(triple):
    pattern = re.compile(r'^([ab])\d+$')
    def replace_if_match(s):
        match = pattern.match(s)
        if match:
            return match.group(1) + '*'
        return s
    return (replace_if_match(triple[0]),
            replace_if_match(triple[1]),
            replace_if_match(triple[2]))

def penman2triples(penman_text):
    """
    将 Penman 文本解析为 AMR 对象，提取三元组和变量-概念映射。
    """
    penman_obj = amr.AMR.parse_AMR_line(penman_text.replace("\n", ""))
    penman_dict = var2concept(penman_obj)
    triples = []
    for t in penman_obj.get_triples()[1] + penman_obj.get_triples()[2]:
        if t[0].endswith('-of'):
            triples.append((t[0][:-3], t[2], t[1]))
        else:
            triples.append((t[0], t[1], t[2]))
    return triples, penman_dict

def score_nodes(penman_pred, penman_gold, inters, golds, preds):
    """
    细粒度（node-level）评估：
      对预测和金标准的 AMR 分别解析后，提取各类节点信息（命名实体、否定、语义角色等），
      并更新三个字典：inters（交集计数）、preds（预测计数）和 golds（金标准计数）。
    注意：函数要求第一个参数为预测结果，第二个为金标准。
    """
    triples_pred, dict_pred = penman2triples(penman_pred)
    triples_gold, dict_gold = penman2triples(penman_gold)

    # nam
    list_pred = disambig(namedent(dict_pred, triples_pred))
    list_gold = disambig(namedent(dict_gold, triples_gold))
    inters["nam"] += len(set(list_pred) & set(list_gold))
    preds["nam"] += len(set(list_pred))
    golds["nam"] += len(set(list_gold))

    # Negation
    list_pred = disambig(negations(dict_pred, triples_pred))
    list_gold = disambig(negations(dict_gold, triples_gold))
    inters["Negation"] += len(set(list_pred) & set(list_gold))
    preds["Negation"] += len(set(list_pred))
    golds["Negation"] += len(set(list_gold))

    # Roles
    list_pred = disambig(roles(triples_pred))
    list_gold = disambig(roles(triples_gold))
    inters["rol"] += len(set(list_pred) & set(list_gold))
    preds["rol"] += len(set(list_pred))
    golds["rol"] += len(set(list_gold))

    # Members
    list_pred = disambig(members(triples_pred))
    list_gold = disambig(members(triples_gold))
    inters["Members"] += len(set(list_pred) & set(list_gold))
    preds["Members"] += len(set(list_pred))
    golds["Members"] += len(set(list_gold))

    # Concepts
    list_pred = disambig(concepts(dict_pred))
    list_gold = disambig(concepts(dict_gold))
    inters["Concepts"] += len(set(list_pred) & set(list_gold))
    preds["Concepts"] += len(set(list_pred))
    golds["Concepts"] += len(set(list_gold))

    # Concept nouns
    list_pred = disambig(con_noun(dict_pred))
    list_gold = disambig(con_noun(dict_gold))
    inters["Con_noun"] += len(set(list_pred) & set(list_gold))
    preds["Con_noun"] += len(set(list_pred))
    golds["Con_noun"] += len(set(list_gold))

    # Concept adjectives
    list_pred = disambig(con_adj(dict_pred))
    list_gold = disambig(con_adj(dict_gold))
    inters["Con_adj"] += len(set(list_pred) & set(list_gold))
    preds["Con_adj"] += len(set(list_pred))
    golds["Con_adj"] += len(set(list_gold))

    # Concept adverbs
    list_pred = disambig(con_adv(dict_pred))
    list_gold = disambig(con_adv(dict_gold))
    inters["Con_adv"] += len(set(list_pred) & set(list_gold))
    preds["Con_adv"] += len(set(list_pred))
    golds["Con_adv"] += len(set(list_gold))

    # Concept verbs
    list_pred = disambig(con_verb(dict_pred))
    list_gold = disambig(con_verb(dict_gold))
    inters["Con_verb"] += len(set(list_pred) & set(list_gold))
    preds["Con_verb"] += len(set(list_pred))
    golds["Con_verb"] += len(set(list_gold))

    # Discourse
    list_pred = disambig(discources(dict_pred, triples_pred))
    list_gold = disambig(discources(dict_gold, triples_gold))
    inters["Discourse"] += len(set(list_pred) & set(list_gold))
    preds["Discourse"] += len(set(list_pred))
    golds["Discourse"] += len(set(list_gold))

    return inters, golds, preds

def evaluate_jsonl(args):
    """
    读取 JSONL 文件，每行包含 "label"（金标准）和 "predict"（生成结果）的 Penman 字符串，
    对每一对进行 smatch 评估，并同时累积细粒度（node-level）的评估统计，最后输出各项指标。
    """
    labels = []
    predicts = []
    with open(args.jsonl_file, "r", encoding="utf-8") as file:
        for line in file:
            data = json.loads(line)
            # 若 label 中存在 (t\d+) 形式的标识，则将其同步到 predict 中
            label_t_code = re.search(r"\(t\d+\b", data["label"])
            if label_t_code:
                label_t_code = label_t_code.group(0)
                data["predict"] = re.sub(r"\(t\d+\b", label_t_code, data["predict"], count=1)
            labels.append(data["label"])
            predicts.append(data["predict"])

    gold_dict = {f"t{i:05d}": label for i, label in enumerate(labels)}
    total = len(predicts)
    avg_f1 = 0
    ill_form = 0

    inters = defaultdict(int)
    golds = defaultdict(int)
    preds = defaultdict(int)

    for i, predict in enumerate(predicts):
        idx = f"t{i:05d}"
        try:
            gold_penman = gold_dict[idx]
            pred_penman = predict

            (precision, recall, best_f_score), unmatched_1, unmatched_2 = score_amr_pairs([gold_penman], [pred_penman])
            avg_f1 += best_f_score
            print(f"{idx}: smatch f1 = {best_f_score:.3f}")

            inters, golds, preds = score_nodes(pred_penman, gold_penman, inters, golds, preds)

        except Exception as e:
            print(f"{idx}: generation error: {e}")
            ill_form += 1

    print(f"\nAverage smatch f1 = {avg_f1 / total:.3f}")
    print(f"Ill-formed count = {ill_form}")

    # 输出细粒度（node-level）评估结果
    print("\nFine-grained (node-level) evaluation:")
    for metric in sorted(preds.keys()):
        p_count = preds[metric]
        g_count = golds[metric]
        inter_count = inters[metric]
        precision = inter_count / p_count if p_count > 0 else 0
        recall = inter_count / g_count if g_count > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        print(f"{metric}: P = {precision:.4f}, R = {recall:.4f}, F = {f1:.4f}")


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate AMR graphs in JSONL format with fine-grained (node-level) metrics"
    )
    parser.add_argument("--jsonl_file", type=str, default="generated_predictions.jsonl",
                        help="Path to the JSONL file containing AMR 'label' and 'predict' strings")
    args = parser.parse_args()
    evaluate_jsonl(args)

if __name__ == "__main__":
    main()
