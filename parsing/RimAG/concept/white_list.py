import re
from collections import Counter
import matplotlib.pyplot as plt


def extract_synsets_from_file(filepath):
    """
    从给定文件中提取所有形如 'word.pos.num' 的 synset 字符串。
    例如：'widow.n.01'
    """
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"文件 {filepath} 未找到。")
        return []
    # 正则表达式匹配形如 "widow.n.01" 的格式
    pattern = r'\b[a-z]+\.(?:n|v|a|r|s)\.\d{2}\b'
    synsets = re.findall(pattern, content)
    return synsets


def plot_synset_distribution(counter):
    """
    绘制 synset 出现频率的分布图
    """
    synsets = list(counter.keys())
    counts = list(counter.values())
    plt.figure(figsize=(12, 6))
    plt.bar(synsets, counts, color='skyblue')
    plt.xlabel("Synset")
    plt.ylabel("出现频率")
    plt.title("Synset 频率分布")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    filepath = "/Users/xiaozhang/code/multi-modal-PMB/tomb/tombreader/annotation/tombs_grounded.txt"  # 确保该文件路径正确
    synset_list = extract_synsets_from_file(filepath)

    if not synset_list:
        print("没有提取到 synset。")
    else:
        counter = Counter(synset_list)
        print("各 synset 出现频率：")
        for syn, cnt in counter.most_common():
            print(f"{syn}: {cnt}")

        # 绘制频率分布图
        plot_synset_distribution(counter)

        # 根据频率分布确定白名单
        # 示例：将出现次数大于 1 的 synset 视为白名单
        threshold = 5
        whitelist = [syn for syn, cnt in counter.items() if cnt > threshold]
        print("\n根据分布确定的白名单：")
        print(whitelist)
