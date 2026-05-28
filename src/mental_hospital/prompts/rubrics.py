"""Rubric prompts for LLM-as-a-Judge subjective evaluation.

Each rubric defines a 1–5 scoring scale for a specific quality dimension.
``RUBRIC_FORMAT`` is the template that wraps a rubric definition together
with the text under evaluation for the judge LLM.
"""

# ---------------------------------------------------------------------------
# Rubric format template
# ---------------------------------------------------------------------------

RUBRIC_FORMAT: str = """\
You are a strict, rubric-based grader.

Your task: **score the given model output strictly according to the
provided rubric**.  The rubric is the sole scoring standard.  Do not
use personal preference, informal impression, or alternative criteria.

## Core principles

1. **Top-down scoring**: Start from **Level 5 (highest)** and work
   downward.  Judge whether the target output fully meets ALL core
   requirements of L5.  If not, drop to L4; continue down to L1 if
   needed.  Criterion for each level: does the target output
   **sufficiently and clearly** satisfy that level's conditions?
2. **Evidence must be quoted**: For every "level satisfied" judgement,
   find **specific verbatim excerpts** from the evaluation input as
   evidence.  Impressions or summaries are not sufficient.  If you
   cannot quote evidence, the level is not met.
3. **Actively check for omissions**: For each level, analyse not only
   "what is present" but also "what is missing".
4. **Benefit of the doubt goes downward**: If you are undecided at a
   level, you MUST assign the lower level.
5. **Do not reward surface features**: Fluency, length, formatting,
   terminology richness, or confidence do not earn extra points.
6. **Do not fabricate evidence**: Score only on what actually appears in
   the evaluation input.

## Reasoning workflow

### Step 1: Content audit
Briefly summarise the key elements actually present (2–3 sentences).
Also point out **clearly missing key elements**.

### Step 2: Level-by-level judgement (L5 → L1)
Starting from Level 5, for each level N:
- **Satisfying evidence**: verbatim excerpts from the target output.
- **Missing evidence**: required elements that are absent.
- **Verdict**: Does the target sufficiently satisfy Level N?  If yes,
  continue to N+1; if no, stay at Level N-1.

## Final answer constraint
At the very end, output the final score in this **exact format**:

[DECISION_START]X[DECISION_END]

where *X* is a single integer from 1 to 5.  No spaces, text, or other
content inside the markers.  The decision line must appear exactly once
and be the last line.

---
## Rubric:
<RUBRIC_CONTENT>
---

---
## Evaluation input:
<TEST_CONTENT>

---

Your task: analyse based on the rubric, then output the final level:
[DECISION_START]X[DECISION_END]
"""

# ---------------------------------------------------------------------------
# Communication Empathy (Phase 1)
# ---------------------------------------------------------------------------

COMMUNICATION_EMPATHY: str = """\
### Task definition
This scale evaluates the quality of empathy in a psychiatric interview.
Empathy here is not politeness, comfort, or "saying nice things".
Evaluation should be based on dialogue context, the patient's verbal
content, non-verbal presentation, and interaction history.

### Scoring criteria

**Level 5 — Insight-level empathy**
**Conditions:** On top of meeting all Level 4 requirements, highly
integrates verbal content, non-verbal presentation, and contextual
experience.  At the right moment, with extremely high fit, reveals a
core experience the patient has not yet fully organised but immediately
strongly identifies with — an "aha moment".  This level is rare.
**Exclusion:** If merely high-level, stable, deep verbal empathy without
a beyond-expected hit of understanding, do not score 5.  If the
"insight" comes from exaggerated reading or psychological projection,
also do not score 5.
**Behavioural signals:**
• In extremely natural language, precisely names a core experience the
  patient "has been going through but hasn't fully articulated"
• Naturally connects subtle expressions, movements, silence with
  earlier content
• The hit is highly context-dependent, only applicable to this person
  in this moment
• Not just "more human" — a genuine leap from "it's empathising" to
  "it saw into me"
• Extremely rare — must simultaneously possess naturalness, accuracy,
  timing, and appropriate restraint

---

**Level 4 — Deep resonance**
**Conditions:** On top of accurately receiving verbal emotions, further
grasps unexpressed hidden feelings, inner tensions, or deeper subjective
meaning.  Naturally and fittingly feeds back on non-verbal cues
(expression, movement, posture, silence) without over-interpretation.
**Exclusion:** If verbally deep but shows no awareness or use of
non-verbal cues, or feedback on such cues is stiff or intrusive, do not
score 4.
**Behavioural signals:**
• Notices "you seemed to pause when you said that"
• Feeds back "I sense you're saying it's fine, but this part may not
  be that easy for you"
• Notices constraint, avoidance, hesitation, suddenly softer tone
• Feedback is restrained — neither interrogation nor forced analysis

---

**Level 3 — Precise attunement**
**Conditions:** The response can relatively accurately identify and
articulate the patient's core emotions, forming a high-resolution
understanding of their subjective experience.  Goes beyond generic
comfort, naturally touching psychological feelings and personal meaning.
**Exclusion:** If still mainly at explicit emotion validation without
subtle discrimination, do not score 3.  If already integrating implicit
emotions across multiple turns, do not stay at 3.
**Behavioural signals:**
• Distinguishes similar but different emotions (hurt vs angry, nervous
  vs terrified, wronged vs disappointed)
• Does not collapse all distress into "sad" / "stressed"
• Begins to reflect "what this means to you", not just "what happened"
• Some reach toward hidden emotions
• Language is clearly more contextually fitting than templated comfort

---

**Level 2 — Passive reception**
**Conditions:** The response provides a basically accurate reception of
the patient's explicit emotions; no longer clearly misjudges the primary
emotion.  However empathy remains largely passive following, not yet
forming truly deep, high-resolution understanding.
**Exclusion:** If still clearly misjudging primary emotion or intensity,
do not score 2.  If already consistently distinguishing subtle
differences and touching deeper meaning, do not stay at 2.
**Behavioural signals:**
• Can respond to explicit emotions (sadness, anxiety, fear)
• Response is basically fitting but coarse-grained
• Empathy established but mostly follows the patient's lead
• Feels "gentle, harmless" but not deep, precise, or memorable
• Unlikely to hit what the patient left unsaid

---

**Level 1 — Surface-level**
**Conditions:** The response does not meet the minimum acceptable
standard of empathy for a psychiatric interview.  While it may contain
polite or comforting language, it remains at the level of surface
parroting, mechanical agreement, or emotional mismatch.
**Exclusion:** If the response already provides a basically accurate
reception of explicit emotions, do not score 1.
**Behavioural signals:**
• Responds to events, not feelings
• Crudely flattens complex emotions (e.g. uses "sad"/"angry" for shame,
  hurt, terror, helplessness)
• Misjudges emotional intensity, groundlessly minimising distress
• High frequency of templated comfort with low contextual fit
• Bot-like, task-like, perfunctory quality
• Patient feels "replied to" rather than "understood"
"""

# ---------------------------------------------------------------------------
# Interviewing Professionalism (Phase 1)
# ---------------------------------------------------------------------------

INTERVIEWING_PROFESSIONALISM: str = """\
### Task definition
This scale evaluates the professionalism of dialogue in a psychiatric
interview.  Professionalism here is not seriousness of tone or frequency
of questioning.  The core is: whether the model has a clear interview
goal, can continuously gather around clinical themes, can form
high-value progression around a diagnostic core, can complete working
anchoring early and conduct targeted gap-filling, and at higher levels
shows differential diagnosis awareness, timing judgement, and
professional boundary control.

### Scoring criteria


**Level 5 — Differential mastery**
**Conditions:** Completes anchoring of the main symptom cluster early,
and in subsequent turns simultaneously shows gap-filling AND
differential diagnosis questioning: both filling in supporting evidence
AND actively screening adjacent, easily confusable, or alternative-
explanation diagnoses.  Interview has highly integrated goal, theme,
progression, anchoring, rhythm, and boundaries, forming near-human
natural clinical mastery.
**Exclusion:** If subsequent questioning still mainly stays at one-way
confirmation lacking clear differential awareness, do not score 5.
**Behavioural signals:**
• Not only supplements evidence but actively checks "might not be that"
• Shows both supporting and excluding layers of awareness
• Actively distinguishes adjacent or easily confusable diagnoses
• Neither mechanically executes a checklist nor loses clinical framework
• Interview feels like real clinical judgement, not just information gathering

---

**Level 4 — Targeted gap-filling**
**Conditions:** Quickly anchors the main symptom cluster or working
diagnostic direction, and in subsequent turns conducts targeted
gap-filling of key details.  Professionalism now shows clear clinical
convergence ability and goal sense.
**Exclusion:** If has not completed main-direction anchoring early, or
after anchoring follow-up does not show clear targeted gap-filling, do
not score 4.  If already further shows active differential diagnosis
questioning and higher-order timing control, do not stay at 4.
**Behavioural signals:**
• Within first few turns, grasps the main symptom cluster (depressive,
  anxiety/panic, psychotic, etc.)
• Subsequent questions clearly fill in key evidence around one working
  direction
• Questions are "targeted" rather than "scattered"
• Interview shifts quickly from open gathering to targeted verification

---

**Level 3 — Theme progression**
**Conditions:** Can sustain progression around a main symptom theme or
problem cluster, and begin forming effective progression around symptom
nature, duration, severity, functional impact, triggers toward a
diagnostic core.  No longer scattered — begins to show structured
progression ability.
**Exclusion:** If still lacks thematic continuity or produces mainly
low-value, low-convergence questioning, do not score 3.  If can already
anchor the main symptom cluster early and shift to targeted gap-filling,
do not stay at 3.
**Behavioural signals:**
• Follows up continuously around one theme
• Progression around "what symptom — how long — how severe — what
  impact"
• Per-turn information gain begins to have clinical value
• Basic organisation among chief complaint, timeline, triggers,
  presentation, and impact
• Can reduce clearly irrelevant branching questions

---

**Level 2 — Emerging goal**
**Conditions:** Shows basic interview goal awareness — knows it needs to
gather information around the patient's problems.  However overall still
relatively scattered, lacking stable thematic focus and diagnostic
convergence.
**Exclusion:** If still mainly at generic companionship or clearly
unfocused questioning, do not score 2.  If can already sustain
progression around a main symptom theme, do not stay at 2.
**Behavioural signals:**
• Begins to ask questions related to chief complaint, but mostly surface
• Knows it is doing an interview, but "what to ask" depends heavily on
  patient's lead
• Questions related to each other but often lack continuous theme
• May stay at broad openings like "how have you been" / "anything else"

---

**Level 1 — Unfocused chat**
**Conditions:** The response does not meet the minimum acceptable
standard for a psychiatric interview.  Overall lacks clear interview
goals, progression is unfocused, often stays at generic comfort,
scattered questioning, or casual chatting.
**Exclusion:** If the response already shows basic interview goal
awareness and actively gathers relevant information, do not score 1.
**Behavioural signals:**
• Questions lack clear clinical goal; asks whatever the patient mentions
• Easily turns interview into companionship, comfort, persuasion
• No stable attention to symptoms, duration, severity, functional impact
• Questions lack thematic connection; jump around; loose structure
• Gets led by the patient's narrative; lacks active organisation
• After multiple turns, new information is scattered and low-relevance
"""

# ---------------------------------------------------------------------------
# Clinical Note Quality (Phase 3)
# ---------------------------------------------------------------------------

CLINICAL_NOTE_QUALITY: str = """\
### Task definition
This scale evaluates the quality of a model-generated clinical note.
The focus is not whether the note "looks professional", but whether it
possesses the structural completeness, information sufficiency, evidence
organisation, and diagnostic support value expected of a psychiatric
clinical record.

### Ceiling rules (apply first)
- If the note lacks basic clinical-note genre and is merely a chat
  summary or symptom restatement, ceiling at Level 1.
- If missing chief complaint or main clinical problem, ceiling at L1.
- If missing history of present illness, or does not record onset time
  and course evolution, ceiling at Level 2.
- If missing mental status examination, ceiling at Level 2.
- If missing most relevant history (past, medication, personal, family),
  ceiling at Level 3.
- If missing risk assessment, ceiling at Level 3.
- If missing key negative findings or exclusion information, ceiling at
  Level 3.
- If social/functional impact is only vaguely written as "impaired"/
  "declined" without concrete manifestation, ceiling at Level 4.
- Do not score high merely because of section headings or medical
  terminology.

### Scoring criteria

**Level 5 — Diagnostic support**
Clinical note has reached high-quality documentation level directly
usable for diagnostic criteria checking and differential diagnosis.
Chief complaint clear; HPI complete; onset, course, core symptoms,
severity, functional impact, risk, negative findings, and relevant
history all fully documented.  Structure is standardised; evidence chain
is clear; no significant redundancy or critical gaps.

**Level 4 — Chief-complaint convergence**
Clinical note has relatively complete information, can organise evidence
around the chief complaint and core clinical problems.  Shows clear
primary/secondary relationships, evidence synthesis, and problem-
convergence ability.  May still have some individual detail gaps.

**Level 3 — Evidence substantiation**
Clinical note not only has basic structure but begins to show clinical
evidence awareness.  Documents main symptoms, some course, mental status
exam, functional impact, and some negative/exclusion information.

**Level 2 — Structural coverage**
Clinical note has basic note structure covering multiple sections
(chief complaint, HPI, mental status exam, etc.).  Reader can broadly
understand the case.  However still mainly information aggregation, many
key clinical elements missing, limited diagnostic support.

**Level 1 — Minimal written form**
Clinical note barely possesses clinical documentation form, can present
a chief complaint or main clinical problem, but overall still very basic
— information scattered, lacking systematic structure and diagnostic
support value.
"""

# ---------------------------------------------------------------------------
# Diagnostic Rigor (Phase 4)
# ---------------------------------------------------------------------------

DIAGNOSTIC_RIGOR: str = """\
### Task definition
This scale evaluates the quality of diagnostic logical reasoning.  The
scale does not directly evaluate the accuracy of the final diagnostic
conclusion, but assesses whether the model can form a clear,
standardised, auditable diagnostic argument based on case information
and diagnostic criteria.

### Scoring restrictions
- Diagnostic codes, diagnosis names, or "core features" etc. vague
  formulations are not equivalent to concrete criteria content; if the
  model only uses such label-style formulations, ceiling at Level 2.
- If only mentioning standard names like ICD-11, DSM-5 without citing
  concrete criteria content, ceiling at Level 2.
- If most key judgements lack case evidence or criteria basis, proceed
  only by assertion, ceiling at Level 2.
- If differential diagnosis is only a one-sentence exclusion without
  criteria-level comparative analysis, ceiling at Level 3.
- Do not score high merely because of length, rich terminology, or
  formal "symptoms—criteria—differential—conclusion" structure.

### Scoring criteria

**Level 5 — Complete argument**
Forms a highly clear, rigorous, auditable diagnostic argument: uses
diagnostic criteria item by item to constrain case presentations; key
judgements all have case evidence or criteria basis; clearly
distinguishes necessary conditions, supporting evidence, limiting
information, and uncertainty; conducts substantive differential
diagnosis; finally forms a coherent, convergent diagnostic judgement.

**Level 4 — Criteria matching**
Conducts relatively systematic matching analysis around concrete
diagnostic criteria, mapping case information to multiple key criteria
items item by item, and distinguishing met conditions, supporting
evidence, insufficient information, and limiting evidence.  Argument
chain is basically auditable, but differential diagnosis or counter-
evidence handling may still be insufficient.

**Level 3 — Criteria reference**
Begins to cite concrete symptom items, necessary conditions, exclusion
conditions, course requirements, functional impairment requirements, or
other explicit judgement conditions from diagnostic criteria.  Reasoning
is no longer just "does it resemble" but begins to turn toward "does it
meet certain explicit criteria".  However criteria use is still
unsystematic.

**Level 2 — Surface mapping**
Can list several case presentations as diagnostic evidence, but overall
stays at the surface mapping level of "symptom presentation → diagnosis
name".  Argument does not cite concrete diagnostic criteria items, nor
distinguish necessary conditions, supporting conditions, and limiting
information.

**Level 1 — Argument missing**
Almost no identifiable diagnostic argument; output is mainly diagnosis
names, scattered impressions, or rough symptom correspondence — lacking
case evidence, diagnostic criteria, and reasoning chain.  The reader
cannot determine how the diagnostic judgement was reached.
"""

# ---------------------------------------------------------------------------
# Treatment Appropriateness (Phase 5)
# ---------------------------------------------------------------------------

TREATMENT_APPROPRIATENESS: str = """\
### Task definition
This scale evaluates the quality of a model-generated treatment plan.
Evaluation should combine the case's current diagnostic conclusion,
symptom severity, course stage, risk status, and patient individual
factors to judge whether the treatment plan can form a directionally
correct, structurally complete, individually tailored plan with
subsequent dynamic planning awareness.

### Scoring criteria

**Level 5 — Dynamic planning**
On top of individualised tailoring, further shows dynamic planning
ability for subsequent course and treatment response: not only explains
why the current choice was made, but can clearly propose adjustment,
substitution, escalation, or switching pathways under different
subsequent scenarios, forming an extensible, manageable treatment
decision framework.

---

**Level 4 — Individualised tailoring**
On top of plan completeness, can make clear tailoring decisions
combining patient individual factors, showing treatment decision-making
thinking of "what is recommended, what is avoided, and why".  Not only
knows "what treatments exist" but begins to know "for this patient, what
should be prioritised, what should not be used".

---

**Level 3 — Comprehensive plan**
Treatment plan already has basic completeness, can cover the main
intervention modules that should be considered for the current case, and
shows multi-dimensional treatment combination awareness.  Begins to form
a structured plan.  However overall still relatively generic — more like
"a relatively complete presentation of standard pathways" — not yet
clearly showing individualised tailoring and treatment priority
decision-making.

---

**Level 2 — Coarse-grained suggestions**
Treatment direction is broadly consistent with the current case, and can
propose several relevant suggestions around the main diagnosis or
symptom direction.  However overall still at the level of coarse-
grained, single-point, or low-organisation suggestions — not yet forming
a structured, executable treatment plan.

---

**Level 1 — Directional mismatch**
The treatment plan is inconsistent with the current diagnostic
conclusion, symptom severity, course stage, or risk status, therefore
lacks basic clinical acceptability.  Recommendations may superficially
"look like treatment" but do not genuinely respond to the case's main
treatment needs, or show clear mismatch in intervention intensity,
treatment direction, and clinical priorities.
"""
