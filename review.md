# NEWTRUE: Four ACL Reviews and Meta-Review

**Paper:** *Newly-True Presuppositions: How Small Open Language Models Treat Facts That Changed After Their Training Data*
**Target:** ACL long paper, with Findings considered separately
**Review date:** 20 November 2026
**Version reviewed:** Current `manuscript/main.tex`, its included sections/tables, and the 19-page `manuscript/main.pdf`; benchmark snapshot 10 November 2026.
**PDF SHA-256:** `f6c53cb300753b2a1b61735177bb2b558a45de3d695979a7a43a56db74d6589e`

These are four simulated reviewer perspectives generated for author feedback, followed by a simulated area-chair assessment. They are not four independently recruited human reviews or an actual ACL decision. The assessment may contain errors. It uses the current manuscript, selected artifact documentation and analysis code, stored statistics, and a targeted primary-source literature check. Model inference, annotation, and the complete reproduction pipeline were not rerun for this review. Earlier internal review scores are not used as evidence for the recommendations below.

## Executive assessment

NEWTRUE identifies a useful evaluation problem: a model may challenge a correct premise because the relevant fact changed after its release. Its strongest contribution is a controlled comparison between a newly true role-holder premise and two false alternatives with the same entity, role, and wording. The manuscript is clear, unusually candid about its limitations, and supported by substantial sensitivity analysis. It does not claim to invent the observation that premise checking can harm valid questions, and it distinguishes fewer false rebuttals from better discrimination.

The main publication risk is measurement validity. The benchmark has only 35 matched entities, the supposedly unfamiliar false controls are often visibly implausible, and all response labels are automatic. These weaknesses matter because most measured rebuttals are hedged, some responses contest answerability rather than the role-holder premise, and the largest oracle-plus-instruction effect is sensitive to the judge. Statistical uncertainty and model-family concentration further limit generalization. These issues do not erase the descriptive findings, but they leave the resource and intervention conclusions less secure than their extensive presentation might suggest.

**Simulated meta-review decision: reject in the current form and revise for the next ARR cycle; overall assessment 2/5.** The paper is close enough to Findings that a sympathetic reviewer could recommend acceptance, but an area chair should resolve the construct and benchmark-validity concerns before treating it as a dependable evaluation resource. A new model architecture or a sweeping theory is not required.

## Scoring convention and reviewer overview

Scores use the current [ARR review form](https://aclrollingreview.org/reviewform): soundness, excitement, overall assessment, and confidence are distinct. Relevant overall recommendations are **2 = Resubmit next cycle**, **2.5 = Borderline Findings**, **3 = Findings**, **3.5 = Borderline Conference**, and **4 = Conference**. Overall scores are judgments, not averages of component ratings. This packet uses the current ARR rubric rather than asserting unverified ACL 2027-specific policies.

| Perspective | Soundness /5 | Excitement /5 | Overall /5 | Confidence /5 | Recommendation |
| --- | ---: | ---: | ---: | ---: | --- |
| R1: Presupposition semantics and measurement | 2.5 | 3.5 | 2.5 | 4 | Borderline Findings |
| R2: Experimental design and statistical inference | 2 | 3 | 2 | 4 | Resubmit next cycle |
| R3: Temporal QA, baselines, and reproducibility | 2.5 | 3 | 2.5 | 3 | Borderline Findings |
| R4: Empirical contribution and practical value | 3 | 3.5 | 3 | 3 | Findings |
| **Meta-review** | — | — | **2** | **4** | **Revise and resubmit** |

The following additional diagnostic dimensions are author-feedback scores, not extra official ARR fields. Here 1 denotes very weak support/quality and 5 denotes excellent support/quality.

| Dimension | R1 | R2 | R3 | R4 |
| --- | ---: | ---: | ---: | ---: |
| Originality | 3 | 3 | 2.5 | 3.5 |
| Importance | 4 | 3.5 | 3.5 | 4 |
| Claim support | 2.5 | 2 | 2.5 | 3 |
| Experimental soundness | 2.5 | 2 | 2.5 | 3 |
| Writing clarity | 4 | 4 | 4 | 4 |
| Community value | 3.5 | 3 | 3.5 | 4 |
| Prior-work contextualization | 3.5 | 3.5 | 3 | 3.5 |

## Contribution and evidence map

Percentages below are reported rates, not independent reproductions. Percentage-point differences are abbreviated pp. Table and section references refer to the reviewed PDF.

| Claim or contribution | Evidence | Assessment and boundary |
| --- | --- | --- |
| Newly true premises attract more rebuttals than long-standing truths | Main grid: 29% versus 8%; direction positive in all seven models. Present-tense T2 subset: 29% versus 15%, with 24 and 13 items and model-level p = .19. §5, Table 2. | Useful descriptive evidence. Different entities and uneven templates prevent a clean causal estimate of the effect of recency. The T2 result is less precise, not proof that the effect disappears. |
| Models separate true and false premises only modestly | 35 triples: NEW/FORMER/SWAP rebuttal rates 30/41/40%; margins +11 [1,23] and +10 [2,22] pp. §5, Table 1. | Matched entity/role/wording is a real advance. Person familiarity and plausibility remain uncontrolled; the margins describe this sample. |
| Premise-check effects depend on wording | Author instruction: 62/75/75%; FreshQA instruction: 29/44/49%. §5, Table 1. | Strong reason to avoid treating premise checking as one intervention. Evidence does not identify which linguistic difference causes the effect. The author-instruction rise in NEW rebuttals has model-level p = .15. |
| Cutoff reminders reduce false rebuttals chiefly through deferral | NEW rebuttals fall from 30% to 11%; deferrals rise from 42% to 64%, including political refusals. §5. | Supported within the labeling scheme. Deferral aggregates several qualitatively different behaviors; it is not a measured improvement in answer utility. |
| Current evidence improves premise handling | Oracle NEW rebuttal rate 0%, but acceptance only 49%; RAG-mixed NEW rebuttals 4%. §5, Table 1. | Controlled evidence-use result, not an end-to-end retrieval result or a universal zero-error guarantee. |
| Premise checking can elicit rebuttals even with confirming evidence | RAG-fresh+PC: primary-judge NEW rate 39%; held-out judges 27–28%; four knowledgeable models 21% with primary judge and 17–20% with held-out judges. §§5–6, Tables 6–7. | Qualitative effect survives; its magnitude and interpretation need adjudication. Of 96 primary-judge rebuttals, 85 come from the three smallest Qwen models. |
| Larger models do not uniformly solve the problem | Three separately reported 14–32B models: triple rates 53/72/71%, margins +19/+18 pp. §5, Table 8. | Useful extension beyond the pooled small models. Three models from two families do not establish a scaling law. |
| Old role knowledge explains false correction | Entity popularity predicts rebuttal, but the predecessor-belief analysis finds 30% versus 29% rebuttal and no positive adjusted association. §6, Appendix E. | Mechanism remains unestablished, as the limitations correctly state. A population-level pattern is not evidence of stored predecessor knowledge on each trial. |
| A reusable benchmark and artifact | Frozen item IDs, raw outputs, labels, scripts, provenance, and documented regeneration. Appendices A–C; `artifact/`. | Promising resource. Independent item/response validation and a consolidated current reproduction entry point remain important. |

## Review 1: Presupposition semantics and measurement

**Overall: 2.5/5 — Borderline Findings. Soundness: 2.5/5. Excitement: 3.5/5. Confidence: 4/5.**

### Summary

The paper examines how small open models respond when a question assumes a true role-holder fact that became true after the model's release. It compares current, former, and swapped holders within 35 matched triples and evaluates eleven prompt/evidence conditions. The central observation is that false corrections of true premises remain common, and that interventions change both the willingness to rebut and the ability to distinguish true from false premises. I find this intersection of temporal knowledge and presupposition handling worthwhile. My reservation concerns whether the response taxonomy consistently measures the intended semantic behavior.

### Strengths

1. **The target behavior is meaningful.** Answering a direct factual question incorrectly and correcting a user who supplied a true premise are different conversational failures. The introduction makes the latter easy to understand without relying on a fabricated example.
2. **The matched design is substantially better than a true/false aggregate alone.** Fixing the entity, role phrase, and question template removes several obvious sources of variation. Reporting both false-minus-true margins also avoids presenting indiscriminate acceptance as success.
3. **The treatment of hedging is candid.** Section 6 reports that 82% of NEW rebuttals contain a cutoff hedge and that only 5% of NEW responses contain an unhedged rebuttal. The paper explicitly refrains from equating these rates with measured user harm.
4. **The authors examine contradictory evidence.** Judge sensitivity, prompt sensitivity, the null predecessor-belief result, and the weak inferential support are disclosed. This makes the work easier to assess and potentially more useful than a cleaner but overstated narrative.

### Major weaknesses

**R1-W1. Premise stance and answerability are not sufficiently separated.** The question asks for a person's priorities, whereas the oracle establishes only that the person holds a role. A response can correctly accept that role and still lack evidence about the priorities. The paper acknowledges that the deferral category includes answers that accept the premise but lack details. Conversely, under RAG-fresh+PC, some answers announce a false premise and then confirm the role while objecting that priorities were not supplied. Counting the entire response as one of accept/rebut/cannot-verify can conflate premise stance, discourse inconsistency, and ability to answer the requested question. This directly affects the interpretation of the 51% oracle deferral rate and the 39% oracle-plus-check rebuttal rate (§§5–6).

**R1-W2. Agreement between model judges does not establish the intended interpretation.** The held-out cross-family validation is valuable, especially the high agreement on the initial three conditions. Nevertheless, all judges receive the same operational instructions. They can agree on a definition that readers would not apply to a dated historical statement. The lower agreement under RAG-fresh+PC is particularly consequential: the primary-judge rate is 39%, versus 27–28% under the held-out judges. The missing evidence is not simply another automatic judge; it is a blind, adjudicated human analysis of these boundary cases.

**R1-W3. The formalization begins with an ambiguous temporal presupposition.** Section 3.1 introduces “since becoming CEO” and formalizes it as holding the role at the snapshot. Becoming a CEO in the past does not imply still being CEO. The authors acknowledge this for the main-grid false groups and use explicitly current T2 wording in the main test, so this is not a fatal flaw in the triples. However, the formal definition and headline main-grid comparison should make that distinction immediately. The first example in the method could use the unambiguous main-test template.

**R1-W4. The pending human protocol needs revision before execution.** Appendix D retains “150 items, 30 per condition,” although the final benchmark has more than five item groups and eleven interventions. It also proposes a three-way label scheme while the automatic annotation begins with four classes, and refers to disagreement between “two” judges without identifying the final pair. Oversampling disagreement cases is sensible for diagnosis, but headline prevalence estimates require sampling weights or a separately representative subset. These are design details that influence the eventual evidence, not merely editorial errors.

### Questions for the authors

1. Among responses that repeat the correct role-holder fact but decline to state priorities, how often do humans label the premise as accepted?
2. How many RAG-fresh+PC rebuttals actually deny the named role-holder proposition, rather than only use a false-premise opening or complain about missing answer evidence?
3. Would conclusions survive a two-axis annotation: premise stance on one axis, answer sufficiency/refusal on the other, with hedging and internal contradiction marked separately?
4. Can the paper report both a strict explicit-denial metric and the broader hedged-correction metric, with manually validated examples and error estimates?

### Recommendation

I am borderline because the topic and controlled comparison are publishable, but the annotation construct is central to the contribution. The requested validation is targeted: adjudicate a representative response sample and deliberately include the ambiguous oracle-plus-check cases. A full user-impact study is unnecessary if the paper continues to avoid harm claims. Clear, stable results under a validated taxonomy would likely move my recommendation to Findings. More stylistic polishing alone would not change it.

## Review 2: Experimental design and statistical inference

**Overall: 2/5 — Resubmit next cycle. Soundness: 2/5. Excitement: 3/5. Confidence: 4/5.**

### Summary

This is an empirical study of premise handling across temporal truth categories. Its principal experiment comprises 35 entity triples evaluated by seven models. The authors report paired margins, two-level bootstrap intervals, model-level tests, multiplicity adjustments, and several sensitivity analyses. I appreciate this effort. My concern is that the nominal controls and inferential units do not support some of the broader interpretations of a controlled newly-true benchmark.

### Strengths

1. **The statistics are considerably more careful than simple response-level testing.** The paper preserves paired comparisons, resamples entities and models, and does not treat thousands of generations as thousands of independent models.
2. **The limits of significance are visible.** Table 1 explicitly states that none of its 22 margin tests survives Holm correction. The abstract calls the discrimination evidence suggestive.
3. **Sensitivity analyses are relevant.** The 256-token Plain rerun, model-wise rates, judge alternatives, T2-only subset, and popularity adjustment address concrete threats. The larger-model comparison is reported separately and does not claim monotonic scaling.
4. **The resource provides a manageable experimental unit.** Entity triples are interpretable, and a future stronger design can build directly on them rather than replacing the entire study.

### Major weaknesses

**R2-W1. SWAP does not isolate unfamiliarity from plausibility.** Only four swaps meet the paper's citizenship compatibility proxy. The swapped person's popularity correlates with rebuttal rate at rho = .61, and 12 of 35 swapped people are more popular than their NEW counterparts. On the 23-triple subset with no greater swapped-person popularity, the margin is +7 pp with interval [−2,19]. The fixed-effects adjustment retains a positive margin, but it controls a noisy popularity proxy, not country, occupational plausibility, name recognition, or actual model familiarity. This does not invalidate the measured SWAP error rate. It prevents interpreting that rate as a clean unfamiliar-false comparison. Moreover, shared citizenship is only a rough screening variable: cross-country appointments can be real, and same-country substitutions can remain implausible.

**R2-W2. The main NEW-versus-OLD comparison remains unmatched.** The 29% versus 8% headline compares different role/entity distributions and assigned templates. Restricting to T2 gives 29% versus 15% with small groups. The matched triples improve true-versus-false comparison but do not match recently true and long-true premises within a comparable sampling design. Consequently, they cannot independently establish that recency, rather than correlated entity/person characteristics, causes the higher rate. The paper largely respects this distinction, but the introductory claim about stored answers still encourages a stronger explanation than the evidence establishes.

**R2-W3. Seven checkpoints are not seven independent draws from a population of model families.** Four pooled models are Qwen2.5 variants. The bootstrap and model-level tests operate over checkpoints; they do not make the selected panel representative or eliminate shared-training dependence. A useful revision would define the estimand explicitly: performance averaged over these seven checkpoints and these entities, with family-balanced and leave-one-family-out sensitivity summaries. With four developers, elaborate asymptotic family-cluster inference may itself be unreliable. I would prefer transparent descriptive sensitivity to an unjustified claim that a different test solves the dependence problem.

**R2-W4. The intervention ranking is not securely established.** FreshQA's SWAP-margin change is +10 pp, but its two-level bootstrap interval is [−2,22], while the per-model t-test gives p = .01. These methods reflect different uncertainty components and assumptions. The paper should explain the discrepancy rather than let one favorable number carry the conclusion. The 22 corrected tests concern margins within conditions; superiority over Plain is a separate family of treatment contrasts and needs its own declared interpretation. None of this proves that the interventions are ineffective; it means ranking them is exploratory.

**R2-W5. Rounding obscures an important boundary.** The stored `v3.json` gives Holm-adjusted p = 0.05147395 for both Plain margins; §5 prints .05. The paper elsewhere says the evidence is weak and does not hide the multiplicity result, so I do not view this as misconduct or a substantive reversal. Reporting .051 or .052 would avoid a readily preventable misreading.

### Questions for the authors

1. What population does each confidence interval target: the fixed model panel over new entities, a population of checkpoints, or model families?
2. Do the Plain and FreshQA patterns remain under equal weighting of developers and after dropping each family in turn?
3. Can a new SWAP set be matched on relation, role plausibility, geography where appropriate, and approximate popularity before any outputs are inspected?
4. Can NEW and OLD be balanced within relation and entity-popularity strata, using the same explicitly current template?

### Recommendation

I recommend revision because these are central control-design questions, not because every result must achieve p < .05. A stronger held-out control set, independent item validation, and a clearly bounded estimand would substantially improve the paper. The statistical response should emphasize effect sizes, interval width, per-family consistency, and transparent exploratory status. Simply adding more generations from the same 35 entities would not resolve the main issues.

## Review 3: Temporal QA, baselines, and reproducibility

**Overall: 2.5/5 — Borderline Findings. Soundness: 2.5/5. Excitement: 3/5. Confidence: 3/5.**

### Summary

NEWTRUE combines temporal factual QA with false-premise evaluation. It offers a Wikidata-based benchmark, matched role-holder substitutions, eleven prompting/evidence conditions, and a detailed analysis of response labeling. This is a plausible ACL resource-and-analysis contribution. Its novelty is specific rather than sweeping: evaluating recently true presuppositions with matched false alternatives. I am less convinced that the current artifact and experiment set establish a dependable benchmark or demonstrate transfer to practical premise-verification systems.

### Strengths

1. **Prior work is acknowledged fairly.** The manuscript explicitly credits FreshQA for valid-premise losses under premise checking and cites recent work on general false challenges. It also distinguishes asking who holds a role from asking a question that already supplies a holder.
2. **The exact FreshQA instruction is an informative baseline.** Its different behavior prevents the paper from reducing all premise-check prompts to the authors' more aggressive wording.
3. **Evidence conditions are useful diagnostic controls.** Fresh, stale, and mixed snippets isolate aspects of evidence use. The manuscript correctly identifies fresh evidence as oracle input and states that these experiments do not evaluate deployed retrieval.
4. **There is substantial local reproducibility material.** The artifact includes cached data, responses, judge labels, analysis scripts, macro/table generation, and provenance. Selected analysis code agrees with the stated paired bootstrap and model-level testing approach.

### Major weaknesses

**R3-W1. Benchmark correctness needs independent evidence at the item level.** Wikipedia surname matching, P39 checks, LLM flagging, and subsequent audits are useful filters, but they do not independently validate all final propositions. Appendix A and the limitations document residual concerns: incomplete historical records, inconsistent treatment of interim holders, generic role names, and two triple dates that may only have year-level precision. In a small temporal benchmark, a few wrong or ambiguous propositions can affect several aggregate results. I would prioritize a complete, dated source audit of the 35 triples and the headline NEW/OLD comparison, with exact role wording and date precision preserved.

**R3-W2. The intervention baseline set is broad but shallow.** Eleven conditions are not eleven competing premise-verification methods. Most are prompt or evidence variants. The paper cites [Qin et al.'s retrieval-augmented logical verification](https://arxiv.org/abs/2504.06438) but does not test a structured verification stage. [Wang and Blanco's atomic-assumption verification approach](https://aclanthology.org/2025.emnlp-main.1228/) is another directly relevant comparison absent from the current bibliography. A compact evidence-grounded verifier that explicitly decides the role-holder proposition before answering would distinguish instruction-following failure from failure of premise verification. This is especially useful given the “priorities” confound.

**R3-W3. Practical retrieval behavior remains unknown.** A one-sentence oracle is a good controlled baseline, but it cannot estimate retrieval recall, source conflict, irrelevant context, or the ability to locate evidence about the requested priorities. This is a scope limitation, not an error in the reported oracle experiment. A small frozen-corpus or snapshot-controlled retrieval test would strengthen the practical contribution. If omitted, the paper should remain a controlled premise-response analysis and avoid implying that current evidence is a deployable solution.

**R3-W4. The public reproduction route needs consolidation.** `artifact/README.md` still describes a five-condition item build and a seven-condition generation pipeline, while the final paper includes additional groups, triples, and eleven interventions. `CHECKPOINT.md` provides the later analysis command, and `PROVENANCE.md` contains both historical mappings and later replacements. The required information largely exists, but a new user must reconstruct which paths are current. A frozen-data reproduction command and a separate fresh-data regeneration command should identify final exclusions, triple construction, model revisions, judge versions, and expected outputs. I did not rerun the full pipeline, so this is a documentation finding, not a claim that reproduction fails.

### Questions for the authors

1. Can each final triple be accompanied by snapshot-dated evidence for current truth, former-holder falsity, swapped-holder falsity, and any uncertain appointment date?
2. Does an explicit evidence-grounded proposition verifier avoid the false-premise opening behavior under the same models and snippets?
3. What exactly is frozen: raw Wikidata responses, article revisions, rendered evidence, or only item IDs and cached extracts? Which future regeneration differences are expected?
4. Can a clean environment reproduce Tables 1–3 from stored outputs without accessing live data or API judges?

### Recommendation

I am borderline Findings. The paper already offers enough models and analyses for a focused empirical study; adding an arbitrary frontier model is not a prerequisite. The highest-value additions are verified item provenance, one stronger structured premise-verification baseline, and a current reproduction path. I would move toward acceptance if these show that the contribution survives outside the authors' particular prompt and audit pipeline. A full production retrieval system is optional if the claims stay controlled and narrow.

## Review 4: Empirical contribution and practical value

**Overall: 3/5 — Findings. Soundness: 3/5. Excitement: 3.5/5. Confidence: 3/5.**

### Summary

I read this paper primarily as a bounded empirical analysis of small open models. It demonstrates an easily overlooked interaction: models can challenge true recent facts, and interventions intended to make them more cautious can change acceptance, deferral, and correction in different ways. The evidence is imperfect, but the paper consistently exposes its limitations. Under that descriptive reading, I would support Findings, while not recommending the main conference.

### Strengths

1. **The recommendation to benchmark true-premise rebuttals is concrete and reusable.** Splitting valid premises by recency and reporting true/false rebuttals separately gives evaluators a useful diagnostic beyond aggregate accuracy. The paper makes this operational with released prompts and triple construction.
2. **Several findings remain informative without universal generalization.** The two premise-check instructions behave differently; cutoff reminders often defer rather than answer; oracle evidence reduces false corrections without guaranteeing premise acceptance under the current labels. These observations warn against treating a single improvement number as evidence of better judgment.
3. **The paper goes beyond a cherry-picked small-model anecdote.** It reports per-model heterogeneity, tests three larger models separately, and includes held-out labels from another provider. The 256-token Plain test retains the qualitative margins. These checks do not settle every concern but provide meaningful triangulation.
4. **Writing and scientific candor are strong.** The introduction establishes the problem, the metric is interpretable, and the limitations distinguish label uncertainty, control flaws, scope, and unproven mechanism. The writing feels specific and accountable; I would not characterize it as generic or formulaic.

### Weaknesses

**R4-W1. The benchmark is narrow.** There are 35 triples across five relations, with only one CEO triple and substantial concentration in government/state roles. Results should not be generalized to all changing knowledge or multilingual deployment. The larger models improve coverage but do not overcome the item-level limitations.

**R4-W2. Some striking numbers are definition-sensitive.** Most Plain rebuttals are hedged, and RAG-fresh+PC results depend on how internally inconsistent answers are classified. The paper now reports enough of this sensitivity for a descriptive reading, but a reader may still remember the pooled 39% rather than the 27–28% held-out rates or the concentration in small Qwen models. I would put these together in the main presentation.

**R4-W3. The main-grid result deserves less rhetorical weight.** The 29% versus 8% comparison is easy to understand but less controlled than the triples. The abstract could lead with the matched result and present NEW-versus-OLD as supporting context. This would align the strongest scientific design with the reader's first impression.

**R4-W4. Practical utility is not measured.** A deferral can be appropriate when the model lacks information about priorities, and accepting a premise does not ensure a correct answer. The paper does not measure user outcomes, answer factuality, or retrieved-document quality. These should remain explicit boundaries, and the deferral breakdown should be easier to locate.

### Questions for the authors

1. What is the smallest set of robust, descriptive conclusions the authors would retain if human adjudication changed the oracle-plus-check rate substantially?
2. Could the abstract and opening figure foreground the matched experiment, with a direct pointer to model heterogeneity and the hedge split?
3. Can the release provide separate stance, refusal, and answer-sufficiency fields so later researchers can use stricter definitions without rerunning generation?

### Recommendation

I support Findings on the strength of the bounded measurement study, not as evidence of a universal mechanism or a validated deployment solution. I regard the cross-family labeling checks and explicit caveats as enough to make the descriptive evidence useful, while recognizing that R1–R3 reasonably place greater weight on independent validation. I would not require a novel algorithm, a mechanistic interpretability study, or broad domain expansion for this paper to merit publication. I would reconsider if adjudication or the complete item audit materially reversed the central patterns. Main-conference acceptance would require a clearer additional advance in measurement validity, explanatory insight, or practical evaluation.

## Shared related-work, baseline, and theory audit

This is a targeted check of eleven research sources, not an exhaustive literature review. “Present” means the work is already cited in the current manuscript; such rows identify opportunities to sharpen comparison rather than missing citations. The conclusions about what NEWTRUE should do are reviewer inferences from the cited work.

| Verified primary source | Status and relevant overlap | Recommended action |
| --- | --- | --- |
| [FreshLLMs / FreshQA, Vu et al., Findings ACL 2024](https://aclanthology.org/2024.findings-acl.813/) | Present. Combines dynamic QA, false-premise questions, search-based prompting, and human-grounded evaluation. | Keep the explicit credit for valid-premise costs. Clarify that the exact instruction baseline is not a reproduction of full FreshPrompt retrieval and evaluation. |
| [Two Axes of LLM Abstention, Wagner, 2026 preprint](https://arxiv.org/abs/2607.08456) | Present. Directly overlaps with indiscriminate challenges after premise-check instructions and separates answer correctness from answerability. | State the incremental contribution as temporally new truths with matched controls. Consider its separation of constructs when redesigning labels; a probe-based system is optional, not a mandatory baseline. |
| [(QA)², Kim et al., ACL 2023](https://aclanthology.org/2023.acl-long.472/) | Present. Studies naturally occurring questionable assumptions and adequacy of responses. | Explain how the constructed role-holder triples complement natural questions. Borrow the evaluation emphasis on response acceptability without claiming to measure it already. |
| [CREPE, Yu et al., ACL 2023](https://aclanthology.org/2023.acl-long.583/) | Present. Natural false-presupposition questions and difficulties with evidence retrieval. | Use to distinguish controlled substitution validity from ecological validity. A small natural-question transfer set would help, but is lower priority than validating the current set. |
| [Don't Let It Hallucinate, Qin et al., 2025 preprint, revised 2026](https://arxiv.org/abs/2504.06438) | Present. Verifies logical premises using retrieved factual evidence before generation. | Add or adapt a structured premise-verification baseline, or explain precisely why evaluating prompt instructions is the chosen scope. The current arXiv record also reports TMLR 2026; check bibliography version metadata before submission. |
| [Identifying and Answering Questions with False Assumptions, Wang and Blanco, EMNLP 2025](https://aclanthology.org/2025.emnlp-main.1228/) | Not found in the current bibliography. Uses external evidence and atomic-assumption generation/validation. | Add a direct comparison in related work. Together with Qin et al., this motivates one compact evidence-grounded verifier; it does not require implementing every published system. |
| [DyKnow, Mousavi et al., Findings EMNLP 2024](https://aclanthology.org/2024.findings-emnlp.471/) | Present. Dynamic Wikidata evaluation of temporal factual knowledge and prompt inconsistency. | Contrast direct factual recall with response to an asserted premise. Make the independent value of matched premise controls explicit. |
| [PAT-Questions, Meem et al., Findings ACL 2024](https://aclanthology.org/2024.findings-acl.777/) | Present. Present-anchored temporal QA with refreshable knowledge-graph answers. | Distinguish a frozen evaluation snapshot from regeneration. Specify how time-qualified statements, article revisions, and date precision are retained. |
| [ClashEval, Wu et al., 2024 preprint](https://arxiv.org/abs/2404.10198) | Present. Studies conflict between internal knowledge and external evidence, including plausibility of perturbed content. | Motivate plausibility controls for SWAP and distinguish evidence compliance from factual discrimination. |
| [When Not to Trust Language Models / PopQA, Mallen et al., ACL 2023](https://aclanthology.org/2023.acl-long.546/) | Present. Relates entity popularity to parametric recall and retrieval benefits. | Retain popularity adjustment, but describe sitelinks as a proxy. Matching on this variable alone does not establish equal familiarity. |
| [STALE, Chao et al., 2026 preprint](https://arxiv.org/abs/2605.06527) | Present. Tests evolving agent memory, including resistance to premises about outdated states. | Sharpen the distinction between updating contextual memories and handling post-release public facts in fixed model parameters. Avoid presenting all temporal premise handling as untouched territory. |

### Baseline priorities

| Priority | Addition or clarification | What it would resolve |
| --- | --- | --- |
| High | Explicit evidence-grounded verification of the role-holder proposition before answering; include supported/contradicted/insufficient-evidence outcomes | Whether a structured verifier handles the task more reliably than asking the answer generator to check a premise |
| High | A compact task asking directly about the role-holder proposition, paired with the existing priorities question | Whether insufficient evidence about priorities is driving apparent premise rejection or deferral |
| Medium | Several preselected paraphrases of both positive-validity and negative-falsity checking instructions | Whether the observed contrast transfers across wording rather than reflecting one sentence pair |
| Medium | Frozen, naturally written source passages and, if practical, snapshot-controlled retrieval | Whether effects survive beyond one-sentence oracle snippets |
| Medium | One additional independent model family when weights and compute permit | Whether the pooled pattern is dominated by Qwen; not a requirement to chase every latest model |
| Low / explanatory | Always-accept, always-rebut, and always-defer reference policies, computed analytically | They all have zero rebuttal margin, but very different practical behavior; this clarifies what J does and does not capture |

### Theory and conceptual opportunities

1. **Signal-detection interpretation:** J is a difference between a false-premise detection rate and a true-premise false-alarm rate. This helps distinguish a broad tendency to challenge from better separation. There is no continuously varied threshold here, so the paper should not imply a full ROC analysis without additional scores or operating points.
2. **Selective prediction:** Deferral changes coverage. A useful extension would report answer coverage and correctness separately from premise stance, using an explicit cost model only if justified. No utility-optimal policy has been established by the current margins.
3. **Causal interpretation:** Time of truth change, familiarity, role plausibility, entity popularity, and wording can all influence behavior. Matching entity and wording does not identify the causal effect of stale internal knowledge. The current null predecessor-belief analysis should constrain mechanistic claims, not be treated as a failed test to be explained away.
4. **Measurement decomposition:** A response may accept a role-holder premise, lack information for the requested answer, hedge its knowledge, and contain a contradictory opening. These are separable properties. Annotating them separately would make the benchmark more reusable and reduce dependence on one aggregation rule.

## Writing, logic, and presentation audit

The prose is generally clear, specific, and appropriately cautious. There is no sound basis for inferring authorship from style, and generic “AI-like writing” is not a substantive weakness of this version. The main improvements concern alignment of constructs, claims, and prominent evidence.

| Location | Issue | Severity | Concrete correction |
| --- | --- | --- | --- |
| Abstract and §1 | The unmatched 29% versus 8% result receives headline prominence before the better-controlled triples. | Medium | Lead with the matched experiment; identify the grid comparison as supporting descriptive evidence. |
| §1, explanation involving the model's stored answer | Can read as an established trial-level mechanism, despite the explicit limitations and null predecessor association. | Medium | Present stale knowledge as a motivating hypothesis and distinguish it from the behavior actually measured. |
| §3.1 opening example | “Since becoming” does not entail current occupancy. | High for the definition; contained in the main triples | Introduce the formal task using the explicitly current T2 wording. |
| §3.5, §5, Appendix B | Premise acceptance, answer insufficiency, and refusal are partly collapsed. | High | Define separate annotation axes and provide adjudicated boundary examples. |
| §5 Plain significance | Adjusted .05147395 is displayed as .05. | Low but consequential | Print at least three decimal places around the decision boundary; retain the suggestive interpretation. |
| §5 oracle-plus-check result | Primary pooled 39% is more prominent than the 27–28% held-out estimates. | Medium | Present the judge range and model concentration alongside the primary rate. |
| §6 popularity analysis | Coefficients from different regression types are adjacent; the entity coefficient's scale is not explicit in the prose. | Low | State whether each coefficient is in log-odds or probability units, and identify clustering/model controls. |
| Tables 1–3 | Dense but informative; many uncertainty summaries compete for attention. | Low | Identify primary estimands and group secondary checks by the threat they address. Do not remove inconvenient results for visual simplicity. |
| Appendix D | Planned sampling and annotation wording lag behind the final experiment. | Medium | Update groups, judge pair, four-way labels, oversampling weights, and coverage of triples before collecting annotations. |
| Artifact README/provenance | Historical and current pipeline descriptions are interleaved. | Medium | Provide one current final-version entry point and mark historical steps as archival. |
| §2 | “Wagner (2026) find” occurs despite a single-author reference. | Low | Change to “finds”; this has no bearing on technical merit. |

## Method, ethics, and artifact assessment

- **Research question:** Clear and suitable for ACL, especially Question Answering or Resources and Evaluation. The empirical/resource contribution should be evaluated on its own merits; a new architecture is unnecessary. These areas appear in the current [ARR call for papers](https://aclrollingreview.org/cfp).
- **Data:** The 332-item main grid and 70 additional false controls give 402 distinct premise items; the 35 triple NEW members reuse existing NEW-post items. This should remain explicit so readers do not infer 437 independent items. The effective unit for the main controlled experiment is 35 entities, not the number of generated responses.
- **Ground truth:** The audit is useful and documented, but the work has no completed independent human item validation. Preserve source revision dates, date precision, and role-specific evidence. Corrected oracle inputs require rerunning affected generations, not merely changing evaluation labels.
- **Response labels:** Held-out validation is a strength. Cross-family agreement is evidence of consistency, not a human accuracy estimate. Evaluate ambiguity by condition and model size rather than relying solely on pooled kappa.
- **Statistics:** Paired testing and two-level resampling are appropriate improvements over treating outputs as independent. Model-family concentration, small entity counts, exploratory contrast selection, and the uncertainty target remain unresolved. No blanket significance requirement is imposed.
- **Robustness:** The existing output-length check is informative but covers Plain for four knowledgeable models; it does not establish length robustness for the oracle-plus-check failure mode. A targeted length check on ambiguous intervention responses would have more value than repeating all already-passing analyses.
- **Reproducibility:** Scripts, cached outputs, and generated tables exist. The stored multiplicity statistics were checked during this review. No claim is made that the full artifact has been independently reproduced or that a public anonymous release is currently accessible.
- **Ethics:** The study concerns public role facts and includes a limitation/ethics discussion. The current review identifies no reason for special ethics escalation. Human annotation should follow the stated compensation/consent plan and applicable local review requirements when conducted. A submitted Responsible NLP checklist was not supplied, so its consistency has not been assessed.
- **Submission presentation:** The current PDF has 19 pages including references and appendices, with the conclusion on page 8 and limitations beginning there. Total PDF length alone is not a main-text page-limit violation. Final venue-specific compliance, artifact anonymity, and required submission forms should be checked when preparing the actual commitment; no ACL 2027-specific compliance verdict is claimed here.

## Meta-review

**Decision: reject in the current form; revise and resubmit to the next ARR cycle.**
**Overall assessment: 2/5. Confidence: 4/5.**
**Reviewer recommendations:** 2.5, 2, 2.5, 3. There has been no actual reviewer discussion or author rebuttal; the synthesis below compares the four simulated assessments.

### Area-chair summary

The paper contributes a useful measurement setting at the intersection of temporal knowledge and presupposition handling. Reviewers agree that the question matters, that the matched triples improve on unstructured examples, and that the manuscript is candid and readable. All recognize meaningful experimental work: multiple instruction/evidence conditions, model-wise results, alternative judges, a longer-output check, and separately reported larger models. The contribution is best understood as an empirical analysis and potential benchmark, rather than a new mitigation method or a causal explanation of outdated knowledge.

The decisive disagreement concerns the standard of evidence needed for publication. R4 accepts the restricted descriptive account, viewing the agreement across judges and the disclosed caveats as sufficient for Findings. R1 and R3 are close to that view but are not satisfied with construct and benchmark validation. R2 gives greater weight to control plausibility and population-level inference. These positions are compatible: the phenomenon can be worth reporting while the proposed measurement resource remains insufficiently validated.

I side with revision because the unresolved weaknesses affect what the central metrics mean. The oracle verifies the role-holder fact but not the priorities requested in the question; some responses mix acceptance, answer insufficiency, and a false-premise opening. Thus, automatic agreement alone cannot settle whether the measured outcome is premise denial. At the item level, the paper explicitly acknowledges potentially wrong dates and ambiguous roles. At the control level, SWAP is mostly a cross-country substitution rather than a verified familiarity match. These are substantive issues for a paper whose principal contribution is controlled measurement.

Statistical uncertainty strengthens the case for careful revision but is not the sole rejection reason. The reported effects are not dismissed because adjusted p-values exceed .05, nor is “no significant difference” interpreted as equivalence. The concern is whether a small selected panel and confounded controls justify the intended generalization. A convincing revision could remain descriptive and publish null or uncertain findings, provided the underlying measurement is trustworthy.

### What is required to change the decision

1. **Validate the measured behavior.** Complete a blind human response study that distinguishes role-premise stance from answer sufficiency, hedging, refusal, and internal contradiction. Recompute the principal results and show judge error by condition. Use representative estimates or explicit sampling weights.
2. **Validate the benchmark propositions.** Independently audit every main-test triple and the headline NEW/OLD sample with snapshot-dated evidence. Fix ambiguous role labels and date precision. Rerun generations where input text changes.
3. **Resolve the false-control claim.** Either construct adequately sized plausible/popularity-matched swaps and evaluate them, or explicitly narrow the contribution to the observed substituted controls and remove the implication that unfamiliarity is isolated. The first option would make the paper substantially stronger.
4. **State the estimand and generalization boundary.** Report family-balanced and leave-one-family-out sensitivity, distinguish fixed-panel description from model-population inference, and separate primary comparisons from exploratory intervention comparisons.
5. **Make the final resource usable.** Consolidate the frozen-data reproduction route and update the annotation protocol and documentation to match the final experiment.

### Important but not independently decisive

A structured evidence-grounded verifier would improve the baseline story. More question paraphrases, an independent model family, natural source passages, or a modest real-retrieval evaluation would strengthen transfer claims. They should be prioritized after validation rather than used to compensate for unresolved labels. A user study, mechanistic interpretability analysis, new architecture, or comprehensive frontier-model sweep is not required for a credible Findings version.

### Acceptance outlook

As subjective author-feedback calibration, I estimate **10–20% for ACL main conference** and **25–45% for any acceptance including Findings** in the current form. These ranges are not empirical predictions and do not derive from averaging the simulated scores. They reflect the clear topic fit and writing, a potentially useful contribution, and likely reviewer disagreement over soundness. If independent validation preserves the main findings and the control/inference issues are resolved, a reasonable revised band would be **20–35% for main conference** and **50–70% for acceptance including Findings**. Confidence in these probability bands is **2/5**; confidence in the identified revision priorities is higher. New evidence that changes the results should change both the claims and this assessment.

## Prioritized revision checklist

### P0 — Decision-changing validation and design

- [ ] **Audit all 35 triples independently.** Record evidence for each of the 105 role-holder propositions, source/revision date, exact role title, temporal validity, and disputed cases. Audit the headline NEW and OLD sets as well. **Done when:** a second checker can trace every retained main-test proposition to evidence and adjudication is logged. Addresses R1-W3, R3-W1.
- [ ] **Preserve date precision and correct role phrases.** Render year-only dates as years, inspect generic chairperson/CEO labels, and apply a consistent interim/reinstatement policy. **Done when:** corrected inputs and exclusions are versioned and all affected generations/labels are regenerated. Addresses R3-W1.
- [ ] **Complete the human response-validation study.** Include a representative sample plus explicit oversampling of hedged denials, oracle-plus-check contradictions, refusals, and priority-insufficiency answers. **Done when:** sampling probabilities, blinded annotation, adjudication, per-class errors, and uncertainty are reported. Addresses R1-W1–W2.
- [ ] **Separate premise stance from answering ability.** Annotate acceptance/denial/uncertainty of the role-holder proposition separately from answer sufficiency/refusal; mark hedges and contradictory statements. **Done when:** the main conclusions are recomputed under both the original and clarified schemes. Addresses R1-W1, R4-W2/W4.
- [ ] **Strengthen or narrow the SWAP comparison.** Prefer a new held-out set with plausible substitutions, approximate popularity matching, and geography considered where relevant; use human plausibility checks rather than citizenship alone. **Done when:** a sufficient matched set is evaluated, or every familiarity-isolation claim is removed and the remaining contribution is justified. Addresses R2-W1.
- [ ] **Clarify the statistical target.** State what varies in each interval; add equal-developer-weight and leave-one-family-out estimates. **Done when:** readers can distinguish fixed-panel findings from extrapolation and see whether one family drives a conclusion. Addresses R2-W3.
- [ ] **Declare the contrast families honestly.** Separate the two Plain margins, within-condition margins, and intervention-minus-Plain comparisons. Mark previously explored analyses as exploratory; do not retrospectively call them preregistered. **Done when:** effect sizes, uncertainty, and any multiplicity handling correspond to the stated claims. Addresses R2-W4.

### P1 — Strengthen the scientific contribution

- [ ] **Improve the NEW-versus-OLD comparison.** Use common present-tense wording and relation/entity-popularity balancing; report residual differences. **Done when:** the recency association is estimated under a more comparable design or kept explicitly descriptive. Addresses R2-W2, R4-W3.
- [ ] **Add one structured premise-verification baseline.** Verify the explicit role-holder proposition against the same evidence before generating an answer. **Done when:** false rebuttals, false-premise catch rate, deferral, and answer sufficiency are compared on the same items. Addresses R3-W2.
- [ ] **Test a direct role-verification task alongside the priorities question.** **Done when:** the analysis can distinguish missing priority information from disagreement with the role premise. Addresses R1-W1, R3-W2.
- [ ] **Check intervention-specific output-length sensitivity.** Focus on ambiguous RAG-fresh+PC responses rather than rerunning every condition. **Done when:** complete outputs show whether opening denials are maintained, qualified, or contradicted later. Addresses R1-W2, R4-W2.
- [ ] **Use a small preselected instruction-paraphrase set.** Include positive-validity and negative-falsity wording without selecting prompts after inspecting results. **Done when:** conclusions about wording report variation across the set. Addresses R2-W4.
- [ ] **Add Wang and Blanco (2025) and sharpen closest-work contrasts.** Update Qin et al.'s version/publication metadata if appropriate. **Done when:** novelty rests on the temporal matched evaluation rather than rediscovery of generic false challenges. Addresses R3-W2.
- [ ] **Consolidate artifact reproduction.** Provide a current offline command for Tables 1–3, expected item counts, model/judge identifiers, dependencies, and a separate regeneration route. **Done when:** a clean environment rebuilds the key tables from frozen outputs without live queries or paid calls. Addresses R3-W4.

### P2 — Presentation and submission preparation

- [ ] Lead the abstract and opening summary with the matched-triple result; label main-grid evidence as descriptive.
- [ ] Introduce the method using the explicitly current template and align the formal proposition with that wording.
- [ ] Print the Plain Holm-adjusted p-value as approximately .0515, avoiding the ambiguous .05 rounding.
- [ ] Put the 39% primary and 27–28% held-out oracle-plus-check rates together, with the concentration in small Qwen models.
- [ ] Identify regression scales and distinguish person popularity from entity popularity wherever both appear.
- [ ] Update Appendix D's group count, judge identities, annotation axes, refusal handling, and weighted-sampling plan before it is used.
- [ ] Keep unproven mechanism, actual retrieval performance, answer factuality, and user harm outside the established conclusions.
- [ ] Fix the singular-author agreement in “Wagner (2026) finds.”
- [ ] Check final venue page limits, anonymous artifact access, and submission-checklist consistency against the venue's current instructions.

**Recommended execution order:** validate items and response constructs first; repair controls and recompute estimates second; add the focused verifier baseline third; then revise the narrative and package the artifact. If corrected measurements materially alter the findings, revise the claims rather than preserving the current headline rates.
