# CareerPath AI — 2-minute judge demo

## One-line pitch

CareerPath AI turns an unstructured student resume into an explainable career direction, a verified skill-gap plan, and inspectable proof of readiness.

## Demo sequence

1. Upload or paste a student resume. Explain that skill detection is local and the current prototype supports a curated skill vocabulary.
2. Complete the short skill check. This is the trust layer: CareerPath does not treat every keyword in a resume as proven ability.
3. Open **Career Match** and select a target role. Explain that every score is traceable to detected skills and role keywords.
4. Open **Skill Gap**. Point to strengths, priority gaps, and the next best move.
5. Open **Roadmap**. Show the month-by-month project outcomes, official-source certification guidance, and the clearly labelled prototype scope.
6. Open **Resume Coach**. Show that it checks for concrete resume evidence—projects, quantified impact and a portfolio link—rather than promising a hidden ATS score.
7. Finish in **Portfolio Lab**. The key differentiator is that CareerPath converts a recommendation into an inspectable capstone project, not just a list of courses.

## The memorable line

> Most career tools stop at “you should learn this.” CareerPath asks, “what evidence will prove you learned it?”

## Honest current scope

This MVP uses curated career data, regex skill detection, TF-IDF-assisted matching, local PDF text extraction, and session-state progress. It does not claim live job-market data, automated credential verification, or a production LLM system. Those are planned integrations, not current features.

## Likely judge questions

**Why not just use ChatGPT for career advice?**

CareerPath provides a repeatable workflow: evidence extraction, transparent matching, skill-gap prioritisation, a structured roadmap, skill checks, and portfolio proof. It is designed to make recommendations explainable and actionable.

**How do you avoid false claims from a resume?**

The MVP uses a knowledge check after detecting skills. It does not certify expertise; it prompts the student to validate foundations before presenting them as strengths.

**What makes this scalable?**

The current curated data can move to a taxonomy-backed backend, embedding-based matching, persistent user profiles, and verified external integrations without changing the student journey.

**What is the next technical step?**

Move matching, roadmap and progress data to FastAPI/PostgreSQL, then add taxonomy-backed roles and embeddings with a deterministic offline fallback.
