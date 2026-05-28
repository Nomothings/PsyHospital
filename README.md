# MentalHospital: A Virtual Psychiatric Evaluation Environment for LLM-based Medical AI

<div align="center">

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Data: EHR-grounded](https://img.shields.io/badge/data-EHR--grounded-orange.svg)](#data-processing)

</div>

## Abstract

Large language models (LLMs) have made substantial progress in psychiatry, yet success on isolated clinical components remains insufficient to reflect the integrated capability required in real-world clinical encounters. Existing virtual medical environments still exhibit three limitations: *(1) Encounter Incompleteness* — centering on doctor--patient communication rather than complete clinical encounters; *(2) Data Inauthenticity* — relying on synthetic or web-based data with limited clinical fidelity; and *(3) Patient Simplification* — modeling virtual patients as reactive symptom carriers rather than faithful psychiatric individuals.

To address these limitations, we introduce **MentalHospital**, the first virtual evaluation environment designed for psychiatric clinical encounters. MentalHospital instantiates the full **S.O.A.P. workflow** (Subjective interviewing → Objective examination → Diagnostic Assessment → Treatment Planning), grounded in **1,193 de-identified psychiatric EHR cases** covering all major ICD-11 psychiatric categories and 76 disorder-level diagnoses. It constructs skill-augmented standardized patients with individualized symptom presentation and dynamic memory recall. We also develop **MentalEval**, a suite of five domain-specific evaluators trained through rubric-grounded SFT and expert-guided DPO, achieving an average QWK of 0.944 with expert judgment.

Experiments with LLMs, clinicians, medical trainees, and crowdworkers reveal that current LLMs still lag behind clinicians by 27–37 percentage points on average across objective metrics, with mental status assessment identified as a key weakness. Clinician surveys indicate positive acceptance of MentalHospital and its perceived value for psychiatric training.

---

## Overview

<p align="center">
  <img src="./figures/overview.pdf" alt="MentalHospital Overview" width="95%">
</p>

MentalHospital provides a complete virtual psychiatric environment where an LLM-based doctor agent interacts with an EHR-grounded standardized patient across the S.O.A.P. clinical workflow. The environment enables dual-track evaluation: **objective comparison** against EHR-derived clinical references and **subjective assessment** of process quality using MentalEval.

---

## Key Contributions

- **MentalHospital** — An EHR-grounded benchmark environment for full S.O.A.P. psychiatric encounters, using skill-augmented standardized patients constructed from 1,193 de-identified psychiatric EHR cases spanning all major ICD-11 categories and 76 disorders.

- **Dual-track evaluation** — A protocol combining objective comparison against EHR-derived references with subjective assessment of clinical process quality, operationalized through **MentalEval**, a suite of specialist-aligned evaluators for scalable subjective assessment.

- **Comprehensive empirical study** — Experiments with 12 LLMs, 8 human experts, 14 medical trainees, and 8 crowdworkers, validating MentalHospital's clinical fidelity (overall score 3.88/5) and MentalEval's expert alignment (QWK 0.944), while revealing persistent gaps in mental status assessment.

---

## MentalHospital

### Data Processing

MentalHospital is constructed from **1,193 de-identified psychiatric EHR cases** obtained through an approved collaborative data-use partnership with a coordinating medical center. The dataset comprises multi-center records from six medical centers across three regions, including 885 single-diagnosis cases and 308 comorbid cases.

Each case was independently reviewed by two licensed psychiatrists (Cohen's $\kappa > 0.8$) and converted into a structured format with:
- **Patient-side evidence** $\mathcal{K}^{\mathrm{pat}}$ — chief complaint, illness history, past/family history, mental status
- **Examination-side evidence** $\mathcal{K}^{\mathrm{exam}}$ — physical and auxiliary examination findings
- **Reference clinical targets** $\mathcal{Y}^{*}$ — diagnostic category, disorder-level diagnosis, treatment information

Privacy protection uses on-premise `DeepSeek-R1`, rule-based detectors, and expert review to generalize or mask sensitive identifiers while preserving clinical meaning.

### S.O.A.P. Interaction Workflow

| Stage | Description | Doctor Agent Role |
|:---|:---|:---|
| **S**ubjective Interviewing | Patient interview and history taking | Ask psychiatric interview questions, elicit symptoms and history |
| **O**bjective Examination | Recommend and review auxiliary examinations | Request examinations, interpret results from hospital-side modules |
| **A**ssessment (Diagnosis) | Clinical note writing and diagnostic reasoning | Generate clinical note, formulate diagnostic hypotheses |
| **P**lan (Treatment) | Individualized treatment planning | Produce treatment plan based on accumulated evidence |

### Environment Modules

| Module | Implementation | Function |
|:---|:---|:---|
| **Controller** | Rule-based state machine | Manages S.O.A.P. stage transitions, routes actions, records outputs |
| **Standardized Patient** | Skill-augmented LLM agent | Individualized symptom presentation + dynamic memory recall |
| **Examination Module** | `DeepSeek-V4-Flash` QA interface | Returns EHR-derived examination results on request |

The standardized patient features a **hybrid skill design**:
- **Memory skill** — Dynamic topic-level memory retrieval; discloses only information supported by retrieved memory while avoiding unrelated or unasked clinical information
- **Presentation skill** — Individualized symptom rendering grounded in EHR mental status examination, enabling inference from both *how* the patient presents and *what* the patient states

---

## MentalEval

We develop **MentalEval**, a suite of five Qwen3-8B-based domain-specific evaluators covering:

| Evaluator | Dimension | Scale |
|:---|:---|:---|
| MentalEval-Emp | Communication Empathy | 1–5 Likert |
| MentalEval-Pro | Interviewing Professionalism | 1–5 Likert |
| MentalEval-Note | Clinical-Note Quality | 1–5 Likert |
| MentalEval-Diag | Diagnostic Rigor | 1–5 Likert |
| MentalEval-Treat | Treatment Appropriateness | 1–5 Likert |

<p align="center">
  <img src="./figures/Mentaleval.pdf" alt="MentalEval Construction Pipeline" width="95%">
</p>

### Training Pipeline

**Stage 1: Rubric-grounded SFT.** We sample 200 cases and run 20 LLMs (3 runs each) to generate complete interaction episodes. A judge ensemble of 5 LLMs (`DeepSeek-V4-Pro`, `KIMI-K2.6`, `GPT-5.5`, `Claude-Opus-4.6`, `Gemini-3.1-Pro`) generates rubric-based evaluation trajectories. Only high-agreement trajectories (≥3/5 judges consensus) are retained as SFT targets.

**Stage 2: Expert-guided DPO.** For low-confidence samples, clinicians select the best evaluation trajectory. Trajectories with the same score as the expert choice are treated as chosen, others as rejected, forming preference triples $(z, s^+, s^-)$ for DPO training.

---

## Experiments

### Benchmark Comparison

| Benchmark | Data Source | Psychiatry | Simulation Scope | Interaction | Evaluation Method | Reference | Evaluator |
|:---|:---|:---:|:---|:---:|:---|:---|:---|
| HealthBench | Physician-authored | ✗ | General Healthcare | ✗ | Rubric | Physician | ✗ |
| MedDialogRubrics | Synthetic | ✗ | Consultation/Diagnosis | ✗ | Rubric | ✗ | ✗ |
| CPsyCoun | Web | ✓ | Consultation | ✗ | Rubric/Metrics | ✗ | ✗ |
| LingxiDiagBench | Synthetic | ✓ | Consultation/Diagnosis | ✗ | Labels | ✗ | ✗ |
| PSYCHE | Synthetic | ✓ | Consultation/Diagnosis | ✓ | Metrics | ✗ | ✗ |
| AI Hospital | Web | ✗ | Consultation/Diagnosis | ✓ | Metrics | ✗ | ✗ |
| OpenHospital | Synthetic | ✗ | Interview/Diagnosis | ✓ | Metrics | ✗ | ✗ |
| AgentClinic | Single Hospital | ✗ | Inter./Exam./Diag. | ✓ | Metrics/Scale | EHR | ✗ |
| **MentalHospital (Ours)** | **Clinical Centers** | ✓ | **Inter./Exam./Diag./Treat.** | ✓ | **Rub./Metr./Lab./Scale** | **EHR/Psychiatrist** | **MentalEval** |

### Main Results

| Model | Inter. (%) | Exam. (%) | Note (%) | Cate. (%) | Diso. (%) | Emp. (1–5) | Prof. (1–5) | Qual. (1–5) | Rigor (1–5) | App. (1–5) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| *Medical Trainees* | 78.23 | 71.05 | 82.91 | 81.42 | 72.58 | 1.63 | 3.86 | 3.87 | 2.33 | 2.47 |
| *Human Experts* | 82.35 | 91.90 | 88.67 | 90.59 | 83.24 | 1.22 | 4.25 | 4.01 | 2.54 | 2.96 |
| | | | | | | | | | | |
| **Small LMs** | | | | | | | | | | |
| Llama-3-8B | 19.06 | 7.94 | 9.96 | 18.11 | 6.08 | 2.05 | 2.88 | 1.93 | 1.86 | 2.67 |
| Qwen3-14B | 23.19 | 8.33 | 12.12 | 23.55 | 15.19 | 1.96 | 2.90 | 2.17 | 2.20 | 2.83 |
| GPT-OSS-20B | 27.43 | 8.60 | <u>33.12</u> | 37.21 | 25.81 | 1.60 | 3.15 | <u>3.14</u> | 2.06 | 3.23 |
| QWQ-32B | <u>30.40</u> | <u>10.87</u> | 32.30 | <u>44.53</u> | <u>26.39</u> | 2.13 | <u>3.72</u> | 2.85 | <u>3.14</u> | <u>3.40</u> |
| | | | | | | | | | | |
| **Large LMs** | | | | | | | | | | |
| GPT-OSS-120B | 36.72 | 9.92 | 39.94 | 49.54 | 34.19 | 1.50 | 3.45 | <u>3.89</u> | <u>2.42</u> | 3.35 |
| Claude-Sonnet-4.6 | 30.44 | 21.28 | 34.81 | 50.28 | 34.57 | 1.72 | 3.39 | 2.70 | 2.22 | 3.17 |
| DeepSeek-V4-Pro | 30.95 | 21.93 | <u>56.46</u> | 26.20 | 20.85 | <u>2.09</u> | 3.48 | 2.91 | 2.39 | 3.29 |
| GPT-5.5 | <u>69.06</u> | <u>22.99</u> | 45.44 | <u>70.23</u> | <u>49.85</u> | 1.50 | <u>3.63</u> | 3.66 | 2.21 | <u>3.48</u> |
| | | | | | | | | | | |
| **Medical LMs** | | | | | | | | | | |
| MedGemma-4B-it | 25.65 | 9.42 | 10.67 | 21.48 | 3.05 | <u>2.16</u> | 2.57 | 1.99 | 2.15 | 2.91 |
| MedGemma-27B-it | 43.12 | 16.05 | 35.91 | 32.27 | 10.10 | 2.05 | 2.83 | 2.67 | 2.33 | 3.17 |
| Baichuan-M2 | <u>51.29</u> | <u>24.76</u> | <u>50.54</u> | <u>80.56</u> | <u>43.19</u> | 1.29 | <u>2.85</u> | <u>2.91</u> | <u>2.44</u> | <u>3.33</u> |

> **Key finding:** The strongest medical-specific model (Baichuan-M2) trails medical trainees by **27.17 pp** and human experts by **37.28 pp** on average across objective metrics.

### Fine-grained Coverage Analysis

| Model | Interview Avg. | Interview CC | Interview MS | Note Avg. | Note CC | Note MS |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| Qwen3-14B | 23.19 | 44.36 | 12.57 | 12.12 | 16.38 | 17.25 |
| MedGemma-4B-it | 25.65 | 40.69 | 10.45 | 10.67 | 9.68 | 6.66 |
| QWQ-32B | 30.40 | 50.90 | 17.84 | 32.30 | 42.91 | 34.22 |
| DeepSeek-V4-Pro | 30.95 | 41.67 | 23.13 | 56.46 | 59.94 | 43.91 |
| GPT-5.5 | 69.06 | 85.38 | 55.72 | 45.44 | 55.34 | 65.89 |

> **Key finding:** LLMs consistently underperform on **Mental Status (MS)** examination coverage compared to **Chief Complaint (CC)**. GPT-5.5 shows a 29.66 pp gap in interviewing (85.38 vs. 55.72).

### Patient Construction Ablation

| Patient Variant | Cov. (%) ↑ | Prec. (%) ↑ | Halluc. (%) ↓ | Realism (1–5) ↑ | Fidelity (1–5) ↑ | Distinct. (1–5) ↑ |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| Naive Prompting | 72.40 | 86.10 | 7.80 | 2.12 | 2.23 | 1.92 |
| Representation Skill Only | 72.40 | 85.72 | 9.04 | 4.12 | 3.82 | 3.72 |
| Memory Skill Only | 84.83 | 91.64 | 4.52 | 3.55 | 3.87 | 2.77 |
| **Full Patient** | **88.91** | **93.27** | **3.08** | **4.17** | **4.05** | **3.87** |

### MentalEval Ablation

| Evaluator | Base (Qwen3-8B) | | | +SFT | | | +DPO | | |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| | QWK ↑ | Acc. ↑ | MAE ↓ | QWK ↑ | Acc. ↑ | MAE ↓ | QWK ↑ | Acc. ↑ | MAE ↓ |
| MentalEval-Emp | 0.677 | 0.225 | 0.875 | 0.824 | 0.500 | 0.525 | **0.926** | **0.725** | **0.275** |
| MentalEval-Pro | 0.705 | 0.275 | 0.825 | 0.844 | 0.550 | 0.475 | **0.941** | **0.775** | **0.225** |
| MentalEval-Note | 0.766 | 0.400 | 0.675 | 0.910 | 0.700 | 0.300 | **0.940** | **0.775** | **0.225** |
| MentalEval-Diag | 0.828 | 0.475 | 0.575 | 0.887 | 0.725 | 0.325 | **0.967** | **0.875** | **0.125** |
| MentalEval-Treat | 0.819 | 0.425 | 0.600 | 0.928 | 0.725 | 0.275 | **0.948** | **0.800** | **0.200** |
| **Average** | 0.759 | 0.360 | 0.710 | 0.879 | 0.640 | 0.380 | **0.944** | **0.790** | **0.210** |

### Expert Agreement

<p align="center">
  <img src="./figures/agreement_heatmaps.pdf" alt="Agreement Heatmaps" width="80%">
</p>

MentalEval achieves the strongest expert alignment (QWK = 0.926, Acc. = 0.725, MAE = 0.275), outperforming LLM-as-a-Judge, Multi-LLM Jury, and individual crowdworker baselines.

### Clinical Faithfulness Survey

<p align="center">
  <img src="./figures/experiments_faithful_scale.pdf" alt="Clinical Faithfulness Ratings" width="50%">
</p>

Clinician survey (5 psychiatrists, 3 psychologists, 14 medical trainees) across five dimensions — Clinical Realism (CR), Patient Fidelity (PF), Patient Distinctiveness (PD), Evaluation Credibility (EC), and Training Suitability (TS) — yields an **overall mean of 3.88/5** (95% CI: [3.78, 3.98]), with positive response rate of 69.9%.

---

## Quick Start

### Prerequisites

- Python 3.10+
- OpenAI-compatible LLM API endpoints (GPT-4, DeepSeek, Qwen, Claude, etc.)

### Installation

```bash
git clone https://github.com/your-org/MentalHospital.git
cd MentalHospital

# Install the package
pip install -e .

# Configure API credentials
cp .env.example .env
# Edit .env with your API base URLs, keys, and model names
```

### Environment Configuration

The system uses multiple LLM agents, each configurable via environment variables:

| Agent | Config Keys | Description |
|:---|:---|:---|
| Doctor | `DOCTOR_API_BASE`, `DOCTOR_API_KEY`, `DOCTOR_MODEL` | The LLM under evaluation |
| Patient | `PATIENT_API_BASE`, `PATIENT_API_KEY`, `PATIENT_MODEL` | Standardized patient agent |
| Evaluators | `EVALUATOR_*_API_BASE/KEY/MODEL` | MentalEval evaluators (5 dimensions) |

All agents use OpenAI-compatible APIs and can point to different backends.

### Testing Your Models

**You must configure the `.env` file before running any evaluation.** Copy `.env.example` to `.env` and fill in your API credentials. The system cannot start without valid API endpoints and keys.

**To evaluate mainstream LLMs** (GPT-4, DeepSeek, Qwen, Claude, etc.), simply replace the `DOCTOR_*` entries in `.env` with the target model's API credentials:

```bash
# Example: evaluate GPT-5.5
DOCTOR_API_BASE=https://api.openai.com/v1
DOCTOR_API_KEY=sk-your-key
DOCTOR_MODEL=gpt-5.5
```

Then run the benchmark:

```bash
python scripts/run_interview.py --mode test
```

**To evaluate your own model**, deploy it as an OpenAI-compatible API via FastAPI or vLLM, then point `DOCTOR_API_BASE` to your local endpoint:

```bash
# Example: custom model served at localhost:8000
DOCTOR_API_BASE=http://localhost:8000/v1
DOCTOR_API_KEY=not-needed
DOCTOR_MODEL=your-model-name
```

> The only requirement is an OpenAI-compatible chat completions endpoint (`/v1/chat/completions`). We recommend using [vLLM](https://github.com/vllm-project/vllm) or [FastChat](https://github.com/lm-sys/FastChat) for deployment.

**MentalEval weights** will be publicly released upon paper acceptance.

---

## Usage

### Web Interface

```bash
python web/app.py
# → http://localhost:5000
```

The web UI guides you through the complete S.O.A.P. clinical workflow with real-time evaluation at each stage:

| Account | Password |
|:---|:---|
| `admin` | `admin123` |
| `test1` | `666666` |

```
History Taking → Examination Recommendation → Clinical Formulation → Diagnosis → Treatment Planning
```

### Benchmark / CLI Evaluation

```bash
# Test a single random case
python scripts/run_interview.py --mode test

# Test a specific case by ID
python scripts/run_interview.py --mode test --case-id 01343170

# Evaluate all cases sequentially
python scripts/run_interview.py --mode eval

# Concurrent batch evaluation (default 32 workers, with auto-resume)
python scripts/run_interview.py --mode batch --concurrency 32
```

Results are written to `data/output/results/{model}.json` with per-case scores and running averages.

### Compute Metrics

```bash
# Analyze case difficulty distribution
python scripts/analyze_difficulty.py

# Compute aggregate metrics from results
python scripts/compute_metrics.py
```

---

## Project Structure

```
MentalHospital/
├── data/
│   ├── cases.jsonl              # 1,193 de-identified psychiatric EHR cases
│   └── mapping.json             # Diagnosis category mapping
├── src/mental_hospital/
│   ├── agents/                  # LLM agent implementations
│   │   ├── patient.py           # Skill-augmented standardized patient
│   │   ├── psychiatrist.py      # Doctor agent
│   │   └── examiner.py          # Examination module agent
│   ├── interview/               # S.O.A.P. pipeline
│   │   ├── pipeline.py          # Main interview orchestrator
│   │   ├── history.py           # Subjective interviewing
│   │   ├── examination.py       # Objective examination
│   │   ├── formulation.py       # Clinical note & diagnostic formulation
│   │   ├── diagnosis.py         # Definitive diagnosis
│   │   └── treatment.py         # Treatment planning
│   ├── evaluation/              # Objective & subjective evaluators
│   ├── prompts/                 # Agent prompts and rubrics
│   ├── analysis/                # Difficulty analysis & aggregation
│   └── utils/                   # Retry, text processing, SFT utilities
├── scripts/
│   ├── run_interview.py         # CLI entry point for benchmark runs
│   ├── compute_metrics.py       # Aggregate metrics computation
│   └── analyze_difficulty.py    # Case difficulty analysis
├── web/
│   ├── app.py                   # Flask web server
│   ├── routes/                  # REST API endpoints
│   ├── service_layer/           # Business logic & evaluation services
│   ├── static/                  # Vue 3 + Element Plus frontend
│   └── templates/               # HTML templates
├── figures/                     # Paper figures
├── tables/                      # LaTeX table sources
└── pyproject.toml
```

---

## Ethical Statement

The study protocol and annotation procedures were approved by the institutional ethics boards of all participating clinical centers. All data collection, processing, and annotation followed the *Declaration of Helsinki*. Since records were de-identified before construction, individual informed consent was waived. All processing was conducted within secure hospital environments using locally deployed models, and no identifiable patient information or intermediate records left institutional governance.

---

## Citation

If you use MentalHospital or MentalEval in your research, please cite:

```bibtex
@article{mentalhospital2025,
  title   = {MentalHospital: A Virtual Psychiatric Evaluation Environment
             for LLM-based Medical AI},
  author  = {Your Name and Collaborators},
  journal = {arXiv preprint},
  year    = {2025}
}
```

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

> **Note:** The EHR-derived case data (`data/cases.jsonl`) is provided for research purposes only under the terms of the collaborative data-use partnership. Please refer to the data use agreement before redistribution.
