from utils.smatch import score_amr_pairs
import json
import re

labels = []
predicts = []

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
geo_count = 0

for i, predict in enumerate(predicts):
    try:
        idx = f"t{i:05d}"
        gold_penman = gold_dict[idx]
        pred_penman = predict
        (precision, recall, best_f_score), unmatched_1, unmatched_2 = score_amr_pairs([gold_penman], [pred_penman])
        avg_f1 += best_f_score
        print(f"tombstone {idx}, get {best_f_score} f1 score.")

    except Exception as e:
        print(f"tombstone {idx}, generation error: {e}")
        ill_form += 1

total = len(predicts)
print(f"avg f1 score: {avg_f1 / total}")
if total - ill_form > 0:
    print(f"avg f1 score without ill: {avg_f1 / (total - ill_form)}")
print(f"ill-formed: {ill_form/600}")