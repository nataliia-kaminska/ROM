# TODO: Diploma Thesis Enhancements (not currently in codebase)

## Section 2 & 3 (Technical & Architectural)
- [ ] **Formal Mathematical Model:** Need to define the recommendation problem as an optimization task or a multi-criteria decision making (MCDM) problem for Section 2.1.
- [ ] **UML Diagrams:** Need to generate Use Case, Class, and Sequence diagrams (not present in the project, but essential for a diploma).
- [ ] **Comparative Analysis of LLMs:** While the code supports Groq/Ollama, the diploma needs a more rigorous comparison of models for requirement extraction (e.g., GPT-4 vs Llama 3 vs Deterministic).
- [ ] **Security Analysis:** Deeper dive into JWT implementation and protection against XSS/CSRF (basic implementation exists, but needs "diploma-level" justification).
- [ ] **Database ER Diagram:** Need a visual representation of the relations between `researcher_profiles`, `opportunities`, `embeddings`, etc.

## Section 4 (Implementation & Testing)
- [ ] **Load Testing:** The codebase has unit tests, but a diploma often requires "stress/load testing" (e.g., using Locust or JMeter) to justify the choice of FastAPI/Redis.
- [ ] **User Feedback Evaluation:** A quantitative analysis of "precision/recall" for the recommendation engine based on some mock data.

## Section 5 (Economic / Occupational Safety - if required)
- [ ] **Economic efficiency calculation:** Estimating time saved by a researcher using the system vs manual search.
- [ ] **Occupational safety (БЖД):** Standard boilerplate section usually required in UA diplomas.

---
*Note: This list tracks what needs to be "invented" or "documented" for the diploma that isn't strictly necessary for the MVP software but is required by academic standards.*
