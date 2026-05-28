/**
 * Frontend shared constants
 *
 * Centralized management of ICD-11 classifications, label mappings,
 * and localization utilities, shared by phase3-diagnosis / phase4-treatment /
 * unified-evaluation and other components.
 */

/* ── ICD-11 Diagnostic Categories and Codes ── */
const ICD11_CATEGORY_OPTIONS = Object.freeze({
    "Neurodevelopmental disorders": [
        "6A00 Intellectual developmental disorders",
        "6A01 Developmental speech or language disorders",
        "6A02 Autism spectrum disorder",
        "6A03 Developmental learning disorders",
        "6A04 Developmental motor coordination disorders",
        "6A05 Attention deficit hyperactivity disorder",
        "6A06 Stereotyped movement disorders",
    ],
    "Schizophrenia or other primary psychotic disorders": [
        "6A20 Schizophrenia",
        "6A21 Schizoaffective disorders",
        "6A22 Schizotypal disorders",
        "6A23 Acute and transient psychotic disorders",
        "6A24 Delusional disorders",
    ],
    "Catatonia": [
        "6A40 Catatonia associated with another mental disorder",
        "6A41 Catatonia induced by substances or medications",
    ],
    "Mood disorders": [
        "6A60 Bipolar type I disorder",
        "6A61 Bipolar type II disorder",
        "6A62 Cyclothymic disorder",
        "6A70 Single episode depressive disorder",
        "6A71 Recurrent depressive disorder",
        "6A72 Dysthymic disorder",
        "6A73 Mixed depressive and anxiety disorder",
    ],
    "Anxiety or fear-related disorders": [
        "6B00 Generalized anxiety disorder",
        "6B01 Panic disorder",
        "6B02 Agoraphobia",
        "6B03 Specific phobias",
        "6B04 Social anxiety disorder",
        "6B05 Separation anxiety disorder",
        "6B06 Selective mutism",
    ],
    "Obsessive-compulsive or related disorders": [
        "6B20 Obsessive-compulsive disorder",
        "6B21 Body dysmorphic disorder",
        "6B22 Olfactory reference disorder",
        "6B23 Hypochondriasis",
        "6B24 Hoarding disorder",
        "6B25 Body-focused repetitive behaviour disorders",
    ],
    "Disorders specifically associated with stress": [
        "6B40 Post-traumatic stress disorder",
        "6B41 Complex post-traumatic stress disorder",
        "6B42 Prolonged grief disorder",
        "6B43 Adjustment disorders",
        "6B44 Reactive attachment disorder",
        "6B45 Disinhibited social engagement disorder",
    ],
    "Dissociative disorders": [
        "6B60 Dissociative neurological symptom disorder",
        "6B61 Dissociative amnesia",
        "6B62 Trance disorder",
        "6B63 Possession trance disorder",
        "6B64 Dissociative identity disorder",
        "6B65 Partial dissociative identity disorder",
        "6B66 Depersonalization-derealization disorder",
    ],
    "Feeding or eating disorders": [
        "6B80 Anorexia nervosa",
        "6B81 Bulimia nervosa",
        "6B82 Binge eating disorder",
        "6B83 Avoidant/restrictive food intake disorder",
        "6B84 Pica",
        "6B85 Rumination-regurgitation disorder",
    ],
    "Elimination disorders": [
        "6C00 Enuresis",
        "6C01 Encopresis",
    ],
    "Disorders of bodily distress or bodily experience": [
        "6C20 Bodily distress disorder",
        "6C21 Body integrity dysphoria",
    ],
    "Disorders due to substance use or addictive behaviours": [
        "6C40 Disorders due to use of alcohol",
        "6C41 Disorders due to use of cannabis",
        "6C42 Disorders due to use of synthetic cannabinoids",
        "6C43 Disorders due to use of opioids",
        "6C44 Disorders due to use of sedatives, hypnotics or anxiolytics",
        "6C45 Disorders due to use of cocaine",
        "6C46 Disorders due to use of stimulants",
        "6C47 Disorders due to use of synthetic cathinones",
        "6C48 Disorders due to use of caffeine",
        "6C49 Disorders due to use of hallucinogens",
        "6C4A Disorders due to use of nicotine",
        "6C4C Disorders due to use of MDMA or related substances",
        "6C4D Disorders due to use of dissociative drugs",
        "6C4E Disorders due to use of other specified psychoactive substances",
        "6C4F Disorders due to use of multiple specified psychoactive substances",
        "6C4G Disorders due to use of unknown or unspecified psychoactive substances",
        "6C4H Disorders due to use of non-psychoactive substances",
        "6C50 Gambling disorder",
        "6C51 Gaming disorder",
    ],
    "Impulse control disorders": [
        "6C70 Pyromania",
        "6C71 Kleptomania",
        "6C72 Compulsive sexual behaviour disorder",
    ],
    "Disruptive behaviour or dissocial disorders": [
        "6C90 Oppositional defiant disorder",
        "6C91 Conduct-dissocial disorder",
    ],
    "Personality disorders and related traits": [
        "6D10 Personality disorders",
    ],
    "Paraphilic disorders": [
        "6D30 Exhibitionistic disorder",
        "6D31 Voyeuristic disorder",
        "6D32 Paedophilic disorder",
        "6D33 Coercive sexual sadism disorder",
        "6D34 Frotteuristic disorder",
        "6D35 Other paraphilic disorders involving non-consenting individuals",
        "6D36 Paraphilic disorders involving solitary behaviour or consenting individuals",
    ],
    "Neurocognitive disorders": [
        "6D70 Delirium",
        "6D71 Mild neurocognitive disorders",
        "6D72 Amnestic disorder",
        "6D80 Dementia due to Alzheimer disease",
        "6D81 Dementia due to cerebrovascular disease",
        "6D82 Dementia due to Lewy body disease",
        "6D83 Frontotemporal dementia",
        "6D84 Dementia due to psychoactive substances or medications",
        "6D85 Dementia due to other specified diseases",
        "6D86 Behavioural or psychological symptoms in dementia",
    ],
    "Mental or behavioural disorders associated with pregnancy, childbirth or the puerperium": [
        "6E20 Mental or behavioural disorders associated with pregnancy, childbirth or the puerperium, without psychotic symptoms",
        "6E21 Mental or behavioural disorders associated with pregnancy, childbirth or the puerperium, with psychotic symptoms",
    ],
    "Factitious disorders": [
        "6D50 Factitious disorder imposed on self",
        "6D51 Factitious disorder imposed on another",
    ],
});

/* ── ICD-11 Category Labels (Phase 3 Diagnosis) ── */
const CATEGORY_LABELS = Object.freeze({
    "Neurodevelopmental disorders": "Neurodevelopmental Disorders",
    "Schizophrenia or other primary psychotic disorders": "Schizophrenia or Other Primary Psychotic Disorders",
    "Catatonia": "Catatonia",
    "Mood disorders": "Mood Disorders",
    "Anxiety or fear-related disorders": "Anxiety or Fear-Related Disorders",
    "Obsessive-compulsive or related disorders": "Obsessive-Compulsive or Related Disorders",
    "Disorders specifically associated with stress": "Disorders Specifically Associated with Stress",
    "Dissociative disorders": "Dissociative Disorders",
    "Feeding or eating disorders": "Feeding or Eating Disorders",
    "Elimination disorders": "Elimination Disorders",
    "Disorders of bodily distress or bodily experience": "Disorders of Bodily Distress or Bodily Experience",
    "Disorders due to substance use or addictive behaviours": "Disorders Due to Substance Use or Addictive Behaviours",
    "Impulse control disorders": "Impulse Control Disorders",
    "Disruptive behaviour or dissocial disorders": "Disruptive Behaviour or Dissocial Disorders",
    "Personality disorders and related traits": "Personality Disorders and Related Traits",
    "Paraphilic disorders": "Paraphilic Disorders",
    "Neurocognitive disorders": "Neurocognitive Disorders",
    "Mental or behavioural disorders associated with pregnancy, childbirth or the puerperium": "Mental or Behavioural Disorders Associated with Pregnancy, Childbirth or the Puerperium",
    "Factitious disorders": "Factitious Disorders",
});

/* ── ICD-11 Diagnosis Category Labels (Unified Evaluation) ── */
const DIAGNOSIS_CATEGORY_LABELS = Object.freeze({
    'Neurodevelopmental disorders': 'Neurodevelopmental Disorders',
    'Schizophrenia or other primary psychotic disorders': 'Schizophrenia or Other Primary Psychotic Disorders',
    'Catatonia': 'Catatonia',
    'Mood disorders': 'Mood Disorders',
    'Depressive disorders': 'Depressive Disorders',
    'Bipolar or related disorders': 'Bipolar or Related Disorders',
    'Anxiety or fear-related disorders': 'Anxiety or Fear-Related Disorders',
    'Obsessive-compulsive or related disorders': 'Obsessive-Compulsive or Related Disorders',
    'Disorders specifically associated with stress': 'Disorders Specifically Associated with Stress',
    'Feeding or eating disorders': 'Feeding or Eating Disorders',
    'Personality disorders and related traits': 'Personality Disorders and Related Traits',
});

/* ── ICD-11 Localization Utility ── */
const ICD11Localization = (() => {
    const codeLabelMap = {};
    const splitPattern = /[|,，;；、]+/;

    Object.values(ICD11_CATEGORY_OPTIONS).forEach((items) => {
        items.forEach((item) => {
            const match = String(item).match(/^([0-9A-Z]+)\s+(.+)$/);
            if (match) {
                codeLabelMap[match[1]] = item;
            }
        });
    });

    const localizeCategory = (category) => CATEGORY_LABELS[category] || category || '';

    const localizeDisease = (disease) => {
        const text = String(disease || '').trim();
        if (!text) return '';
        const match = text.match(/^([0-9A-Z]+)\b/);
        if (match && codeLabelMap[match[1]]) {
            return codeLabelMap[match[1]];
        }
        return text;
    };

    const localizeDiseaseText = (value) => {
        const text = String(value || '').trim();
        if (!text) return '';
        return text
            .split(splitPattern)
            .map((item) => localizeDisease(item))
            .filter(Boolean)
            .join(' | ');
    };

    return {
        localizeCategory,
        localizeDisease,
        localizeDiseaseText,
    };
})();

window.ICD11Localization = ICD11Localization;
