## Tombstone-Parsing

> ACM MM 2025: Multi-Modal Semantic Parsing for the Interpretation of Tombstone Inscriptions. Link(https://arxiv.org/abs/2507.04377)

> The repo includes datasets, data statistics, few-shot prompts, OCR baseline, RAG pipelines, and evaluation.

---

## Overview

This repository functions as the supplmentary material and reproduction for the corresponding paper. We include the dataset, the statistics of the dataset (samples, languages, font size, etc.), some examples (tombstone images and structured representations TMR), the experiments (few-shot, lora fine-tuning, RAG) and the evaluation of the TMR.

---

## Repository Structure

```text
Tombstone-Parsing/
  data/
    annotations/tombs_grounded.txt  # TMRs
    augmentation/fusion.py        # add noise to tombstone images (see paper section 6)
    images/                      # Raw images (.jpg)
    graphs/                      # graphs of TMRs
    noises/                      # Noises, such as crack, moss, scratch
    split/                       # Train/test splits, and json format for fine-tuning

  parsing/
    OCR-base/                    # OCR baseline
    few_shot/                    # Few-shot prompts for Qwen/LLaVA, etc.
    evaluation/                  # Evaluation scripts
    RibAG/ RieAG/ RimAG/         # RAG variants and data builders
```

Start by browsing `data/` and `parsing/` to see ready-to-run scripts and sample data.

---

## Environment & Installation

Recommended: Python 3.9+ (3.10/3.11 preferred)

Example (conda):

```bash
conda create -n tombstone-parsing python=3.11 -y
conda activate tombstone-parsing

# Common dependencies (install as needed)
pip install -U pillow opencv-python numpy matplotlib tqdm
pip install graphviz python-graphviz networkx
pip install pandas seaborn

# For LLMs/evaluation (optional)
pip install transformers accelerate datasets sentencepiece peft
```

To render `.dot` files, install Graphviz system-wide:

- macOS (Homebrew): `brew install graphviz`
- Ubuntu/Debian: `sudo apt-get install graphviz`

---

## Quick Start

1) Clone and prepare

```bash
git clone https://github.com/<your_org>/Tombstone-Parsing.git
cd Tombstone-Parsing
```

2) Inspect splits (train/test and LLaMAFactory conversion)

```bash
ls data/split
# Expect train_images/ test_images/ and tomb_parsing_*.json
```

3) Render graph structure (.dot -> .png/.svg)

```bash
python data/dot/dot2png.py --src data/dot --dst data/graphs
```

4) Run a simple augmentation and plot

```bash
python data/augmentation/plot.py --src data/images --dst data/noised_images
```

---

## Data & Augmentations

- `data/images/`: main dataset images, e.g., `t00000.jpg`
- `data/dot/`: per-image graph annotations (Graphviz `.dot`). Use `dot2png.py` to render into `data/graphs/`.
- `data/split/`:
  - `train_images/` and `test_images/`: split subsets
  - `tomb_parsing_{train,test}.json`: labels for parsing
  - `split_for_llamafactory.py`: convert to LLaMAFactory format

Augmentation scripts (partial):

- `data/augmentation/FBM.py`: fractal noise (FBM)
- `data/augmentation/perspective.py`: perspective transform
- `data/augmentation/fusion.py`: multi-noise fusion
- `data/augmentation/plot.py`: preview/plotting utilities

Examples:

```bash
# Perspective augmentation
python data/augmentation/perspective.py \
  --src data/images --dst data/perspective_images

# Noise augmentation (example)
python data/augmentation/fusion.py \
  --src data/images --noise-dir data/noises --dst data/noised_images
```

---

## Parsing & Baselines

- `parsing/OCR-base/`: OCR baseline entry (integrate your preferred OCR engine if needed)
- `parsing/classify_inscription/`: classify inscription segments and post-process answers
- `parsing/few_shot/`:
  - `qwen_7b/`, `qwen_3b/`, `qwen_72b/`, `llava_7b/`, etc.: few-shot prompts, logs, and outputs
  - Refer to `*_one_shot.py`, `*_four_shot.py`, `*_five_shot.py` for quick trials
- `parsing/RibAG/`, `parsing/RieAG/`, `parsing/RimAG/`: RAG variants with data builders and first-step results
- `parsing/base/`: general notes and sample results (e.g., `qwen2_5_vl_7B/results/`)

Usage examples:

```bash
# Run a few-shot script (edit paths/params inside if needed)
python parsing/few_shot/qwen_7b/qwen_7b_five_shot.py

# Build RAG data (example)
python parsing/RibAG/geo/create_json_rag_geo.py \
  --input data/split/tomb_parsing_train.json --output parsing/RibAG/geo/tomb_parsing_train_rag.json
```

> Note: Some scripts use in-file path variables rather than CLI flags. Open and edit the top of the script if flags are not provided.

---

## Evaluation & Visualization

- `parsing/evaluation/`:
  - `fine_grained.py`, `date_eva.py`: fine-grained and date-related evaluation
  - `utils/smatch.py`, `utils/smatch_fromlists.py`: SMATCH metric
  - `fine_grained/`: plotting utilities and examples (`noise_plot.py`, `language_plot.py`)

Examples:

```bash
# Compute SMATCH or fine-grained metrics (example)
python parsing/evaluation/fine_grained.py \
  --pred parsing/base/qwen2_5_vl_7B/results/generated_predictions.jsonl \
  --gold parsing/evaluation/generated_predictions.jsonl

# Statistics and plots (example)
python parsing/evaluation/fine_grained/language_plot.py
```

`.dot` visualization:

```bash
python data/dot/dot2png.py --src data/dot --dst data/graphs
```

---

## Reproducibility Tips

1) Prepare environment and Graphviz
2) Familiarize yourself with `data/split/` and `parsing/few_shot/` formats
3) Render several `.dot` files to check structure-image consistency
4) Choose one path (Few-shot / OCR / RAG) and run inference/training
5) Use `parsing/evaluation/` for metrics and plots

For strict reproducibility, fix random seeds and package versions, and log outputs (many scripts export JSON/JSONL).

---

## FAQ

- Graphviz errors when rendering `.dot`? Install Graphviz and ensure the `dot` binary is in `PATH`.
- Do LLM scripts require GPUs? Recommended for Qwen/LLaVA inference; evaluation/plotting works on CPU.
- JSON/JSONL mismatches? Check expected fields and paths; edit top-level variables in scripts if needed.

---

## Acknowledgments & Citation

If this repository helps your research or product, please consider citing:

```text
@misc{tombstone-parsing,
  title        = {Tombstone-Parsing: A Multimodal Pipeline for Tombstone Layout and Content Parsing},
  author       = {Contributors of Tombstone-Parsing},
  year         = {2025},
  howpublished = {GitHub repository},
  note         = {\url{https://github.com/<your_org>/Tombstone-Parsing}}
}
```

Issues and PRs are welcome. Thank you for your support!


