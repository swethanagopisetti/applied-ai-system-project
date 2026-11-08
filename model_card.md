# PawPal+ Model Card and Responsible-AI Reflection

## System purpose

PawPal+ is a pet-care task planner with an optional retrieval-augmented question-answering feature. The assistant retrieves short, locally curated cat- and dog-care summaries and, when `ANTHROPIC_API_KEY` is configured, sends the question and retrieved passages to Anthropic to formulate a cited answer. Without a key, it displays the retrieved passages extractively. It is an informational aid, not a veterinary service.

## Limitations and potential biases

- The knowledge base is a small starter set of four paraphrased ASPCA passages about cat and dog grooming, scratching, exercise, and play. It is not comprehensive and represents only the sources and topics selected for it.
- Retrieval is lexical, not semantic. Basic token normalization helps with a few word forms, but synonyms and differently phrased questions may retrieve weak or irrelevant passages.
- The displayed evidence-match percentage reflects lexical overlap with the top retrieved passage. It is not calibrated confidence, factual accuracy, or a probability that the answer is correct.
- Anthropic may produce unsupported or incomplete statements despite the prompt and citation checks. The code checks citation numbers against the retrieved set, but does not verify that each claim follows from its citation.
- Medical and urgent-care routing is based on a limited list of keywords and phrases. It can miss health-related questions or misclassify benign ones. It is not a substitute for professional review.
- The app is currently English-only and includes species-specific source data for cats and dogs; other species may receive unfiltered or insufficiently relevant content.
- When a key is configured, the user's question and retrieved passage text are sent to Anthropic. Users should not include sensitive personal information.

## Misuse risks and mitigations

The main foreseeable misuse is treating an answer as veterinary diagnosis, treatment, or medication guidance. PawPal+ attempts to reduce this risk by routing recognized health or emergency questions to veterinary care before retrieval or model use, limiting model responses to supplied passages, displaying citations, declining when retrieval finds no sufficiently relevant material, and labeling answers as general information rather than veterinary advice. These safeguards are incomplete and do not guarantee that all risky queries will be recognized or all claims will be grounded.

Task scheduling is separate from answer generation. The assistant does not automatically create tasks; an owner must review and explicitly submit a task. This also means users must rely on their veterinarian's instructions for medical care tasks rather than using PawPal+ to create or alter treatment advice.

## Reliability testing and what surprised me

The automated suite covers scheduling, retrieval, species filtering, citations, local fallback, provider errors, safety responses, and the Streamlit task-confirmation flow. On 2026-11-08, 40 of 40 tests passed without an API key or live Anthropic request. These tests establish behavior for known examples; they do not establish live model answer quality.

One surprising result was that the query “How often should I brush a cat?” initially tied cat grooming with unrelated cat enrichment. Simple lexical overlap gave both documents similar scores because the query shared few exact words with the grooming summary. Adding a small stop-word list and basic `-ing` normalization made the expected grooming document rank first in the evaluation case. This improved those examples but does not solve general synonym or intent matching.

The app also has an evidence-match display, but it should not be read as an AI confidence score. No calibrated confidence or aggregate answer-accuracy score has been measured.

## Human evaluation

No human review results for live Anthropic-generated responses have been recorded yet. The review log is in the README's **Testing summary → Reliability checks and human review** table. Before relying on model-generated responses, a reviewer should compare each answer claim with the cited passage, check the source, confirm no ungrounded medical advice appears, and record a pass/fail result with reviewer, date, and model. Mocked provider tests are not a substitute for this review.

## AI collaboration reflection

I used AI to brainstorm the RAG feature, implement and refine retrieval and answer handling, write tests, and improve project documentation. I checked proposed behavior against the code and tests rather than treating generated suggestions as automatically correct.

**Suggestion accepted:** AI recommended Retrieval-Augmented Generation as a suitable extension for PawPal+, because pet-care answers benefit from being grounded in sources. I chose to build that feature, beginning with curated material and retrieval, then adding answer generation and UI integration.

**Suggestion revised/rejected:** An early design suggestion expanded the project into a more complicated set of classes, including separate planning-constraint and daily-plan concepts. I kept the original core `Task`, `Pet`, `Owner`, and `Scheduler` structure instead. Those extra abstractions were not needed for the project's immediate scheduling behavior and would have increased complexity. I also chose a small local knowledge base and extractive no-key fallback rather than requiring a model API for every run, keeping setup and basic operation accessible.

## Intended use and non-goals

Use PawPal+ as a small demonstration of source-backed general pet-care information and deterministic task scheduling. Do not use it to diagnose health problems, choose treatments or medication, respond to emergencies, or replace a veterinarian. The system should not be treated as comprehensive, clinically validated, or reliably safe for unrestricted pet-care questions.
