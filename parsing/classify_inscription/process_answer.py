import json
from collections import defaultdict, Counter

# 加载 JSON 数据（假设文件名为 qwen_72b_answer.json）
with open("qwen_72b_answer_new_2.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 预处理，构造记录字典：键为文件名，值为包含9个字段的字典
records = {}
for filename, content in data.items():
    # 以换行符分割，并去除两端空白
    parts = [p.strip() for p in content.split("\n") if p.strip()]
    # 去除每个部分末尾的冒号（如果有）
    parts = [p.rstrip(":") for p in parts]
    if len(parts) == 9:
        (language, font_style, coreference, rhetorical_devices,
         syntactic_complexity, figurative_language,
         anaphoric_deictic_pronouns, abbreviated_names, multiple_persons) = parts

        records[filename] = {
            "language": language,
            "font_style": font_style,
            "coreference": coreference,
            "rhetorical_devices": rhetorical_devices,
            "syntactic_complexity": syntactic_complexity,
            "figurative_language": figurative_language,
            "anaphoric_deictic_pronouns": anaphoric_deictic_pronouns,
            "abbreviated_names": abbreviated_names,
            "multiple_persons": multiple_persons
        }
    else:
        print(f"Warning: {filename} 字段数量异常，获得字段：{parts}")

# 定义需要统计的字段
dimensions = [
    "language",
    "font_style",
    "coreference",
    "rhetorical_devices",
    "syntactic_complexity",
    "figurative_language",
    "anaphoric_deictic_pronouns",
    "abbreviated_names",
    "multiple_persons"
]

# 统计各字段的分布情况
distributions = {dim: Counter() for dim in dimensions}
for rec in records.values():
    for dim in dimensions:
        distributions[dim][rec[dim]] += 1

print("各字段分布：")
for dim, counter in distributions.items():
    print(f"{dim}: {dict(counter)}")
print()

# 找出每个字段最常见的值（排除特殊处理字段）
most_common = {}
for dim, counter in distributions.items():
    if dim not in ["abbreviated_names", "multiple_persons", "coreference"]:
        most_common[dim] = counter.most_common(1)[0][0]
        print(f"字段 '{dim}' 中最常见的值是: {most_common[dim]}")
print()

# 提取结果
result = {}
for dim in dimensions:
    if dim in ["abbreviated_names", "multiple_persons", "coreference"]:
        # 只收集回答为 "Yes" 的文件
        yes_list = []
        for filename, rec in records.items():
            if "Yes" in rec[dim]:
                yes_list.append(filename)
        result[dim] = {"Yes": {"files": yes_list, "count": len(yes_list)}}
    else:
        # 其他字段保持原逻辑：输出非最常见项
        groups = defaultdict(list)
        for filename, rec in records.items():
            if rec[dim] != most_common[dim]:
                groups[rec[dim]].append(filename)
        result[dim] = {key: {"files": value, "count": len(value)} for key, value in groups.items()}

# 输出结果
print("非最常见项 / 特殊字段结果（包含文件数量）：")
for dim, group in result.items():
    print(f"{dim}:")
    for key, value in group.items():
        print(f"  {key}: {value['files']} (count: {value['count']})")