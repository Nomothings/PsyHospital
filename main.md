# Introduction

Large language models (LLMs) have made substantial progress in
psychiatry [@lee2021artificial; @kolding2025use]. Existing studies have
reported strong performance on key clinical components, including
dialogue [@arora2025healthbench; @zhang2024cpsycoun; @racha2026omind; @liu2025interactive],
medical record understanding [@patel2022neuroblu], diagnostic
reasoning [@sun2026mentalseek], and treatment planning [@zhang2025cbt].
However, success on isolated clinical components remains insufficient to
reflect the integrated capability required in real-world clinical
encounters.

Recent studies have increasingly recognized the limitations of isolated
evaluation [@agrawal2025evaluation; @li2025counselbench]. Accordingly,
several works have begun exploring virtual medical environments for more
comprehensive clinical simulation and
assessment [@schmidgall2024agentclinic; @fan2025ai; @liu2026openhospital; @jiang2025medagentbench].
Yet, as summarized in
Table [\[tab:benchmark_comparison\]](#tab:benchmark_comparison){reference-type="ref"
reference="tab:benchmark_comparison"}, these environments still exhibit
three limitations: *(1) Encounter Incompleteness*. Existing environments
still center on doctor--patient communication, rather than complete
encounters across multiple clinical scenarios and tasks. *(2) Data
Inauthenticity*. The environmental evidence and reference targets are
often derived from synthetic or web-based data, limiting clinical
fidelity. *(3) Patient Simplification*. Virtual patients are often
reactive symptom carriers, rather than faithful and distinctive
psychiatric individuals.

To address these limitations, we introduce **MentalHospital**, to our
knowledge the first virtual evaluation environment designed for
psychiatric clinical encounters. MentalHospital moves beyond
dialogue-centered simulation by instantiating the full S.O.A.P.
workflow [@donohoe2015implementing], from interviewing and examination
to diagnosis and treatment planning. It is grounded in 1,193
de-identified psychiatric EHR cases covering all major ICD-11
psychiatric categories and 76 disorder-level diagnoses, and constructs
skill-augmented standardized patients with individualized symptom
presentation and dynamic memory recall. In each interaction, LLMs must
elicit evidence from the standardized patient, request auxiliary
examinations from hospital-side modules, generate clinical notes and
disorder-level decisions, and finally produce individualized treatment
plans.

MentalHospital evaluates each encounter through *objective comparison*
against EHR-derived references and *subjective assessment* of clinical
process quality. The former can be computed from structured clinical
targets, whereas the latter requires specialist judgment and is
difficult to scale with clinician review alone. Our validation further
shows that general-purpose LLM judges are insufficiently reliable for
specialist clinical assessment: LLM-as-a-Judge achieves only a QWK of
0.677, an accuracy of 0.225, and an MAE of 0.875. To address this gap,
we develop **MentalEval**, a suite of five domain-specific evaluators
covering communication empathy, interviewing professionalism,
clinical-note quality, diagnostic rigor, and treatment appropriateness.
MentalEval is trained in two stages: *(1) Rubric-grounded SFT*, which
teaches evaluators to generate rubric-based rationales and ratings from
multi-level evaluation trajectories, and *(2) Expert-guided DPO*, which
further aligns evaluator preferences with clinician-selected judgments.

We conduct experiments with LLMs, clinicians, medical trainees, and
crowdworkers. Expert and trainee ratings validate the clinical fidelity
of MentalHospital, with an overall score of 3.96/5, while ablations show
that the full patient construction achieves the best objective
faithfulness and subjective fidelity. MentalEval also achieves strong
expert alignment, reaching an average QWK of 0.944 after DPO and
outperforming LLM-as-a-Judge, Multi-LLM Jury, and individual crowdworker
baselines. Using this evaluation setting, we find that current LLMs
still lag behind clinicians in objective psychiatric competence: even
the strongest medical-specific model trails medical trainees by 27.17
percentage points and human experts by 37.28 points on average across
objective metrics, while showing complementary potential in empathic
communication and treatment assistance. Fine-grained analysis further
reveals a key weakness in mental status assessment. Finally, survey
responses from 22 clinicians indicate positive acceptance of
MentalHospital and its perceived value for psychiatric training. Our
contributions are summarized as follows:

- We introduce **MentalHospital**, an EHR-grounded benchmark environment
  for full S.O.A.P. psychiatric encounters, using skill-augmented
  standardized patients constructed from 1,193 de-identified psychiatric
  EHR cases spanning all major ICD-11 categories and 76 disorders.

- We design a dual-track evaluation protocol that combines objective
  comparison against EHR-derived references with subjective assessment
  of clinical process quality, and develop **MentalEval**, a suite of
  specialist-aligned evaluators for scalable subjective assessment.

- We conduct comprehensive experiments with LLMs, clinicians, medical
  trainees, and crowdworkers, validating MentalHospital's clinical
  fidelity and MentalEval's expert alignment while revealing persistent
  gaps between current LLMs and clinicians in mental status assessment.

<figure id="fig:intro" data-latex-placement="t">
<embed src="./figures/overview.pdf" />
<figcaption> Overview of MentalHospital. A virtual psychiatric
evaluation environment for LLM-based medical AI, built on the S.O.A.P.
workflow and designed for dual-track evaluation. </figcaption>
</figure>

# [MentalHospital]{.smallcaps}

## Data Processing

MentalHospital is constructed from 1,193 de-identified psychiatric EHR
cases obtained through an approved collaborative data-use partnership
with a coordinating medical center. The resulting dataset comprises
multi-center records sourced from six medical centers across three
regions. The dataset includes 885 single-diagnosis cases and 308
comorbid cases. These cases cover all major ICD-11 psychiatric
categories and 76 disorder-level diagnoses, providing broad
disorder-level diversity for virtual psychiatric simulation (see
Appendix [\[data_source_and_case_composistion\]](#data_source_and_case_composistion){reference-type="ref"
reference="data_source_and_case_composistion"}). Each case was
independently reviewed by two licensed psychiatrists to ensure clinical
completeness and consistency (Cohen's $\kappa > 0.8$). Details see
Appendix [\[app:data_distribution\]](#app:data_distribution){reference-type="ref"
reference="app:data_distribution"}. Each EHR case is converted into a
structured MentalHospital case $c$ with patient-side evidence,
examination-side evidence, and reference clinical targets:
$$\begin{equation}
x_c = \{\mathcal{K}^{\mathrm{pat}}_c, \mathcal{K}^{\mathrm{exam}}_c\},
\qquad
\mathcal{Y}^{*}_c =
\{y^{\mathrm{cat}*}_c, y^{\mathrm{dis}*}_c, y^{\mathrm{treat}*}_c\}.
\end{equation}$$ Here, $\mathcal{K}^{\mathrm{pat}}_c$ contains
patient-side evidence such as chief complaint, illness history, past and
family history, and mental status; $\mathcal{K}^{\mathrm{exam}}_c$
contains examination-side evidence such as physical and auxiliary
examination findings. The reference targets $\mathcal{Y}^{*}_c$ include
the diagnostic category $y^{\mathrm{cat}*}_c$, the disorder-level
diagnosis $y^{\mathrm{dis}*}_c$, and EHR-derived treatment information
$y^{\mathrm{treat}*}_c$. In MentalHospital,
$\mathcal{K}^{\mathrm{pat}}_c$ is used to instantiate the standardized
patient, $\mathcal{K}^{\mathrm{exam}}_c$ supports the hospital-side
examination module, and $\mathcal{Y}^{*}_c$ serves as the reference for
diagnostic and treatment evaluation. Details see
Appendix [\[app:data_processing\]](#app:data_processing){reference-type="ref"
reference="app:data_processing"}.

To protect privacy while preserving clinical meaning, each EHR is
processed using an on-premise `DeepSeek-R1` [@liu2025deepseek],
rule-based detectors, and expert review. Sensitive events, exact dates,
locations, institutions, and other identifiable details are generalized
or masked. Clinically relevant sensitive events are rewritten into
semantically similar but non-identifiable descriptions, so that
psychiatric evidence remains usable for simulation and evaluation.

The study protocol and annotation procedures were approved by the
institutional ethics boards of all participating clinical centers. All
data collection, processing, and annotation followed the *Declaration of
Helsinki*. Since records were de-identified before construction,
individual informed consent was waived. All processing was conducted
within secure hospital environments using locally deployed models, and
no identifiable patient information or intermediate records left
institutional governance.

## Interaction Process

Given a psychiatric case $c$, MentalHospital instantiates a
case-conditioned sequential environment: $$\begin{equation}
\mathcal{E}_c = \{\mathcal{P}_c, \mathcal{M}^{\mathrm{exam}}_c\},
\end{equation}$$ where $\mathcal{P}_c$ denotes the standardized patient
constructed from patient-side evidence $\mathcal{K}^{\mathrm{pat}}_c$,
and $\mathcal{M}^{\mathrm{exam}}_c$ denotes the hospital-side
examination module supported by examination-side evidence
$\mathcal{K}^{\mathrm{exam}}_c$. The doctor agent cannot directly access
$\mathcal{K}^{\mathrm{pat}}_c$, $\mathcal{K}^{\mathrm{exam}}_c$, or
$\mathcal{Y}^{*}_c$, but must recover clinical evidence and infer
decisions through interaction.

As shown in Figure [1](#fig:intro){reference-type="ref"
reference="fig:intro"}, MentalHospital follows the clinical S.O.A.P.
workflow. In the subjective interviewing stage, the doctor asks
psychiatric interview questions and receives patient responses from
$\mathcal{P}_c$, aiming to recover patient-side evidence such as
symptoms, illness history, and mental status. In the objective
examination stage, the doctor recommends examinations, and
$\mathcal{M}^{\mathrm{exam}}_c$ returns the corresponding EHR-derived
results when available. In the diagnostic assessment stage, the doctor
integrates the dialogue trajectory and examination findings to generate
a clinical note and diagnostic hypotheses. In the treatment planning
stage, the doctor produces a treatment plan based on the accumulated
evidence and diagnostic assessment. The interaction history is updated
step by step: $$\begin{equation}
h_t = h_{t-1} \cup \{(a_t,o_t)\},
\end{equation}$$ where $a_t$ is the doctor action and $o_t$ is the
environment observation returned by either the standardized patient or
the examination module. After completing the workflow, each episode
produces $$\begin{equation}
\hat{y}_c =
\left\{
\tau_c,\,
\hat{\mathcal{A}}^{\mathrm{exam}}_c,\,
\hat{n}_c,\,
\hat{d}_c,\,
\hat{p}_c
\right\},
\end{equation}$$ where $\tau_c$ is the doctor--patient trajectory,
$\hat{\mathcal{A}}^{\mathrm{exam}}_c$ is the recommended examination
set, $\hat{n}_c$ is the clinical note, $\hat{d}_c$ is the diagnosis with
reasoning, and $\hat{p}_c$ is the treatment plan. Detailed interaction
details are provided in the
Appendix [\[app:interaction_prompt\]](#app:interaction_prompt){reference-type="ref"
reference="app:interaction_prompt"}.

## Environment Modules

MentalHospital consists of an environment controller, a standardized
patient agent, a hospital-side examination module, and the doctor agent
under evaluation. The controller manages the S.O.A.P. stage transitions,
routes doctor actions to the corresponding module, records intermediate
outputs, and issues instructions for completing the episode. See the
Appendix [\[app: module_prompts\]](#app: module_prompts){reference-type="ref"
reference="app: module_prompts"} for implementation details.

#### Environment Controller.

The controller coordinates the S.O.A.P. interaction process. It
maintains the interaction history $h_t$, records the doctor--patient
trajectory $\tau_c$, collects examination requests
$\hat{\mathcal{A}}^{\mathrm{exam}}_c$, and stores downstream outputs
including the clinical note $\hat{n}_c$, diagnosis $\hat{d}_c$, and
treatment plan $\hat{p}_c$. It ensures that the doctor agent interacts
with the appropriate module at each stage.

#### Standardized Patient.

The standardized patient $\mathcal{P}_c$ is constructed from
patient-side evidence $\mathcal{K}^{\mathrm{pat}}_c$ as a
skill-augmented patient configuration: $$\begin{equation}
\mathcal{C}_c=\{\mathcal{R}_c,\mathcal{S}^{\mathrm{pre}}_c,\mathcal{S}^{\mathrm{mem}}_c\},
\end{equation}$$ where $\mathcal{R}_c$ specifies role information,
$\mathcal{S}^{\mathrm{pre}}_c$ encodes individualized symptom
presentation grounded in the EHR mental status examination, and
$\mathcal{S}^{\mathrm{mem}}_c$ stores patient-side evidence as
topic-level memory units. During interaction, the patient maintains an
active memory state rather than exposing all memory units at once. Given
the doctor action $a_t$ and history $h_{t-1}$, the memory skill
determines whether the current topic should be maintained or switched:
$$\begin{equation}
m_t=\mathrm{UpdateMem}(m_{t-1},a_t,h_{t-1},\mathcal{S}^{\mathrm{mem}}_c).
\end{equation}$$ After updating the active memory, the patient generates
a content-level response from the current recalled experience and role
information, and then renders it with the presentation skill:
$$\begin{equation}
\tilde{u}_t^{\mathrm{pat}}
\sim
\pi_{\mathrm{pat}}^c(\cdot\mid h_{t-1},a_t,\mathcal{R}_c,m_t),
\qquad
o_t^{\mathrm{pat}}
=
\mathrm{Render}(\tilde{u}_t^{\mathrm{pat}},\mathcal{S}^{\mathrm{pre}}_c).
\end{equation}$$ The final observation $o_t^{\mathrm{pat}}$ contains
both behavioral presentation and verbal response, enabling the doctor
agent to infer clinical evidence from both how the patient presents and
what the patient states. This hybrid design ensures that the patient
agent discloses only information supported by the retrieved memory while
avoiding unrelated, unasked, or future-stage clinical information.

#### Examination Module.

The examination module $\mathcal{M}^{\mathrm{exam}}_c$ is implemented as
a hospital-side question-answering interface based on
`DeepSeek-V4-Flash` [@liu2025deepseek]. It receives examination requests
from the doctor agent and returns results according to the
examination-side evidence $\mathcal{K}^{\mathrm{exam}}_c$. If a
requested examination exists in $\mathcal{K}^{\mathrm{exam}}_c$, the
module returns the corresponding EHR-derived report; otherwise, it
returns *"result unavailable"*. The module also records the requested
examination set $\hat{\mathcal{A}}^{\mathrm{exam}}_c$ for comparison
with the EHR-derived reference set when calculating examination
coverage.

## Dual-track Evaluation

MentalHospital evaluates each completed episode through *objective
comparison* and *subjective assessment*. Objective comparison measures
outcome-level task correctness against EHR-derived references.
Subjective assessment evaluates process-level clinical professionalism
and interpretability using expert-defined rubrics. Detailed metrics are
provided in Section [4.0.0.2](#sec:experiments){reference-type="ref"
reference="sec:experiments"}.

# [MentalEval]{.smallcaps}

We explored two approaches to scalable subjective evaluation:
crowdworker review and rubric-prompted general-purpose LLM judges.
Experiment [4.4](#MentalEval_test){reference-type="ref"
reference="MentalEval_test"} shows that crowdworker review is reasonably
aligned with specialists (QWK = 0.904, Acc. = 0.625, MAE = 0.375), yet
costly to scale, while LLM-as-a-Judge shows limited specialist agreement
(QWK = 0.677, Acc. = 0.225, MAE = 0.875).We therefore develop
**MentalEval**, a suite of five Qwen3-8B-based domain-specific
evaluators trained with rubric-grounded SFT followed by expert-guided
DPO. The evaluators assess communication empathy, interviewing
professionalism, clinical-note quality, diagnostic rigor, and treatment
appropriateness. Given an evaluation context such as dialogue, clinical
note, diagnostic reasoning, or treatment recommendation, each evaluator
outputs a rubric-grounded rationale and a Likert-style 1--5 rating.
Detailed rubrics are provided in
Appendix [\[app:rubrics\]](#app:rubrics){reference-type="ref"
reference="app:rubrics"}.

<figure id="fig:mentaleval" data-latex-placement="t">
<embed src="./figures/Mentaleval.pdf" />
<figcaption>Overview of MentalEval construction. MentalEval is trained
on MentalHospital interaction data via rubric-grounded SFT and
expert-guided DPO for subjective clinical evaluation.</figcaption>
</figure>

## Stage 1: Rubric-grounded SFT

The first stage provides a cold start for learning rubric-grounded
evaluation patterns. We sample 200 cases for evaluator training, then
select 20 LLMs covering different providers, model scales, and
specialties, and run each model three times on each case, yielding
complete interaction episodes. As shown in
Figure [2](#fig:mentaleval){reference-type="ref"
reference="fig:mentaleval"}, these episodes are further decomposed into
stage-level interaction data for the five subjective evaluation
dimensions. For each stage-level sample $z_i$, we use a judge ensemble
$\mathcal{J}$ of five LLMs (`DeepSeek-V4-Pro` [@liu2025deepseek],
`KIMI-K2.6` [@team2025kimi], `GPT-5.5` [@singh2025openai],
`Claude-Opus-4.6` [@bai2022constitutional], and
`Gemini-3.1-Pro` [@team2024gemma]) to generate rubric-based evaluation
trajectories and ratings: $$\begin{equation}
(s_{i,j}, r_{i,j}) = J_j(z_i, \mathcal{B}), 
\qquad j \in \mathcal{J}, \quad r_{i,j}\in\{1,\ldots,5\},
\end{equation}$$ where $\mathcal{B}$ denotes the expert consensus
rubric, $s_{i,j}$ is the generated evaluation trajectory, and $r_{i,j}$
is the assigned score. To filter reliable supervision, we retain only
judge outputs with sufficient score agreement. Specifically, the
consensus score for $z_i$ is defined as: $$\begin{equation}
r_i^{*}
=
\arg\max_{r\in\{1,\ldots,5\}}
\sum_{j\in\mathcal{J}}\mathbf{1}[r_{i,j}=r].
\end{equation}$$ If at least $k$ judges assign $r_i^{*}$, the
trajectories with score $r_i^{*}$ are retained as high-quality SFT
targets; otherwise, the candidate set is treated as low-confidence and
reserved for preference construction. Because extreme scores are
underrepresented, we additionally select near-boundary samples and
rewrite 2-point cases toward 1-point quality and 4-point cases toward
5-point quality. These augmented samples are retained only after
judge-ensemble verification. The SFT objective is: $$\begin{equation}
\mathcal{L}_{\mathrm{SFT}}
=
-\mathbb{E}_{(z,s)\sim\mathcal{D}_{\mathrm{SFT}}}
\log \pi_{\theta}(s\mid z).
\end{equation}$$

## Stage 2: Expert-guided DPO

After cold-start training, we further align MentalEval with specialist
judgment using expert-guided preference optimization. For each
low-confidence candidate set
$\mathcal{S}_i=\{(s_{i,1},r_{i,1}),\ldots,(s_{i,5},r_{i,5})\}$, we
present the original stage-level interaction data $z_i$ and the
candidate evaluation trajectories to clinicians. The clinician selects
the trajectory $s_i^{*}$ whose rating and rationale best match the
clinical quality of $z_i$. Candidate trajectories with the same score as
$s_i^{*}$ are treated as chosen responses, while the remaining
trajectories are treated as rejected responses: $$\begin{equation}
\mathcal{S}_i^{+}=\{s_{i,j}\mid r_{i,j}=r_i^{*}\},
\qquad
\mathcal{S}_i^{-}=\{s_{i,j}\mid r_{i,j}\ne r_i^{*}\}.
\end{equation}$$ We then construct preference triples
$(z_i,s_i^{+},s_i^{-})$ for DPO training. The DPO objective is:
$$\begin{equation}
\mathcal{L}_{\mathrm{DPO}}
=
-\mathbb{E}_{(z,s^+,s^-)}
\log \sigma\left(
\beta
\left[
\log\frac{\pi_{\theta}(s^+\mid z)}{\pi_{\mathrm{ref}}(s^+\mid z)}
-
\log\frac{\pi_{\theta}(s^-\mid z)}{\pi_{\mathrm{ref}}(s^-\mid z)}
\right]
\right).
\end{equation}$$ Detailed MentalEval training settings are provided in
Appendix [\[app:training_settings\]](#app:training_settings){reference-type="ref"
reference="app:training_settings"}.

# Experiments

#### Task Definition.

We formulate evaluation as a multi-stage, mixed-type clinical task.
Given a case $c$, a doctor agent completes an episode covering
subjective interviewing, objective examination, diagnostic assessment,
and treatment planning. The task combines three forms: (1) open-ended
generation, including dialogue, clinical-note writing, diagnostic
reasoning, and treatment planning; (2) multi-label decision making,
including examination recommendation and category-level diagnosis; and
(3) ranked disorder prediction, for definitive diagnosis. We evaluate
the resulting trajectory and stage outputs from two perspectives: (i)
objective comparison, which measures EHR-grounded outcomes, and (ii)
subjective assessment, which measures process-level clinical quality.

#### Evaluation Metrics. {#sec:experiments}

For EHR-grounded outputs, including examination recommendation (Exam.),
clinical interviewing (Inter.), and clinical-note generation (Note), we
measure reference coverage: $$\begin{equation}
\mathrm{Coverage}(y_c, \mathcal{K}_c)
=
\frac{1}{|\mathcal{K}_c|}
\sum_{k \in \mathcal{K}_c}
\mathbb{I}\left[ k \preceq y_c \right],
\end{equation}$$ where $\mathcal{K}_c$ denotes the EHR-derived reference
checkpoint set for case $c$, and $k \preceq y_c$ indicates that
checkpoint $k$ is semantically entailed by the generated output $y_c$.
We use a conservative semantic similarity threshold of $\tau=0.85$ for
high-precision automatic matching, and adjudicate pairs below the
threshold with an empirically validated Multi-LLM-assisted semantic
matching procedure. For definitive diagnosis, we report category
identification (Cate.) and disorder-level diagnosis ranking (Diso.),
with nDCG used to evaluate diagnostic prioritization. For subjective
assessment, MentalEval scores communication empathy (Emp.), interviewing
professionalism (Prof.), clinical-note quality (Qual.), diagnostic rigor
(Rigor), and treatment appropriateness (App.) using expert-defined
rubrics. For more details see
Appendix [\[app:metrics\]](#app:metrics){reference-type="ref"
reference="app:metrics"}.

#### Comparison Groups.

We consider five comparison groups: human experts, medical trainees,
crowdworkers, general-purpose LLMs, and medical-specific LLMs. The
expert group consists of 5 licensed psychiatrists and 3 psychology
experts. We also include 14 medical trainees and 8 non-specialist
crowdworkers. For LLMs, we evaluate a set of general-purpose models,
including Llama-3-8B [@grattafiori2024llama],
Qwen3-14B [@yang2025qwen3], GPT-OSS-20B [@agarwal2025gpt],
QwQ-32B [@yang2025qwen3], GPT-OSS-120B [@agarwal2025gpt],
DeepSeek-V4-Pro [@liu2025deepseek], GPT-5.5 [@singh2025openai], and
Claude-Sonnet-4-6 [@bai2022constitutional]. We also include
medical-oriented LLMs, including
MedGemma-4B-it [@sellergren2025medgemma],
MedGemma-27B-it [@sellergren2025medgemma], and
Baichuan-M2 [@dou2025baichuan].

## Can LLMs Interact Like Clinicians?

We evaluate 12 LLMs, 8 human experts, and 14 medical trainees in
MentalHospital. As shown in
Table [\[tab:main_results\]](#tab:main_results){reference-type="ref"
reference="tab:main_results"}, current LLMs still show a clear gap from
clinicians in objective clinical competence. Compared with the strongest
medical-specific model, Baichuan-M2, medical trainees achieve higher
scores across all five objective metrics, with an average gap of 27.17
percentage points; human experts further widen this gap to 37.28 points.
In subjective assessment, LLMs and clinicians show complementary
strengths rather than uniform superiority of either group. Human experts
exhibit stronger interviewing professionalism (4.25), reflecting more
efficient, goal-directed clinical information gathering, but receive
lower scores in expressed communication empathy (1.22). In contrast, the
best-performing LLMs reach or exceed human experts in expressed empathy
(2.16 vs. 1.22), diagnostic rigor (3.14 vs. 2.54), and treatment
appropriateness (3.48 vs. 2.96), while remaining lower in interviewing
professionalism (3.72 vs. 4.25) and clinical-note quality (3.89 vs.
4.01). These results suggest that LLMs are not yet reliable substitutes
for clinicians, but may provide complementary value in verbal affective
support and evidence-informed treatment assistance.

## Where Do LLMs Fall Short in Clinical Interaction?

To identify the core gap, we decompose coverage in clinical interviewing
and note generation into Chief Complaint (CC) and Mental Status (MS) in
Table [\[tab:interview_note\]](#tab:interview_note){reference-type="ref"
reference="tab:interview_note"}, current LLMs fail to recognize the
clinical importance of mental status examination in psychiatric
assessment and diagnosis. For example, `GPT-5.5` shows a large gap in
interviewing (85.38 vs. 55.72), and `DeepSeek-v4-Pro` exhibits a similar
pattern in note generation (59.94 vs. 43.91).

## Does Skill-Augmented Patient Construction Improve Fidelity?

We evaluate patient construction fidelity through objective evaluation
and subjective assessment, with detailed experimental settings provided
in
Appendix [\[app:patient_ablation\]](#app:patient_ablation){reference-type="ref"
reference="app:patient_ablation"}. As shown in
Table [\[tab:patient_ablation\]](#tab:patient_ablation){reference-type="ref"
reference="tab:patient_ablation"}, naive prompting achieves reasonable
factual faithfulness but performs poorly in subjective fidelity,
indicating that directly exposing the EHR does not yield realistic
patient simulation. Representation skill substantially improves clinical
realism and patient distinctiveness, while memory skill improves
evidence coverage, precision, and hallucination control. The full
construction achieves the best overall performance.

<figure id="fig:agreement_heatmaps" data-latex-placement="t">
<embed src="./figures/agreement_heatmaps.pdf" />
<figcaption>Agreement with expert ratings, where MentalEval shows the
strongest alignment.</figcaption>
</figure>

## Does MentalEval Align with Expert Judgment? {#MentalEval_test}

MentalEval is designed as a task-specific evaluator for MentalHospital,
rather than a general-purpose LLM judge across arbitrary clinical tasks.
Our goal is therefore to test whether it can reproduce expert judgments
within the MentalHospital evaluation setting.To avoid evaluation
leakage, we additionally sampled 40 psychiatric EHR cases from the
coordinating medical center to construct the MentalEval test set. These
cases were strictly excluded from all MentalEval training data. For each
case, we sample model-generated responses and evaluate them across the
five MentalEval dimensions, yielding 200 dimension-level test samples in
total. Each sample is independently rated by three experts, and only
unanimously assigned samples are retained as expert-validated
references. We ablate the two-stage training procedure on this held-out
set of unseen expert-labeled cases. As shown in
Table [\[tab:mentaleval_ablation\]](#tab:mentaleval_ablation){reference-type="ref"
reference="tab:mentaleval_ablation"}, rubric-grounded SFT consistently
improves all five evaluators, increasing average QWK from 0.759 to 0.879
and reducing MAE from 0.710 to 0.380. Expert-guided DPO further improves
agreement, reaching an average QWK of 0.944, accuracy of 0.790, and MAE
of 0.210. We then compare the trained MentalEval with LLM-as-a-Judge,
Multi-LLM Jury, and individual crowdworker ratings in
Figure [3](#fig:agreement_heatmaps){reference-type="ref"
reference="fig:agreement_heatmaps"}. MentalEval achieves the strongest
expert alignment, with the highest QWK (0.926) and accuracy (0.725), and
the lowest MAE (0.275).

## Does MentalHospital Provide a Clinically Faithful Environment?

::: wrapfigure
r0.55
![image](./figures/experiments_faithful_scale.pdf){width="\\linewidth"}
:::

We conduct a survey to assess the clinical faithfulness with 5
psychiatrists, 3 psychologists, and 14 medical trainees (full
questionnaire is see
Appendix [\[app:faithfulness_questionnaire\]](#app:faithfulness_questionnaire){reference-type="ref"
reference="app:faithfulness_questionnaire"}). The questionnaire covers
five dimensions: clinical realism (CR), patient fidelity (PF), patient
distinctiveness (PD), evaluation credibility (EC), and training
suitability (TS), using a 5-point Likert scale. As shown in
Figure [\[fig:faithful_scale\]](#fig:faithful_scale){reference-type="ref"
reference="fig:faithful_scale"}, MentalHospital receives consistently
positive ratings, with an overall mean score of 3.88/5 (95% bootstrap
CI: \[3.78, 3.98\]), a positive response rate of 69.9% (95% CI: \[64.8%,
75.0%\]), and a negative response rate of only 5.1% (95% CI: \[3.4%,
6.8%\]). The ratings are particularly strong for training suitability
and evaluation credibility, with positive response rates of 84.8% and
75.0%, suggesting that MentalHospital provides a clinically plausible
environment.

## Qualitative Error Analysis

::: wrapfigure
r0.55 ![image](./figures/case_study.pdf){width="\\linewidth"}

[]{#fig:case_study label="fig:case_study"}
:::

Figure [\[fig:case_study\]](#fig:case_study){reference-type="ref"
reference="fig:case_study"} illustrates two representative failure modes
observed in MentalHospital. In a case involving anxiety and possible
perceptual disturbance, `GPT-5.5` directly probes hallucination-related
features such as source and content, yielding higher objective evidence
coverage than `Qwen3-14B`. However, its response contains limited
empathic acknowledgment, resulting in a lower MentalEval empathy score.
Conversely, `Qwen3-14B` provides more explicit emotional validation and
reassurance, but fails to pursue the hallucination hypothesis through
targeted psychiatric questioning. This contrast shows that
evidence-seeking behavior and process-level communication quality can
diverge substantially. A model may recover key diagnostic evidence while
offering poor affective support, whereas another may appear empathic but
remain clinically under-informative.

# Related Work

#### Psychiatric Benchmarks.

Early medical LLM evaluation mainly relied on static question-answering
benchmarks, testing medical knowledge recall and exam-style clinical
reasoning [@singhal2025toward; @tu2024towards]. This paradigm was later
expanded to broader medical evaluation suites and real-world clinical
benchmarks covering diverse tasks, safety, and clinical
reliability [@chen2024gmai; @bedi2025medhelm; @zhang2025llmeval; @arora2025healthbench],
with subsequent work further examining clinical safety, expert
consensus, and specialized
reasoning [@wang2025novel; @mehandru2025er; @yan2026livemedbench; @zheng2026clinconsensus].
In parallel, mental-health benchmarks began to assess counseling,
emotional support, and
psychotherapy [@li2025counselbench; @xu2025mentalchat16k; @zhang2025cbt],
while clinically oriented psychiatric benchmarks focused on psychiatric
practice, disorder recognition, and diagnostic
reasoning [@liu2025psychbench; @fouda2025psychiatrybench; @sun2026mentalseek; @song2026mentalbench].
These efforts connect subclinical mental-health support with
threshold-level psychiatric assessment, but still largely evaluate
isolated responses or task-specific outputs. Recent work has moved
toward multi-turn dialogue and simulated clinical environments, testing
contextual interaction across
turns [@zhang2024cpsycoun; @racha2026omind; @liu2025interactive; @li2024mediq; @yao2025dischargesim; @pombal2025mindeval]
and patient--doctor
simulation [@schmidgall2024agentclinic; @fan2025ai; @liu2026openhospital; @sviridov20253mdbench; @almansoori2025self; @xu2026lingxidiagbench].
However, existing benchmarks still rarely support virtual psychiatric
encounters.

#### Evaluation Methods.

Early evaluation of LLM outputs mainly relied on task accuracy and
surface-level automatic metrics, including lexical overlap and
embedding-based
similarity [@papineni2002bleu; @lin2004rouge; @banerjee2005meteor; @zhang2019bertscore].
These metrics remain common in benchmark-based assessment and text
generation evaluation [@singhal2023large; @zhang2025llmeval], but they
are insufficient for clinically nuanced behaviors such as empathy,
professionalism, diagnostic rigor, and treatment appropriateness. Later
work therefore incorporated clinician-centered or expert-based
protocols [@kocaman2025clinical; @arora2025healthbench], with similar
trends in clinical safety and reasoning
benchmarks [@wang2025novel; @zhou2025automating]. Although expert review
improves clinical validity, it is difficult to scale. Recent studies
have explored model-based judging, including judge-style, jury-style,
and rubric-driven
frameworks [@croxford2025evaluating; @bedi2025medhelm; @lee2025checkeval],
while also highlighting reliability concerns of LLM-based judges in
medical
settings [@belmadani2026judges; @williams2025human; @gu2024survey].
Existing methods therefore still struggle to balance expertise and
scalability, especially for subjective mental-health evaluation where
process quality cannot be reduced to objective correctness alone.

# Conclusion

We present MentalHospital, a virtual psychiatric evaluation environment
for LLM-based medical AI. MentalHospital supports interactive
S.O.A.P.-based psychiatric assessment with EHR-grounded virtual patients
and a dual-track evaluation protocol that combines objective comparison
with scalable subjective assessment. To operationalize specialist
judgment, we develop MentalEval, a suite of five domain-specific
evaluators trained through rubric-grounded SFT and expert-guided DPO.
Experiments show that current LLMs remain limited in clinician-like
psychiatric interaction, especially in mental status assessment, while
MentalHospital and MentalEval provide faithful and scalable tools for
evaluating in psychiatric care. Finally, clinician survey responses
indicate positive acceptance of MentalHospital and its perceived value
for psychiatric training.

[^1]: Use footnote for providing further information about author
    (webpage, alternative address)---*not* for acknowledging funding
    agencies.
