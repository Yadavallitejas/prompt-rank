PromptRank
One-line: PromptRank is a competitive platform (Codeforces-style) where contestants write system prompts to solve hidden challenges; submissions are auto-evaluated across correctness, robustness, efficiency and consistency and players earn dynamic ELO-style ratings.
Audience: Competitive prompt engineers, hiring teams, researchers, recruiters, and companies that want measurable LLM-control skill.
________________________________________
1. Objective & Vision
Objective: Build the first credible, defensible, and scalable competitive platform that measures control over LLMs (not raw creativity). Rankings must be hard to game and correlate with real-world ability to craft reliable system prompts.
Vision (3 years): Standards-based credential for prompt engineering; enterprise hiring integration; competitive leagues and tournaments.
________________________________________
2. Key Principles (non-negotiable)
1.	Deterministic evaluation where possible — runs use seeded randomness and fixed model settings.
2.	Hidden testcases & repeated sampling — no overfitting by trial-and-error.
3.	Multi-judge evaluation — use an ensemble of evaluators and rule-based checks.
4.	Rate-limited, versioned submissions — behave like a true contest judge.
5.	Usability-first contest UX — feel like a contest (not ChatGPT).
6.	Scoring must be defensible & explainable — every score component visible in report.
________________________________________
3. Target Users & Personas
•	Competitive Prompt Coder (Primary): 18–35, wants leaderboard recognition and to improve; cares about rating math and contest schedule.
•	Recruiter / Hiring Manager: Seeks validated skill signals for hiring.
•	Enterprise Ops / LLM Ops Engineer: Wants benchmark & stress tests for internal models.
•	Researcher / Benchmarker: Wants control and reproducibility for experiments.
________________________________________
4. Success Metrics (KPIs)
•	Core product metrics
o	Monthly Active Competitors (MAC): target 5k in Year 1.
o	Average submissions per contest: ≥3.
o	Retention (30-day): ≥25%.
o	Contest NPS: ≥45.
•	Quality metrics
o	% of submissions flagged for cheating: <1% (after mitigations).
o	Correlation between platform ratings and recruiter-blind skill assessment >0.6 (pilot).
•	Financial
o	Enterprise paid customers: 10 by month 12.
o	ARPU (enterprise): $3k/month.
________________________________________
5. Problem Scenarios & User Stories
•	Contestant: “I want to enter a timed contest, submit a prompt, and climb the leaderboard based on robust evaluation.”
•	Recruiter: “Show me a candidate’s recent contest history, strengths (extraction, reasoning, efficiency).”
•	Organizer: “Create a live contest, pick problems, freeze settings, publish results and ELO changes.”
________________________________________
6. MVP — Scope & Features
MVP Goals: validate judging, scoring, and anti-cheat. Keep scope minimal but rigorous.
Must-haves (MVP)
1.	Contest platform
o	Problem page (statement + constraints + output schema)
o	Monaco prompt editor (system prompt only; optional context inputs allowed by problem)
o	Fixed single model option (e.g., GPT-4-like API settings) with locked settings (temperature, top_p, max_tokens)
o	Submission versioning & rate limiting (e.g., 3 submissions per problem per contest)
2.	Evaluation harness
o	Hidden dataset (≥20 testcases per problem)
o	Repeated-run sampling (N=5 runs per testcase)
o	Deterministic seed injection for model prompts where supported
o	Rule-based parser + evaluator models (ensemble of 3) + aggregator
3.	Scoring
o	Multi-metric scorecard + aggregated final score
o	ELO-style rating update after contest
4.	Leaderboard
o	Live leaderboard during contest (with final ranking)
o	User profile + recent submissions + score breakdown
5.	Anti-cheat
o	Hidden tests, randomized order, rate-limits
o	Logging and anomaly detection (submission fingerprints)
6.	Admin tools
o	Problem uploader
o	Hidden testcase management
o	Run logs + sample outputs viewer
Nice-to-haves (post-MVP)
•	Multi-model selection & cost-weighted scoring
•	Private contests & enterprise integrations (SSO)
•	Replay/compare submissions feature
•	Contest spectator mode & contest replays
•	Challenge editor with automated test generator
________________________________________
7. Scoring & Evaluation (Detailed)
Core idea: Score across orthogonal dimensions, each defensible, aggregated to final points used by rating engine.
Metrics & weights (example MVP)
•	Accuracy (A) — correctness wrt ground truth; range 0–1. Weight: 40%
•	Consistency (C) — how stable outputs are across N runs; 0–1. Weight: 20%
•	Format Compliance (F) — strict adherence to schema (JSON keys, types). Weight: 15%
•	Token Efficiency (T) — normalized (lower better). Weight: 10%
•	Latency (L) — normalized response time. Weight: 5%
•	Robustness (R) — correctness on adversarial/noisy inputs (holdout). Weight: 10%
Final Score (0–100):
Final = 100 × (0.40×A + 0.20×C + 0.15×F + 0.10×(1−T_norm) + 0.05×(1−L_norm) + 0.10×R)
(Normalization: T_norm and L_norm scaled 0–1 where 1 = worst.)
Repeated runs & aggregation
•	For each testcase, run the model N = 5 times (configurable).
•	Per-testcase accuracy = proportion of runs that pass.
•	Consistency measured via sample entropy or Jaccard similarity across runs.
ELO-style rating
•	Use modified ELO where expected score is computed against contest average or distribution.
•	Rating delta proportional to (ActualScore − ExpectedScore). Use K factor adjustable (e.g., K=20 for new players, 10 for established).
•	Optionally implement a contest “placement” approach: compute matchups pairwise with all participants to derive expected vs actual.
Explainability
•	Generate per-submission report: per-testcase pass/fail, sample outputs, failure categories (format error, wrong field, hallucination), token count, response times.
________________________________________
8. Anti-Gaming & Security
Threat model: brute-force prompting using many submissions, leaking testcases, RAG/Tooling to fetch hidden answers, automated adversarial submissions.
Mitigations
1.	Submission rate-limits (e.g., 3 per hour per problem; contest configurable).
2.	Hidden testcases & test rotation — change per contest; keep seed unseen.
3.	Randomized input order & variable seeds.
4.	Disable tool calls / external browsing in judged environment; sandbox model calls to not allow external RAG.
5.	Behavioral analysis / anomaly detection — flag unusually similar submissions, improbable success patterns, token & timing anomalies.
6.	IP & account restrictions — throttle, require identity checks for ranked tiers.
7.	Logging & audit storage — preserve model outputs, full request/response for audits.
8.	Plagiarism detection — check prompt similarity across users and public repos.
________________________________________
9. System Architecture (High level)
Components
•	Frontend: Next.js + TypeScript; Monaco editor; React hooks for live leaderboard.
•	Backend API: FastAPI (Python) for request handling and judge orchestration.
•	Execution Workers: Dockerized workers (K8s) that run prompt evaluation in sandbox; manage LLM API calls.
•	Queue: Redis + Celery for task scheduling.
•	DB: PostgreSQL (primary) + Timescale/Influx for metrics if needed.
•	Cache & state: Redis for ephemeral contest state.
•	Storage: S3-compatible for logs, sample outputs.
•	Analytics: Prometheus + Grafana.
•	Auth: JWT + optional SSO (enterprise).
•	CI/CD: GitHub Actions; Docker images pushed to registry.
Security sandboxing
•	Workers run minimal privileges, network egress blocked (only to allowed LLM APIs).
•	Secrets stored in vault (HashiCorp / cloud KMS).
________________________________________
10. Data Model (Core tables — simplified)
•	users: id, username, email, hashed_password, rating, role, created_at
•	contests: id, name, type (live/virtual), start_at, end_at, settings, created_by
•	problems: id, title, statement, schema, constraints, public (bool), author_id
•	testcases: id, problem_id, input_blob (hidden), expected_output_blob (hidden), tags
•	submissions: id, user_id, problem_id, contest_id, prompt_text, version, status, final_score, metrics_json, created_at
•	runs: id, submission_id, testcase_id, run_index, output_blob, passed_bool, tokens_used, latency
•	ratings_history: id, user_id, contest_id, before_rating, after_rating, delta
________________________________________
11. UX / Flow (Contestant)
1.	Landing: upcoming contests + leaderboards + profile.
2.	Join contest: click, accept rules, see limited problem set.
3.	Open problem: read spec, download sample inputs (non-eval).
4.	Write system prompt in Monaco editor (no chatting). Optionally add fixed “context” or “tool instructions” if permitted.
5.	Submit: confirmation modal shows submission cost (if any) and remaining attempts.
6.	Wait: live status shows “queued → running → evaluated”. Minimal latency target: evaluation per submission < 30s * N_runs.
7.	Results: Scorecard + report + leaderboard update. Historical submissions visible but not testcases.
________________________________________
12. Example Problem (Fully Specified — for PRD)
Title: Invoice Extractor (Competitive)
Statement: Given messy invoice-like texts (typos, mixed languages, missing units), return JSON with fields: vendor_name (string), invoice_date (ISO date), total_amount (float, INR), items (array of {name, qty, unit_price}), tax_rate (float), currency (enum: INR, USD, EUR).
Constraints: Strict JSON, exact keys, no extra fields. Any date format acceptable but must be convertible to ISO; if missing, return null.
Hidden testcases: 20 cases including adversarial (OCR errors, swapped lines, currency symbols, missing units, multilingual labels).
Scoring: accuracy on fields + schema & consistency. Run N=5.
________________________________________
13. Operational Considerations
•	Cost: LLM API calls are the major cost. Minimize by:
o	Using smaller fixed model for MVP (cheaper) but defensible performance.
o	Caching repeated prompts for identical requests.
o	Limiting N to 5 initially.
•	Throughput planning: Expect heavy traffic during contests; use autoscaling workers and rate limits.
•	Data retention & storage: Keep submission logs for at least 90 days for audits; longer for enterprise customers.
•	Privacy: Users may submit proprietary prompts; give option for “private contest” and enterprise data agreements.
________________________________________
14. Compliance & Legal
•	User content: Terms of Service must allow storing prompts and model outputs for evaluation & anti-cheat.
•	Data handling: Comply with GDPR for EU users; include data deletion workflow.
•	Intellectual Property: Clarify ownership of prompts and outputs—contestants should retain IP unless agreed otherwise.
________________________________________
15. Roadmap & Timeline (16-week, concrete — assume small team)
Team assumption: 1 PM, 2 Backend devs, 1 Frontend, 1 ML/LLM engineer, 1 SRE/DevOps.
Week 0 (planning) — finalize problem + scoring rubric + infra budget.
Weeks 1–4 (Core infra & judge)
•	FastAPI backend skeleton + DB schema.
•	Worker prototype: run single prompt against fixed model and store outputs.
•	Implement submission pipeline + Redis queue.
Weeks 5–8 (Evaluation & scoring)
•	Hidden testcase runner (N=5), deterministic seed injection.
•	Implement metrics: accuracy, format compliance, consistency calculation.
•	Build submission report generator.
Weeks 9–11 (Frontend & UX)
•	Next.js UI, Monaco editor, problem pages, live leaderboard.
•	Submission flow & versioning UI.
Weeks 12–13 (Anti-cheat & Admin)
•	Rate-limits, randomized testcase ordering, logging & anomaly detection.
•	Admin console for problems and testcases.
Weeks 14–15 (Polish & pilot)
•	Sample first contest with internal testers.
•	Fix performance, debugging.
Week 16 (Beta launch)
•	Invite 200–500 early users; measure metrics, iterate.
(Deliverables per milestone: code repos, deployed staging, test dataset, scoring docs, admin UI, pilot contest results.)
________________________________________
16. Risks, Assumptions & Mitigations (Pragmatic)
1.	Assumption: LLM outputs can be reliably scored.
Risk: Subjectivity and false positives.
Mitigation: Combine rule-based checks + multi-evaluator ensemble + human audit for edge cases.
2.	Assumption: Users won’t brute-force prompts.
Risk: Brute-force or learned leaks.
Mitigation: rate-limits, protected testcases, submission cost (soft).
3.	Assumption: Cost of LLM API is manageable.
Risk: Costs spike with usage.
Mitigation: Start with smaller models, capped evaluation runs, enterprise cost recovery.
4.	Assumption: Ratings reflect real skill.
Risk: Ratings gamed by narrow optimization.
Mitigation: Diverse problems, rotating testcases, cross-problem evaluation, tournament modes.
5.	Assumption: Users will accept platform rules.
Risk: Pushback on private prompts, IP concerns.
Mitigation: Clear ToS, private contest options, enterprise agreements.
________________________________________
17. Monitoring & Analytics
•	Track submission latency, queue depth, worker error rates.
•	Score distribution per contest; top-10 vs median.
•	Churn & retention per cohort.
•	Fraud signals: sudden rating jumps, identical prompts from multiple accounts.
________________________________________
18. Business Model
•	Freemium: free access to practice problems and public contests.
•	Pro subscription: advanced analytics, unlimited practice submissions, private history.
•	Enterprise: private contest orchestration, SSO, API access, team management, SLA.
•	Events & Tournaments: sponsored contests and paid tournament entries.
Pricing suggestion: Pro ₹499/month; Enterprise custom (≥$3k/month depending on scale).
________________________________________
19. Developer APIs & Integrations (sample)
Endpoints (examples)
•	POST /api/v1/submissions — submit prompt (body: user_id, problem_id, prompt_text)
•	GET /api/v1/submissions/{id}/report — get evaluation report
•	POST /api/v1/contests/{id}/start — admin starts contest
•	GET /api/v1/leaderboard?contest_id=... — get leaderboard
Webhook: on contest end send ranking deltas to enterprise systems.
________________________________________
20. Acceptance Criteria (for MVP)
•	Platform executes submissions with N=5 sampling and returns report ≤ 2 minutes for 95% of submissions.
•	Hidden dataset scoring is deterministic and reproducible (within defined tolerance).
•	Leaderboard updates correctly and ELO recalculation works for contests with up to 500 participants.
•	Anti-cheat rate-limits and randomization active.
•	Pilot contest run completed with ≥50 participants and usability feedback collected.
________________________________________
21. Example Admin Checklist (pre-contest)
•	Problem statement locked and reviewed.
•	Hidden testcases uploaded (≥20).
•	Ensemble evaluator models selected and configured.
•	Contest settings frozen (seeds, allowed models, submission limits).
•	Monitoring + alerting enabled.
________________________________________
22. Next Tactical Steps (what you should do now)
1.	Design the first official contest problem (one I'd create for you as pilot — I can produce it now).
2.	Choose the initial model & budget constraint (cheap small LLM vs powerful one). I recommend starting with a smaller, deterministic model to control cost and focus on scoring mechanics.
3.	Prepare a 20-case hidden dataset for that problem (I can draft 20 inputs).
4.	Build evaluation harness prototype (1 engineer can run a minimal loop in ~2 weeks).
5.	Run internal pilot with 10–20 testers to validate scoring.
________________________________________
23. Hard Truths / Challenges (no sugarcoating)
•	Scoring is the product. If scoring is weak, the platform is meaningless — investing in robust evaluation is mandatory.
•	Costs are real. Frequent sampling across many submissions multiplies API spend — expect non-trivial running costs.
•	Users will game the system. Plan for persistent anti-cheat investments.
•	Correlation to hiring skill is non-trivial. You’ll need enterprise pilots to validate that high-rated users are actually better hires.
________________________________________
24. Deliverables I can produce for you right now (pick any — I will deliver immediately)
•	Full first contest spec with 20 hidden testcases and sample expected outputs.
•	Complete scoring implementation pseudo-code + reproducible scripts (Python).
•	Database schema SQL and API contract spec (OpenAPI).
•	ELO/rating algorithm implementation (Python code).
•	Mockups for Contest UI (Figma-ready layout descriptions).
•	Anti-cheat detection rule set + anomaly detection thresholds.

