# PawPal+: Pet Care Planner and RAG Assistant

**Presentation length:** approximately 6 minutes  
**Format:** six slides with speaker notes and a short live demo

---

## Slide 1 — The project and the problem (0:45)

### On the slide

- **Original project:** PawPal+, a pet-care task planner
- Organizes recurring care tasks and daily schedules
- This extension adds source-grounded pet-care Q&A
- Goal: useful answers with traceable sources and clear limits

### Speaker notes

“PawPal+ began as a planner for pet owners: it represents owners, pets, and care tasks, sorts a schedule, and flags conflicts. For this project I added retrieval-augmented generation, or RAG. The assistant looks up relevant passages in a curated knowledge base before answering, so it can show where its guidance came from rather than responding from model knowledge alone.”

---

## Slide 2 — How information flows (0:55)

### On the slide

```text
Question + selected species
            ↓
Safety and scope checks
            ↓
Retrieve relevant, species-filtered passages
            ↓
Anthropic synthesis OR local extractive answer
            ↓
Cited response, limitation, or veterinary referral
            ↓
Owner reviews any optional schedule task
```

- Sources are curated by a human
- Automated tests check retrieval and answer behavior
- A human reviewer should check generated claims against citations

### Speaker notes

“The user asks through Streamlit and selects a species. The answer service first checks for recognized medical concerns, unsupported topics, and species conflicts. The retriever ranks local passages and filters by species. If an Anthropic key is configured, the model synthesizes from those passages; otherwise the app displays the retrieved text with citations. The existing scheduler stays separate, and the owner must explicitly submit any task. The complete system diagram is in `diagrams/rag_system.mmd`.”

---

## Slide 3 — Retrieval: from a small source set to custom sources (0:55)

### On the slide

- Bundled source: four reviewed ASPCA summaries
- Now combines bundled data with multiple local JSON files
- Custom paths are configured with `PAWPAL_KNOWLEDGE_BASE_PATHS`
- Species, topics, source metadata, and unique document IDs are validated
- Example file: `data/example_custom_pet_care.json`

### Speaker notes

“The original knowledge base was intentionally small. I extended the loader so it can combine it with multiple local JSON files, without changing the retrieval algorithm. That makes it possible to extend the collection with reviewed local material while preserving species filters and citation metadata. The committed example is explicitly marked as demonstration-only; it is not an authoritative pet-care source.”

---

## Slide 4 — Live demo: retrieve a custom passage (1:40)

### On the slide

1. Start the app with the example source:

   ```bash
   export PAWPAL_KNOWLEDGE_BASE_PATHS="data/example_custom_pet_care.json"
   unset ANTHROPIC_API_KEY
   python -m streamlit run app.py
   ```

2. Select **dog**.
3. Ask: **“dog enrichment snuffle mat activity”**
4. Inspect the returned excerpt and its source citation.
5. Try: **“dog exercise and play for mental stimulation”** to see a bundled-source result.

### Speaker notes / demo narration

“I’m running without an API key to show exactly what was retrieved, rather than imply that a model-generated paraphrase is a direct quote. The custom JSON file is appended to the bundled dataset. With dog selected, this query should return the demonstration snuffle-mat passage and identify its title, publisher, and URL. If I remove the custom-source setting and restart, the bundled documents do not cover snuffle mats, so the same query returns an insufficient-evidence response. The second question illustrates retrieval from a bundled ASPCA summary. Any custom content used for real care should first be replaced with material reviewed from a trustworthy source.”

### Demo fallback

If the UI is unavailable, the retrieval behavior can be shown from the repository root:

```bash
PAWPAL_KNOWLEDGE_BASE_PATHS=data/example_custom_pet_care.json python -c \
'from rag_retrieval import KnowledgeBase; print(KnowledgeBase().retrieve("dog enrichment snuffle mat activity", species="dog"))'
```

---

## Slide 5 — Reliability and responsible limits (0:55)

### On the slide

- Recognized health and emergency questions are referred to a veterinarian
- Unsupported species/topics and weak evidence are declined
- Generated sentences need citations and lexical overlap with cited passages
- Failed claim checks fall back to retrieved excerpts
- **58 automated tests pass**
- Limits: keyword guards and lexical overlap are not proof of safety or truth

### Speaker notes

“Reliability here means more than a plausible answer. The system declines many unsupported or recognized health-related requests before calling a model. Generated sentences must cite retrieved passages and have lexical overlap; otherwise the system returns the local excerpts. These safeguards are deliberately described as heuristics: a keyword screen can miss intent, and word overlap cannot prove that a source entails a claim. The 58 tests cover known cases, but do not validate live model quality.”

---

## Slide 6 — What I learned (0:50)

### On the slide

- Evidence quality and retrieval scope shape the answer
- Species context matters: a mismatch refusal may be correct behavior
- More documents improve coverage only when their content is trustworthy
- Tests catch regressions; human review checks meaning
- Next step: source review and evaluation with real, approved custom material

### Speaker notes

“The main lesson is that adding a model is only one part of building a useful AI feature. Retrieval determines what evidence is available, source quality determines what can be trusted, and evaluation has to check whether the response actually follows the evidence. I also learned to treat a refusal in context: when I asked about a cat while the UI was set to dog, the species guard was doing what it was designed to do. The next step is not simply adding more text; it is reviewing real sources and measuring whether they improve answers.”

---

## Portfolio artifact

**Code:** [github.com/swethanagopisetti/applied-ai-system-project](https://github.com/swethanagopisetti/applied-ai-system-project)

**What this project says about me as an AI engineer:** I aim to build AI features around evidence and user needs, not just model output. In PawPal+, I paired retrieval with citations, species and safety guardrails, local fallback behavior, and tests, while documenting where those protections are limited. Extending the knowledge base through reviewed local files also reflects my belief that maintainable data and honest evaluation are as important as generation.

---

## Preparation checklist

- Run `python -m pytest` before presenting.
- Start the app from the repository root and select **dog** for the custom-source question.
- Keep `ANTHROPIC_API_KEY` unset to demonstrate the extractive path and avoid live API use.
- If using the custom source, set `PAWPAL_KNOWLEDGE_BASE_PATHS` before starting Streamlit.
- Do not describe the example JSON as veterinary advice; it is a retrieval-format demonstration only.
