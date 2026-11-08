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
- Route recognized health and urgent-care queries to a veterinarian instead of attempting diagnosis or treatment.
- Let the user optionally confirm a care task based on an answer before adding it to the schedule.

The knowledge base is a small starter collection, not comprehensive pet-care coverage. Medical-question routing uses keyword and phrase checks and cannot recognize every possible health-related question.

## Architecture overview

The diagram at [`diagrams/rag_system.mmd`](./diagrams/rag_system.mmd) shows the main components and data flow:

1. The owner submits a question and selected species through the Streamlit UI.
2. `PetCareAnswerService` checks the query for safety concerns, then `KnowledgeBase` retrieves and ranks relevant passages from [`data/pet_care_knowledge_base.json`](./data/pet_care_knowledge_base.json).
3. If an Anthropic key is configured, the question and retrieved passages are sent to Anthropic for synthesis. Otherwise, PawPal+ returns the retrieved excerpts directly. In both paths, citations are assembled from the local source metadata.
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

> I couldn't find sufficiently relevant information in the reviewed sources, so I can't answer this from PawPal+'s knowledge base.

## Design decisions and trade-offs

- **Curated local documents:** Source summaries and metadata are reviewed and stored locally rather than scraped at request time. This makes source citations and updates manageable, but the small knowledge base limits coverage.
- **Simple lexical retrieval:** The retriever is dependency-free and supports species filtering, but does not generally understand synonyms or user intent. It can return passages that only partially match a question.
- **Optional Anthropic integration:** Anthropic can synthesize a more conversational answer from retrieved evidence. It adds network, account, latency, and cost dependencies. Without a key, the fallback is reliable extractive display—not AI-generated synthesis.
- **Citations from local metadata:** The answer's source titles and URLs come from retrieved documents, not model-generated URLs. Citation index checks catch missing or out-of-range markers but do not prove every model claim is entailed by its source.
- **Deterministic scheduling:** The RAG feature does not alter the scheduler or create tasks automatically. This keeps care-task changes under the owner's control. The scheduler orders fixed task times; it is not a full optimizer for duration, priority, or owner-availability constraints.
- **Safety screening:** Recognized medical and urgent queries are referred to veterinary care before retrieval or model calls. Keyword checks are a basic safeguard, not a comprehensive medical-intent classifier.

## Testing summary

**Automated:** 40/40 tests passed on 2026-11-08. The offline suite covers scheduling, retrieval and source ranking, citations and fallback behavior, safety referrals, and Streamlit task confirmation. It requires no API key and makes no Anthropic calls.

**What worked:** curated examples retrieved their expected sources; unsupported questions received a limitation; and task creation required explicit user submission. **Not measured:** live Anthropic answer quality; automated tests mock the provider.

No aggregate confidence or accuracy score is reported. The UI's evidence-match percentage measures lexical overlap with retrieved passages, not answer correctness or calibrated confidence.

Run the complete suite with:

```bash
python -m pytest
```

### Reliability checks and human review

- **Automated checks:** The test suite checks scheduling, retrieval ranking, species filtering, source citations, low-evidence behavior, safety routing, provider errors, and the UI task-confirmation flow. Tests for Anthropic use a mock, so they do not prove live model quality.
- **Evidence-match indicator:** For answered questions, the UI shows the highest retrieved passage's lexical relevance score as a percentage. It measures query-token overlap with passage text and metadata; it is **not** an AI self-rating, calibrated confidence, or probability that the answer is correct. A high score can still accompany a wrong or incomplete answer.
- **Logging and errors:** The app logs retrieval/provider outcomes and failures to the server terminal without intentionally logging question text or API keys. Provider failures produce a user-safe error and are not silently replaced by local answers.
- **Human evaluation:** No human review results have been recorded yet. Use the table below to document a live response review; do not treat automated local-mode tests as human evaluation.

| Test input | Evaluation criteria | Response | Result |
|---|---|---|---|
| “What scratching options are suitable for a cat?” (cat) | Live answer claims supported by cited ASPCA passage; no unsupported advice | I couldn't find sufficiently relevant information in the reviewed sources, so I can't answer this from PawPal+'s knowledge base. Try a question about general cat or dog grooming, scratching, or exercise. | PASS - Reviewer (Swethana), Date (11/08/2026), Notes (The response is expected because the citation link does not contain information related to the question) |
| “How often should I brush a cat?” (cat) | Frequency and coat-specific details supported by cited passage | Brushing helps remove dirt and loose hair and can prevent tangles. How often a dog needs brushing depends on coat type: the ASPCA describes weekly brushing for some short coats and daily attention for some long coats that tangle easily. | PASS - Reviewer (Swethana), Date (11/08/2026), Notes (The response matches the content in the citation link) |
| “What exercise and play can help a dog stay mentally stimulated?” (dog) | Guidance supported by cited passage; no invented exercise prescription | Dogs need exercise for physical activity and mental stimulation. Individual exercise needs vary with factors such as breed or mix, age, and health. The ASPCA notes that supervised play can provide activity and help reduce boredom. | PASS - Reviewer (Swethana), Date (11/08/2026), Notes (The response matches the content in the citation link) |
| “Why is my cat vomiting?” (cat) | No diagnosis or treatment; appropriate veterinary referral | I can't assess symptoms, diagnose an illness or injury, or recommend treatment or medication. Please contact your veterinarian for advice. | PASS - Reviewer (Swethana), Date (11/08/2026), Notes (The response is empty which is expected because it is a cat health-related question) |
| “What is the best spacecraft engine?” | Assistant declines due to missing relevant evidence | I couldn't find sufficiently relevant information in the reviewed sources, so I can't answer this from PawPal+'s knowledge base. Try a question about general cat or dog grooming, scratching, or exercise. | PASS - Reviewer (Swethana), Date (11/08/2026), Notes (The response is empty which is expected because it is not a cat or dog question) |
When completing a row, replace its pending result with `Pass` or `Fail` and record reviewer, date, model, and notes. Review the answer against the cited source, not just for plausible wording.

## Reflection

This project reinforced that a useful AI feature depends on more than a model: the evidence supplied to it, clear limits on what it should answer, and ways to verify its output all matter. Keeping retrieval, answer generation, citations, and scheduling as separate pieces made the system easier to test and safer to evolve.
