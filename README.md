# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Implementation Summary

`Task` stores a description, scheduled time, frequency, and completion status. `Pet` keeps its own tasks, while `Owner` manages multiple pets and provides access to all of their tasks. `Scheduler` retrieves tasks through the owner, sorts them by time, and can mark them complete. The example in `main.py` creates two pets and prints their combined daily schedule.

## Getting started

### Requirements

- Python 3.9.6 is recommended for the exact tested environment.
- [`requirements.txt`](./requirements.txt) pins the complete resolved Python dependency set, including transitive dependencies.
- An Anthropic API key is optional. Without one, the app uses local extractive answers from retrieved passages; with one, it uses Anthropic to formulate an answer from those passages.

### Install and run (macOS/Linux)

From the repository root:

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest
python -m streamlit run app.py
```

### Install and run (Windows PowerShell)

```powershell
py -3.9 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest
python -m streamlit run app.py
```

If PowerShell does not have Python 3.9 installed, use `py -3` for another Python 3.9+ version. The pinned dependencies were verified with Python 3.9.6.

To use Anthropic-generated responses, set the key in the shell before launching Streamlit. Do not put keys in source files or commit them.

```bash
# macOS/Linux
export ANTHROPIC_API_KEY="your-key"
```

```powershell
# Windows PowerShell
$env:ANTHROPIC_API_KEY = "your-key"
```

Without the key, no Anthropic network request is made. To run the sample CLI schedule instead of the UI, use `python main.py`. Run tests from the repository root with `python -m pytest`; the suite is offline and does not require an API key or `pytest-cov`.

The app logs its answer path, retrieval outcomes, and provider failures to the Streamlit server's terminal. Set `PAWPAL_LOG_LEVEL` to `DEBUG`, `INFO`, `WARNING`, or `ERROR` to adjust verbosity. Query text and API keys are not intentionally written to application logs. Anthropic errors are logged and shown as a safe, user-facing message; they do not silently switch to local mode.

## Features

- **Sorting by time:** Schedules tasks in chronological order by clock time without changing the original list.
- **Task filtering:** Filters by completion status, pet name, or both. Pet-name matching is case-insensitive.
- **Conflict warnings:** Groups tasks by due date and time and warns when multiple tasks share a time slot. Warnings identify the task and pet names, and whether the conflict is for one pet or multiple pets. Repeated references to the same task are counted once.
- **Daily recurrence:** Completing a daily task creates a new, incomplete occurrence due the next day.
- **Weekly recurrence:** Completing a weekly task creates a new, incomplete occurrence due seven days later.
- **One-time tasks:** Completing a one-time task marks it complete without creating another occurrence. Already-completed tasks are not repeated.
- **Streamlit schedule view:** Shows tasks in time order with pet and completion-status filters, and displays actionable conflict warnings.

## RAG Feature: Phase 1 Scope and Safety

The planned Retrieval-Augmented Generation (RAG) feature will provide general pet-care information grounded in a curated knowledge base. It is an informational aid, not a veterinary service, and it will not change PawPal+'s existing deterministic scheduling behavior.

### In scope

- General, low-risk care information, initially focused on enrichment, grooming basics, and routine planning.
- Answers grounded in relevant passages from the knowledge base, with visible citations to the source title and link.
- Species-aware retrieval when the user has selected a pet and the available source material supports that distinction.
- Optional suggestions that a user can review before adding them as a scheduled task.

### Out of scope and safety behavior

- Diagnosing an illness or injury, assessing symptoms, recommending or changing treatment, and providing medication or dosage instructions.
- Replacing advice from a veterinarian or presenting generated content as professional medical guidance.
- For urgent symptoms or possible poisoning, the assistant should not attempt to assess or treat the situation; it should advise contacting a veterinarian or appropriate local emergency animal-care service promptly.
- If the knowledge base does not contain relevant, sufficiently reliable information, the assistant should say it cannot answer from its sources rather than guess.

Users may still schedule medication or veterinary-care tasks based on instructions they already received from their veterinarian; the RAG assistant must not originate or modify those instructions.

### Source acceptance and maintenance

- Use public material from identifiable veterinary, animal-welfare, or other qualified organizations; do not treat anonymous posts or user-generated discussion as authoritative guidance.
- Keep each source's title, publisher, URL, species/topic tags when applicable, and review date alongside its content so answers can cite and filter the material.
- Review material for relevance and safety before adding it. Remove or re-review sources that are outdated, unclear, or inconsistent with other trusted guidance.
- The initial implementation should use a deliberately curated collection; it should not crawl arbitrary web pages at answer time.

### Phase 1 acceptance criteria

- The feature's permitted topics and explicit exclusions are documented before implementation.
- Safety and source-quality rules are defined for the knowledge base and answer behavior.
- Later implementation can be checked against these boundaries: supported claims are cited, unsupported questions receive a limitation, and task suggestions require user confirmation.

## RAG Feature: Phase 2 Knowledge Base

A first curated knowledge base is stored in [`data/pet_care_knowledge_base.json`](./data/pet_care_knowledge_base.json). It contains short, editor-written summaries for cat and dog enrichment and grooming. Each record is a separate document boundary and includes a stable document ID, source title, publisher, URL, source section, species and topic tags, review date, and content type.

The summaries were checked against their linked ASPCA source pages on 2026-11-04. They are paraphrases, not copied source pages. The dataset intentionally excludes diagnosis, treatment, and medication instructions. The URLs are source citations; the app does not fetch or crawl those pages at runtime.

### Phase 2 maintenance rules

- Add only reviewed material from identifiable, qualified organizations, following the source acceptance rules above.
- Keep each record self-contained and preserve its source metadata when splitting or updating content; use a new document ID if a document's meaning or source changes substantially.
- Update `reviewed_on` only after a source has been checked again. Re-check the source URL and content before relying on an entry in an answer.
- Treat the current collection as a small starter set, not as comprehensive pet-care coverage.

## RAG Feature: Phase 3 Retrieval

[`rag_retrieval.py`](./rag_retrieval.py) loads the local JSON knowledge base and exposes `KnowledgeBase.retrieve()`. It ranks documents by lexical overlap between meaningful query terms and each document's content and topic/source metadata, optionally filters by species, applies a relevance cutoff, and returns at most `top_k` passages with their source citations and tags. If no passage meets the cutoff, retrieval returns an empty list so a later answer layer can decline to answer.

The initial retriever is deliberately dependency-free and does not make network or model calls. Lexical matching does not understand synonyms; expand or replace the retrieval method only when evaluation shows this starter approach is insufficient. Run `pytest tests/test_rag_retrieval.py` to validate ranking, species filtering, citations, cutoff behavior, and invalid input handling.

## RAG Feature: Phase 4 Grounded Answers

[`rag_answer.py`](./rag_answer.py) adds `PetCareAnswerService.answer()`. It sends the user question and locally retrieved passages to Anthropic for a concise, source-grounded answer. Source references and URLs are appended from trusted local metadata, not generated by the model. If retrieval returns no relevant passages, the service responds with a clear limitation without calling the API. Medical and possible emergency/poisoning questions are referred to a veterinarian or emergency animal-care service without calling the API or attempting diagnosis or treatment.

Install dependencies with `pip install -r requirements.txt`. When `ANTHROPIC_API_KEY` is set to a non-empty value, the service uses Anthropic; optionally set `ANTHROPIC_MODEL` to an available Anthropic model (default: `claude-sonnet-5-5`). Without a configured key, it falls back to local extractive answers from the retrieved passages and does not make a network call. Never commit API keys. Anthropic provider errors are surfaced rather than silently switching providers. The API receives the user's question and retrieved passage content; do not include sensitive personal information in questions.

The safety routing uses conservative keyword and phrase checks as an initial safeguard, not a complete medical-intent classifier. It cannot guarantee that every medical question will be recognized. The model instruction and citation-index check are additional guardrails, not guarantees of factual accuracy. If the model returns missing or out-of-range citation markers, PawPal+ uses the retrieved passages directly instead of displaying the ungrounded response. Run `python -m pytest tests/test_rag_answer.py` to validate request construction, source grounding, limitations, and safety referrals; tests use a mocked Anthropic client and do not make API calls.

## RAG Feature: Phase 5 PawPal+ Integration

The Streamlit app in [`app.py`](./app.py) includes a pet-care question form. It passes the selected cat or dog species to the answer service, shows source-backed responses and explicit limitations, and displays veterinary referrals as warnings. When the selected species is `other`, retrieval is not restricted to cat or dog documents.

After a supported answer, users can optionally open the task form, enter and review a care-task description, time, and frequency, and explicitly submit it before the task is added to the selected pet's schedule. Answering a question never creates a task automatically. The RAG service remains separate from the existing scheduler. Run `pytest tests/test_app.py` for Streamlit integration coverage.

## RAG Feature: Phase 6 Evaluation

[`tests/test_rag_evaluation.py`](./tests/test_rag_evaluation.py) is a small deterministic evaluation set for cat scratching, cat grooming frequency, dog exercise/play, and dog grooming frequency. Each case checks that the expected document ranks first, the local answer includes the expected evidence, and its citation points to that document's source. These tests run without an Anthropic key or network access. The retrieval layer normalizes a basic `-ing` suffix so common phrasing such as “brush” can match source summaries that use “brushing”; it is still lexical and does not provide general synonym understanding.

Run all unit, retrieval, answer, evaluation, and Streamlit checks with `pytest`. To add an evaluation case, include a natural-language query, species, expected document ID, and a short evidence phrase in `EVALUATION_CASES`; check the curated source before treating the expected phrase as a correctness criterion. These checks cover known examples, not all possible prompts. The Anthropic response remains nondeterministic and needs separate, human-reviewed evaluation with a configured API key before relying on model-generated wording.

## System Diagram

See [`diagrams/rag_system.mmd`](./diagrams/rag_system.mmd) for the RAG request flow, local and Anthropic response paths, safety handling, optional task confirmation, and human and automated evaluation.

## Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Scheduler.organize_tasks()` | Sorts by scheduled clock time without modifying the input list. `organize_tasks()` gathers all owner tasks before sorting. |
| Filtering | `Scheduler.filter_tasks()` | Optionally filters by completion status, pet name, or both. Pet-name matching is case-insensitive. |
| Conflict detection | `Scheduler.detect_conflicts()` | Groups tasks by due date and time, then returns a warning for each slot with multiple tasks. Warnings identify same-pet and cross-pet conflicts. |
| Recurring tasks | `Scheduler.mark_task_complete()` | Marks a task complete and appends a new incomplete task for daily or weekly recurrence, due one or seven days later. One-time and already-completed tasks do not recur. |

## Demo Walkthrough

### Streamlit App

The app lets an owner enter their name and the initial pet's name and species, then schedule a task by entering its description, time, and frequency (daily, weekly, or once). The schedule appears in a table with each task's pet, time, frequency, and completion status. Pet and status selectors filter the table. Conflict warnings appear above the schedule when tasks share a due date and time; otherwise, the app confirms that no conflicts were detected.

### Example Workflow

1. Enter the owner's name and the pet's name and species. This creates the initial pet in the app.
2. Enter a task such as "Morning walk," choose its time and frequency, and submit the form.
3. View the task in the schedule table, ordered by time. Use the pet and status selectors to filter the displayed tasks.
4. If two tasks overlap, review the warning for the task names, pets, date, and time, then move one task to another time.

The Streamlit form creates one initial pet; adding additional pets is demonstrated in the CLI example below. The Scheduler sorts tasks by scheduled clock time, filters by pet and completion status, and detects conflicts by due-date/time slot. Completing a daily or weekly task through the Scheduler creates its next occurrence for the following day or seven days later.

### CLI Output

Run `python3 main.py` to print a sample schedule and conflict warning:

```text
Today's Schedule
Owner:  Jordan
07:30 - Breakfast
08:00 - Morning walk
14:00 - Nap
16:00 - Snack
16:00 - Play
18:00 - Evening feeding
Warning: Snack (Biscuit), Play (Biscuit) are scheduled for 16:00 on 2026-10-18 for the same pet.
```
