# PawPal+ Model Card and Responsible-AI Reflection

## System purpose

PawPal+ is a pet-care task planner with an optional retrieval-augmented question-answering feature. The assistant retrieves short, locally curated cat- and dog-care summaries and, when `ANTHROPIC_API_KEY` is configured, sends the question and retrieved passages to Anthropic to formulate a cited answer. Without a key, it displays the retrieved passages extractively. It is an informational aid, not a veterinary service.

## Limitations and potential biases

- The knowledge base is a small starter set of four paraphrased ASPCA passages about cat and dog grooming, scratching, exercise, and play. It is not comprehensive and represents only the sources and topics selected for it.
- Retrieval is lexical, not semantic. A minimum weighted relevance of 0.6 filters weak matches, with content tokens weighted fully and topic tags at 0.75. Species mentioned in the query are used as a filter when no species is selected; mixed-species questions and selected/query mismatches are declined. Synonyms and differently phrased questions may still be declined or retrieve incomplete passages.
- The displayed evidence-match percentage reflects lexical overlap with the top retrieved passage. It is not calibrated confidence, factual accuracy, or a probability that the answer is correct.
- Anthropic may produce unsupported or incomplete statements despite the prompt and checks. Each generated sentence must cite an in-range retrieved passage and pass a lexical-overlap check; a failed check falls back to local excerpts. Lexical overlap is only a heuristic and cannot prove that a claim is entailed by a source.
- Medical, urgent-care, supported-topic, and prompt-injection routing uses limited keyword and phrase checks. It can miss health or injection attempts and misclassify benign wording. Retrieved passages and questions are marked as untrusted in the model prompt, but this is not a complete prompt-injection defense.
- The app is currently English-only and includes species-specific source data for cats and dogs; other species are declined rather than given species-specific guidance.
- When a key is configured, the user's question and retrieved passage text are sent to Anthropic. Users should not include sensitive personal information.

## Misuse risks and mitigations

The main foreseeable misuse is treating an answer as veterinary diagnosis, treatment, or medication guidance. PawPal+ attempts to reduce this risk by routing recognized health or emergency questions to veterinary care before retrieval or model use, restricting topics and species, declining when retrieval finds no sufficiently relevant material, requiring citations and lexical claim overlap for model sentences, falling back to retrieved excerpts when that check fails, and labeling answers as general information rather than veterinary advice. These safeguards are incomplete and do not guarantee that all risky queries will be recognized or all claims will be grounded.

Prompt injection is another foreseeable risk when user questions or retrieved text contain instructions aimed at changing the model's behavior. Common user-side override phrases are declined, and the model prompt explicitly treats the question and retrieved passages as untrusted data. Phrase detection and prompting are defense-in-depth measures, not a guarantee against indirect or novel attacks.

Task scheduling is separate from answer generation. The assistant does not automatically create tasks; an owner must review and explicitly submit a task. This also means users must rely on their veterinarian's instructions for medical care tasks rather than using PawPal+ to create or alter treatment advice.

## Reliability testing and what surprised me

The automated suite covers scheduling, retrieval thresholds, species inference/filtering/mismatch handling, scope refusals, citations, lexical claim support, untrusted passage prompting, local fallback, provider errors, safety responses, and the Streamlit task-confirmation flow. In the latest run, 55 of 55 tests passed without a live Anthropic request. These tests establish behavior for known examples; they do not establish live model answer quality.

One surprising result was that a cat grooming question could receive dog-specific retrieved content when no species filter was explicitly selected. The service now infers an unambiguous species mentioned in the query and applies that filter, with regression tests for the cat grooming case. A separate per-sentence lexical claim-support check now catches some uncited or weakly supported model outputs. Neither change solves general synonym matching or proves semantic entailment.

The app also has an evidence-match display, but it should not be read as an AI confidence score. No calibrated confidence or aggregate answer-accuracy score has been measured.

## Human evaluation

No human review results for live Anthropic-generated responses have been recorded yet. The review log is in the README's **Testing summary → Reliability checks and human review** table. Before relying on model-generated responses, a reviewer should compare each answer claim with the cited passage, check the source, confirm no ungrounded medical advice appears, and record a pass/fail result with reviewer, date, and model. Mocked provider tests are not a substitute for this review.

## AI collaboration reflection

I used AI to brainstorm the RAG feature, implement and refine retrieval and answer handling, write tests, and improve project documentation. I checked proposed behavior against the code and tests rather than treating generated suggestions as automatically correct.

**Suggestion accepted:** AI recommended Retrieval-Augmented Generation as a suitable extension for PawPal+, because pet-care answers benefit from being grounded in sources. I chose to build that feature, beginning with curated material and retrieval, then adding answer generation and UI integration.

**Suggestion revised/rejected:** An early design suggestion expanded the project into a more complicated set of classes, including separate planning-constraint and daily-plan concepts. I kept the original core `Task`, `Pet`, `Owner`, and `Scheduler` structure instead. Those extra abstractions were not needed for the project's immediate scheduling behavior and would have increased complexity. I also chose a small local knowledge base and extractive no-key fallback rather than requiring a model API for every run, keeping setup and basic operation accessible.

## Intended use and non-goals

Use PawPal+ as a small demonstration of source-backed general pet-care information and deterministic task scheduling. Do not use it to diagnose health problems, choose treatments or medication, respond to emergencies, or replace a veterinarian. The system should not be treated as comprehensive, clinically validated, or reliably safe for unrestricted pet-care questions.
