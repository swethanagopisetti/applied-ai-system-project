# PawPal+ — Pet Care Planner and RAG Assistant

## Project summary

**Original project (Modules 1–3): PawPal+**, a pet-care planning project. Its original goal was to help busy pet owners keep track of their pets' care tasks and organize a daily schedule. The project modeled owners, pets, tasks, and a scheduler; it supports task entry, chronological ordering, filtering, recurring tasks, and schedule-conflict warnings.

This iteration adds a Retrieval-Augmented Generation (RAG) question-answering feature to the Streamlit app. PawPal+ retrieves short, reviewed cat- and dog-care passages, then either sends them to Anthropic to formulate a grounded response or, without an API key, displays the retrieved passages with their citations.

It matters because pet-care answers should be traceable to sources and should not present unsupported content as veterinary guidance. The scheduler remains deterministic, and the RAG assistant never creates tasks without the owner's confirmation.

## What it does

- Add and view pet-care tasks in a Streamlit schedule.
- Sort and filter tasks and warn about tasks scheduled at the same time.
- Retrieve curated guidance about cat and dog grooming, scratching, exercise, and play.
- Filter retrieval by the selected cat or dog species.
- With `ANTHROPIC_API_KEY`, have Anthropic synthesize an answer from the retrieved passages.
- Without an API key, return the relevant reviewed passages directly; this local mode is extractive, not a local generative model.
- Show source citations and decline unsupported questions.
- Limit answers to grooming, scratching, enrichment, exercise, and play; decline unsupported topics and species.
- Infer cat/dog retrieval filters from a species named in the question, and decline mixed-species or selected/query mismatches.
- Route recognized health and urgent-care queries to a veterinarian instead of attempting diagnosis or treatment.
- Treat user questions and retrieved passages as untrusted input; reject common instruction-override requests and check generated claims for citation and lexical support before accepting them.
- Let the user optionally confirm a care task based on an answer before adding it to the schedule.

The knowledge base is a small starter collection, not comprehensive pet-care coverage. Scope, prompt-injection, and medical screening use bounded keyword and phrase checks; they cannot recognize every risky or out-of-scope query. The claim-support check is lexical, not proof of semantic entailment.

## Architecture overview

The diagram at [`diagrams/rag_system.mmd`](./diagrams/rag_system.mmd) shows the main components and data flow:

1. The owner submits a question and selected species through the Streamlit UI.
2. `PetCareAnswerService` checks the query for health/safety concerns, species mismatches, and supported topics. `KnowledgeBase` then retrieves and ranks passages from [`data/pet_care_knowledge_base.json`](./data/pet_care_knowledge_base.json), filtering by the selected species or a single species named in the query.
3. If an Anthropic key is configured, the question and retrieved passages are sent to Anthropic for synthesis. The prompt marks both as untrusted data; each generated sentence must cite a retrieved passage and pass a lexical-overlap check or PawPal+ falls back to the retrieved excerpts. Without a key, PawPal+ returns those excerpts directly. Citations are assembled from local source metadata.
4. The UI shows the answer, a limitation, or a veterinary referral. A suggested schedule task is added only after the owner fills out and submits the task form.
5. Automated tests check retrieval, answer handling, safety routes, and the UI. Human review is needed to assess source quality and whether model-generated wording is faithful to its citations.

Key implementation files:

- [`app.py`](./app.py) — Streamlit interface and optional task confirmation.
- [`rag_retrieval.py`](./rag_retrieval.py) — curated knowledge-base loading and lexical retrieval.
- [`rag_answer.py`](./rag_answer.py) — safety routing, answer-provider selection, and source citations.
- [`data/pet_care_knowledge_base.json`](./data/pet_care_knowledge_base.json) — reviewed, editor-written summaries and source metadata.
- [`pawpal_system.py`](./pawpal_system.py) — pet, owner, task, and scheduler logic.
- [`tests/`](./tests) — scheduler, retrieval, RAG, evaluation, and Streamlit tests.

## Setup and run

### Requirements

- Python 3.9.6 is the tested version.
- [`requirements.txt`](./requirements.txt) pins the full tested dependency set.
- An Anthropic API key is optional. No key is required for local extractive responses or tests.

### macOS or Linux

Run these commands from the repository root:

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest
python -m streamlit run app.py
```

### Windows PowerShell

```powershell
py -3.9 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest
python -m streamlit run app.py
```

To request Anthropic-generated responses, set your API key in the shell before launching the app. Do not store it in source code or commit it.

```bash
# macOS/Linux
export ANTHROPIC_API_KEY="your-key"
```

```powershell
# Windows PowerShell
$env:ANTHROPIC_API_KEY = "your-key"
```

`ANTHROPIC_MODEL` can optionally select another model available to your account. Without a configured key, the app makes no Anthropic request. To run the sample command-line schedule instead of Streamlit, use `python main.py`.

The app logs answer routing, retrieval outcomes, and provider failures to the server terminal. Set `PAWPAL_LOG_LEVEL` to `DEBUG`, `INFO`, `WARNING`, or `ERROR` to adjust verbosity. Logs do not intentionally include question text or API keys. Provider failures are logged and surfaced as a user-safe error; they do not silently switch to local mode.

## Sample interactions

The following are representative **local-mode** outputs, captured with `ANTHROPIC_API_KEY` unset. Local mode quotes retrieved knowledge-base summaries; it does not generate a paraphrase.

### 1. Supported cat-care question

**Input:** “What scratching options are suitable for a cat?” (species: cat)

**Output excerpt:**

> Offer cats appropriate places to scratch, such as a stable scratching post with a rough covering or a scratching pad. Interactive toys are also listed by the ASPCA among basic cat supplies. [1]
>
> [1] General Cat Care — ASPCA, Scratching; Cat Supply Checklist

The actual response also includes the source URL and a note that the information is not veterinary advice.

### 2. Supported dog-care question

**Input:** “What exercise and play can help a dog stay mentally stimulated?” (species: dog)

**Output excerpt:**

> Dogs need exercise for physical activity and mental stimulation. Individual exercise needs vary with factors such as breed or mix, age, and health. The ASPCA notes that supervised play can provide activity and help reduce boredom. [1]
>
> [1] General Dog Care — ASPCA, Exercise

### 3. Health-related question

**Input:** “Why is my cat vomiting?”

**Output:**

> I can't assess symptoms, diagnose an illness or injury, or recommend treatment or medication. Please contact your veterinarian for advice.

This is a safety referral, not a diagnosis. The keyword-based screen may not catch every medical question.

### 4. Unsupported question

**Input:** “What is the best spacecraft engine?”

**Output:**

> I can help only with general cat or dog grooming, scratching, enrichment, exercise, and play questions covered by the reviewed sources.

## Design decisions and trade-offs

- **Curated local documents:** Source summaries and metadata are reviewed and stored locally rather than scraped at request time. This makes source citations and updates manageable, but the small knowledge base limits coverage.
- **Simple lexical retrieval:** The dependency-free retriever filters by selected or query-mentioned species, excludes species and source-title metadata from relevance, weights matching content terms fully and topic tags at 0.75, and requires a minimum relevance of 0.6 by default. It does not generally understand synonyms or user intent, so it may decline paraphrases or return only partially relevant passages.
- **Optional Anthropic integration:** Anthropic can synthesize a more conversational answer from retrieved evidence. It adds network, account, latency, and cost dependencies. Without a key, the fallback is reliable extractive display—not AI-generated synthesis.
- **Citations and claim checks:** Source titles and URLs come from retrieved documents, not model-generated URLs. Generated sentences must cite an in-range passage and overlap lexically with it; this heuristic catches some unsupported or uncited claims, but cannot prove semantic entailment or truth.
- **Deterministic scheduling:** The RAG feature does not alter the scheduler or create tasks automatically. This keeps care-task changes under the owner's control. The scheduler orders fixed task times; it is not a full optimizer for duration, priority, or owner-availability constraints.
- **Safety screening:** Recognized medical and urgent queries are referred to veterinary care before retrieval or model calls. Scope and injection phrase checks are also bounded keyword safeguards, not comprehensive classifiers; retrieved text is still sent to the model as untrusted input when a request passes the guards.

## Testing summary

**Automated:** 55/55 tests passed in the latest run. The offline suite covers scheduling, retrieval and source ranking, species filtering and mismatch handling, scope/safety refusals, citations and unsupported-claim fallback, provider errors, and Streamlit task confirmation. Tests mock Anthropic and make no live model calls.

**What worked:** curated examples retrieved their expected sources; unsupported questions received a limitation; and task creation required explicit user submission. **Not measured:** live Anthropic answer quality; automated tests mock the provider.

No aggregate confidence or accuracy score is reported. The UI's evidence-match percentage measures lexical overlap with retrieved passages, not answer correctness or calibrated confidence.

Run the complete suite with:

```bash
python -m pytest
```

### Reliability checks and human review

- **Automated checks:** The test suite checks scheduling, retrieval ranking and thresholds, species inference/mismatch handling, scope and safety routes, citations, lexical claim support, prompt treatment of untrusted passages, provider errors, and the UI task-confirmation flow. Tests for Anthropic use a mock, so they do not prove live model quality.
- **Evidence-match indicator:** For answered questions, the UI shows the highest retrieved passage's weighted lexical relevance score as a percentage. It measures query-token matches against passage content and topic tags; it is **not** an AI self-rating, calibrated confidence, or probability that the answer is correct. A high score can still accompany a wrong or incomplete answer.
- **Logging and errors:** The app logs retrieval/provider outcomes and failures to the server terminal without intentionally logging question text or API keys. Provider failures produce a user-safe error and are not silently replaced by local answers.
- **Human evaluation:** Cat-care questions were first submitted while the Species dropdown was set to Dog, so the species-mismatch guard correctly declined them. Changing the dropdown to Cat allowed the question to be answered. No code change was needed; the answer produced after switching species was not recorded here for source review. No live Anthropic review is recorded.

| Test input | Evaluation criteria | Response | Result |
|---|---|---|---|
| “What scratching options are suitable for a cat?” (query species: cat; selected Species dropdown: dog) | Decline a query that conflicts with the selected pet species; answer after selecting the matching species | The question mentions a different or multiple species than the selected pet. Ask about one supported species at a time. Offer cats appropriate places to scratch, such as a stable scratching post with a rough covering or a scratching pad. Interactive toys are also listed by the ASPCA among basic cat supplies. [1] Sources: [1] General Cat Care — ASPCA, Scratching; Cat Supply Checklist: https://www.aspca.org/pet-care/cat-care/general-cat-care This is general information, not veterinary advice. | PASS - Reviewer (Swethana), Date (11/08/2026), Notes (Mismatch refusal was expected with Dog selected. The question was answered after changing the dropdown to Cat.) |
| “How often should I brush a cat?” (query species: cat; selected Species dropdown: dog) | Decline a query that conflicts with the selected pet species; answer after selecting the matching species | The question mentions a different or multiple species than the selected pet. Ask about one supported species at a time. Regular brushing can remove dirt and loose hair from a cat's coat. The ASPCA suggests one or two brushings per week for many cats, while long-haired indoor cats may need grooming every few days to reduce tangles. If grooming is difficult or risks injury, seek help from a professional groomer or veterinarian. [1] Sources: [1] Cat Grooming Tips — ASPCA, Skin and Fur Care; Brushing Your Cat: https://www.aspca.org/pet-care/cat-care/cat-grooming-tips This is general information, not veterinary advice. | PASS - Reviewer (Swethana), Date (11/08/2026), Notes (Mismatch refusal was expected with Dog selected. User reports the question was answered after changing the dropdown to Cat.) |
| “What exercise and play can help a dog stay mentally stimulated?” (dog) | Guidance supported by cited passage; no invented exercise prescription | Dogs need exercise for physical activity and mental stimulation. Individual exercise needs vary with factors such as breed or mix, age, and health. The ASPCA notes that supervised play can provide activity and help reduce boredom. | PASS - Reviewer (Swethana), Date (11/08/2026), Notes (The response matches the content in the citation link) |
| “Why is my cat vomiting?” (cat) | No diagnosis or treatment; appropriate veterinary referral | I can't assess symptoms, diagnose an illness or injury, or recommend treatment or medication. Please contact your veterinarian for advice. | PASS - Reviewer (Swethana), Date (11/08/2026), Notes (Referral shown; no diagnosis or treatment advice) |
| “What is the best spacecraft engine?” | Assistant declines due to missing relevant evidence | I can help only with general cat or dog grooming, scratching, enrichment, exercise, and play questions covered by the reviewed sources. | PASS - Reviewer (Swethana), Date (11/08/2026), Notes (Out-of-scope request declined) |

When completing a row, replace its pending result with `Pass` or `Fail` and record reviewer, date, model, and notes. Review the answer against the cited source, not just for plausible wording.

## Reflection

This project reinforced that a useful AI feature depends on more than a model: the evidence supplied to it, clear limits on what it should answer, and ways to verify its output all matter. Keeping retrieval, answer generation, citations, and scheduling as separate pieces made the system easier to test and safer to evolve.
