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

---

## Environment & Installation


```bash
git clone git@github.com:LastDance500/Tombstone-Parsing.git
cd Tombstone-Parsing
git clone --depth 1 https://github.com/hiyouga/LLaMA-Factory.git
cd LLaMA-Factory
pip install -e ".[torch,metrics]" --no-build-isolation
pip install --upgrade huggingface_hub
huggingface-cli login
cd ..
```


---


## Parsing & Baselines

> coming soon

---

## Evaluation & Visualization

> coming soon


## Acknowledgments & Citation

If this repository helps your research or product, please consider citing:

```text
@article{zhang2025multi,
  title={Multi-Modal Semantic Parsing for the Interpretation of Tombstone Inscriptions},
  author={Zhang, Xiao and Bos, Johan},
  journal={arXiv preprint arXiv:2507.04377},
  year={2025}
}
```

Issues and PRs are welcome. Thank you for your support!


