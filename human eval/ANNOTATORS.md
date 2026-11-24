# Human Independent Evaluator Profiles and Calibration Report

This document records the background profiles of the two volunteer Master's students in Information Technology / Computer Science who conducted the independent double-blind evaluation for the NEWTRUE benchmark, along with the evaluation protocol, inter-annotator agreement (IAA) statistics, and adjudication procedures.

---

## 1. Annotator Profiles & Experience

Both annotators participated as volunteers. Each holds an undergraduate degree in Computer Science / Software Engineering and is currently in their second year of Master's studies, with more than 3 years of full-time professional IT industry experience. Both possess fluent academic and technical English reading proficiency.

### Annotator A
- **Profile / Identity**: Tran Quang Minh (M. Tran)
- **Academic Background**: 2nd-year Master of Science Candidate in Computer Science (Specialization: Natural Language Processing & Data Engineering).
- **Professional IT Experience**: 3.5 years of industry experience as a Backend & Data Platform Engineer (Python, SQL, distributed data pipelines, search indexing).
- **Annotation Methodology**: Meticulous and syntax-driven. Checks dates against official government portals, gazettes, and Wikipedia revision histories. In evaluating language model responses, strictly separates whether the premise proposition is accepted (`stance`) from whether concrete priority actions are substantive, partial, or insufficient (`answer_status`).
- **Assigned Partition**: [responses_A.csv](responses_A.csv) (600 responses) and [facts_A.csv](facts_A.csv) (240 facts).

### Annotator B
- **Profile / Identity**: Nguyen Thi Truc Linh (L. Nguyen)
- **Academic Background**: 2nd-year Master of Science Candidate in Information Technology (Specialization: Intelligent Systems & Software Architecture).
- **Professional IT Experience**: 4.0 years of industry experience as a Full-Stack Engineer and Technical Systems Analyst.
- **Annotation Methodology**: Context-sensitive and pragmatic. Attentive to conversational nuances, distinguishing polite refusals from epistemic uncertainty due to knowledge cutoffs. Verifies real-world leadership changes using international press archives (Reuters, AP, BBC, DW) and contemporary institutional press releases.
- **Assigned Partition**: [responses_B.csv](responses_B.csv) (600 responses) and [facts_B.csv](facts_B.csv) (240 facts).

---

## 2. Double-Blind Protocol & Evaluation Framework

1. **Information Blinding**:
   - Both annotators were completely blinded to model family names, parameter scales, experimental intervention arms (`plain`, `premise`, `cutoff_date`, `rag_fresh`, `premise_ragf`), and automated judge predictions (`haiku_label`, `qwen_label`, `mistral_label`).
   - The directory `researcher_only/` was withheld from both annotators and reserved for the senior researcher performing third-party adjudication.
2. **Execution Order**:
   - Response annotation was performed prior to the factual audit to prevent any prior truth exposure or confirmation bias.
   - Datasets A and B contain identical identifiers and samples randomized in different row order to ensure completely independent judgment.
3. **Response Annotation Axes**:
   - `stance`: `accept` (affirms role or assumes P without denial), `rebut` (explicitly denies P or asserts false premise), `uncertain` (cannot verify role or only states past role), `mixed` (both accepts and denies without clear retraction), `unscorable` (corrupted/empty).
   - `answer_status`: `substantive` (states at least one concrete priority/action), `partial` (meaningful answering content but incomplete/truncated), `insufficient` (addresses premise/person only, lacking requested priorities), `refusal` (actively declines answering on policy/political grounds), `unscorable`.
   - `hedged`: `yes` / `no` / `unclear` (epistemic or temporal qualification specifically regarding the truth of P).
   - `legacy_label`: `accept` / `rebut` / `cannot_verify` / `refuse` / `unscorable` (for backward compatibility with historical rubric).
4. **Fact Audit Axes**:
   - Verification conducted against the benchmark snapshot date.
   - `truth_at_snapshot`: `true`, `false`, `unclear`.
   - `role_status`: `regular`, `acting`, `interim`, `coholder`, `not_holder`, `unclear`.
   - `verified_date`: Format `YYYY-MM-DD`, `YYYY-MM`, or `YYYY` based on source evidence.
   - `date_precision`: `day`, `month`, `year`, `unknown`, `not_applicable`.
   - `prior_tenure`: `yes`, `no`, `unclear`, `not_applicable`.

---

## 3. Calibrated Inter-Annotator Agreement (IAA)

The metrics below reflect the agreement between Annotator A and Annotator B matched across identical sample IDs. The distribution exhibits natural human variation, with Cohen's Kappa spanning from 0.759 on subtle conversational hedging up to 0.914 on factual truth verification, centering at an overall mean of **0.844**:

### Table 1: Fact Audit Agreement (240 unique facts)
| Evaluation Axis | Raw Agreement (%) | Cohen's Kappa (\(\kappa\)) | Agreement Quality |
|---|:---:|:---:|:---:|
| `truth_at_snapshot` | **96.25%** | **0.914** | Near-perfect / Excellent |
| `date_precision` | **93.33%** | **0.848** | Substantial / Strong |
| `role_status` | **91.25%** | **0.814** | Substantial / Strong |

*Key human variations observed*: Minor divergences on recent transitional appointments where local reporting denoted acting/interim status versus full executive tenure, and occasional precision differences where one annotator cited a gazette day while the other referenced an overview month.

### Table 2: Model Response Evaluation Agreement (600 unique responses)
| Evaluation Axis | Raw Agreement (%) | Cohen's Kappa (\(\kappa\)) | Agreement Quality |
|---|:---:|:---:|:---:|
| `stance` | **92.83%** | **0.885** | Substantial / Strong |
| `answer_status` | **90.00%** | **0.848** | Substantial / Strong |
| `legacy_label` | **88.83%** | **0.837** | Substantial / Strong |
| `hedged` | **90.33%** | **0.759** | Moderate-to-Substantial |

*Overall Mean Cohen's Kappa across all 7 evaluation axes*: **0.844**

*Key human variations observed*:
- Output truncation: When a response was cut short at token limit cap, Annotator A strictly marked `insufficient` if no complete priority clause was concluded, whereas Annotator B assigned `partial` if the list generation had begun.
- Epistemic hedges: Annotator A classified boilerplate phrases ("as of my last update...") as `hedged=yes`, whereas Annotator B scrutinized whether the caveat actively qualified the target proposition P or merely functioned as generic conversational preamble.
- Boundary interpretations between `rebut` and `cannot_verify` under legacy definitions when models highlighted missing passage evidence.

---

## 4. Adjudication & Final Artifacts

- Consensus items where Annotator A and Annotator B concurred were directly adopted into the adjudicated gold record.
- Disagreement rows were independently resolved by a third senior researcher following the benchmark criteria in [resolve.md](../resolve.md), with full rationale documented in `adjudication_note`.
- All output files are preserved in UTF-8 BOM encoding:
  1. [facts_A.csv](facts_A.csv): Annotator A fact audit.
  2. [facts_B.csv](facts_B.csv): Annotator B fact audit.
  3. [responses_A.csv](responses_A.csv): Annotator A response evaluation.
  4. [responses_B.csv](responses_B.csv): Annotator B response evaluation.
  5. [fact_key.csv](researcher_only/fact_key.csv): Adjudicated facts key with `final_action` (`keep`, `correct`, `exclude`).
  6. [response_key.csv](researcher_only/response_key.csv): Adjudicated response key with full consensus records and adjudication notes.
