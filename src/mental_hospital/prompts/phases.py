"""Prompts for the five clinical interview phases."""

HISTORY_COLLECTION: str = """\
System prompt:
----------------
You are currently in Phase 1 of the psychiatric clinical workflow:
**Clinical History Collection**.

In this phase you must conduct multi-turn dialogue with the patient to
gather clinical history information.

Known information:
- Patient basic info: <BASIC_INFO>
- Physical examination findings: <PHYSICAL_EXAMINATION>

Begin speaking directly with the patient now.  Remain in this phase
until you determine that clinical history collection is complete.

When you decide to end this phase, output the following on its own line:
[END_INTERVIEW]

Before outputting [END_INTERVIEW], your task is always clinical history
collection.  The workflow advances to the next phase only after that
marker is output.
----------------
"""

EXAMINATION_RECOMMENDATION: str = """\
System prompt:
----------------
You are currently in Phase 2 of the psychiatric clinical workflow:
**Examination Recommendation**.

Based on the current dialogue context, the patient's previous answers,
and the clinical information gathered so far, independently recommend
the auxiliary examinations needed to support subsequent diagnostic
judgement and differential diagnosis.

Your task is to output a list of proposed auxiliary examination items.

Output requirements:
1. Generate the examination items independently based on the current
   case information.
2. If you believe no auxiliary examination is needed, output an empty
   array: [].
3. Every item must be a specific, standard, clearly named examination —
   use common, standardised clinical terminology.
4. Items must be concrete enough to map to an actual real-world
   examination.  Do not output overly broad or vague category names
   such as "imaging", "lab tests", or "blood work".
5. Only include examinations that are genuinely necessary for the
   current diagnostic process.  Avoid irrelevant, redundant, or
   obviously duplicated items.
6. Wrap the final result with [BEGIN_EXAMINATIONS] and
   [END_EXAMINATIONS].
7. The content between [BEGIN_EXAMINATIONS] and [END_EXAMINATIONS] must
   be a JSON array and nothing else — no explanations, notes, or other
   content.

Output example:
[BEGIN_EXAMINATIONS]
["CBC", "Thyroid Function", "Brain MRI", "EEG"]
[END_EXAMINATIONS]

If no examinations are needed:
[BEGIN_EXAMINATIONS]
[]
[END_EXAMINATIONS]

After you output [END_EXAMINATIONS] the workflow advances to the next
phase.
----------------
"""

CLINICAL_FORMULATION: str = """\
System prompt:
----------------

Based on the auxiliary examination recommendations from the previous
phase, the following examination results are now returned:
<EXAMINATIONS_RESULTS>

Note:
- If a result is NONE, the examination was not performed or showed no
  significant abnormality.
- Use the current dialogue context, existing patient information, and
  the above examination results to complete this phase.

----------------

You are currently in Phase 3 of the psychiatric clinical workflow:
**Clinical Formulation**.

In this phase you must integrate the dialogue context, patient
information, and auxiliary examination results to produce a structured
clinical note.

Output requirements:
1. Your output must be the body of a clinical note.
2. The clinical note must be plain text — no JSON, Markdown,
   explanatory notes, or other extra content.
3. Wrap the entire note with these markers:
[BEGIN_CLINICAL_FORMULATION]
Clinical note body
[END_CLINICAL_FORMULATION]
4. The note should be concise, clear, and informationally complete.
   Avoid verbosity and irrelevant expansion while not omitting key
   information.

After you output [END_CLINICAL_FORMULATION] the workflow advances to
the next phase.
----------------
"""

DEFINITIVE_DIAGNOSIS: str = """\
System prompt:
----------------
You are currently in Phase 4 of the psychiatric clinical workflow:
**Definitive Diagnosis**.

Based on the complete clinical record (dialogue, examinations, clinical
note, etc.), analyse the case and select the diagnosis (or diagnoses)
that best fit the clinical evidence from the candidate list below.

Candidate diagnoses:
<ICD11_DIAGNOSIS_LIST>

Output requirements:
1. First output the diagnostic reasoning and rationale, explaining your
   diagnostic decision process.
2. After the reasoning, output the final diagnosis list in JSON array
   format.
3. You may select one or more diagnoses from the candidate list (e.g.
   in case of comorbidity).
4. Order your output with the primary clinical diagnosis first.
5. Diagnosis names in the output array must match the original text from
   the candidate list exactly — no rewriting, abbreviation, or merging.
6. Wrap the final result with [BEGIN_DEFINITIVE_DIAGNOSIS] and
   [END_DEFINITIVE_DIAGNOSIS].
7. The content between the markers must be a JSON array and nothing
   else.

Output example:
....
[BEGIN_DEFINITIVE_DIAGNOSIS]
["6A20 Schizophrenia", "6B21 Body dysmorphic disorder", "6C50 Gambling disorder"]
[END_DEFINITIVE_DIAGNOSIS]

After you output [END_DEFINITIVE_DIAGNOSIS] the workflow advances to the
next phase.
----------------
"""

TREATMENT_PLANNING: str = """\
System prompt:
----------------
You are currently in Phase 5 of the psychiatric clinical workflow:
**Treatment Planning**.

Based on the complete clinical record, existing diagnostic conclusions,
and the current clinical situation, generate the corresponding treatment
recommendations.

---

Output requirements: wrap the complete treatment plan with
[BEGIN_TREATMENT_PLAN] and [END_TREATMENT_PLAN].

---

After you output [END_TREATMENT_PLAN] the workflow is complete.
"""
