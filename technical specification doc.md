PromptRank
Technical Specification (Finalized Architecture)
1. Architecture Decision
Chosen Stack
Layer	Technology
API Backend	FastAPI (Python, async)
Workers	Celery + Redis
Database	PostgreSQL
Cache	Redis
Frontend	Next.js (React + TypeScript)
Infra	AWS (ECS + RDS + ElastiCache)
Monitoring	Prometheus + Grafana + Sentry
LLM Abstraction	Custom Provider Layer
Containerization	Docker
Orchestration	ECS (MVP) → EKS (scale)

This gives:

High async throughput

Python-native LLM evaluation

Reliable job queues

Clean scaling path

Low DevOps overhead initially

2. System Architecture
High-Level Flow
4
Services Overview
1️⃣ API Service (FastAPI)

Responsibilities:

Auth (JWT)

Contest management

Submission intake

Leaderboard queries

Admin panel endpoints

Stateless. Horizontally scalable.

2️⃣ Evaluation Worker Service (Celery Workers)

Responsibilities:

Fetch submission

Retrieve hidden testcases

Run LLM N times per testcase

Collect outputs

Compute metrics

Store detailed run logs

Runs in isolated containers.

3️⃣ Scoring Engine

Runs inside worker after evaluation:

Accuracy calculation

Format validation

Consistency score

Token efficiency normalization

Final score computation

4️⃣ Rating Engine

Runs after contest ends.

Modified ELO

Rating delta stored

History persisted

5️⃣ Leaderboard Service

Redis-backed sorted set

Real-time updates

Cached ranking responses

3. LLM Abstraction Layer (Critical Component)

You must NEVER hardcode provider logic.

Interface Design
class LLMProvider:
    async def run(
        self,
        system_prompt: str,
        user_input: str,
        temperature: float,
        seed: int,
        max_tokens: int
    ) -> LLMResponse:
        pass
LLMResponse Structure
class LLMResponse:
    content: str
    tokens_used: int
    latency_ms: int

This allows:

Swapping providers

Multi-model competitions later

Cost accounting per model

Deterministic seed injection

4. Evaluation Engine Specification

This is the heart.

Execution Algorithm
for testcase in hidden_testcases:
    results = []
    for i in range(N):
        response = LLM.run(
            system_prompt=submission.prompt,
            user_input=testcase.input,
            temperature=FIXED_TEMP,
            seed=base_seed + i
        )
        results.append(response)

    evaluate(results, testcase.expected_output)
N (Sampling Count)

MVP: N = 5
Future: adaptive N (higher for borderline scores)

Metrics Calculation
1. Accuracy (A)

Compare output JSON fields to expected.

Numeric tolerance allowed (±1% configurable).

Partial scoring per field.

2. Format Compliance (F)

Strict JSON parse.

Schema validation.

No extra keys.

No missing keys.

Binary per run → aggregated.

3. Consistency (C)

Measured via:

Pass rate variance across N runs.

Output similarity (Jaccard similarity or structural hash).

High divergence = lower consistency.

4. Robustness (R)

Special subset of adversarial testcases:

Noise injection

Random token shuffle

Minor language shift

Separate scoring.

5. Token Efficiency (T)

Normalized score:

T_norm = (tokens_used - min_tokens) / (max_tokens - min_tokens)

Lower tokens = higher score.

6. Latency (L)

Average latency per run.

Normalized.

Final Score Formula
FINAL =
100 * (
    0.40*A +
    0.20*C +
    0.15*F +
    0.10*(1 - T_norm) +
    0.05*(1 - L_norm) +
    0.10*R
)

Stored as float(2 decimal precision).

5. Rating System (Competitive Core)
Modified ELO

After contest:

expected_score = 1 / (1 + 10 ** ((opponent_rating - user_rating)/400))
rating_delta = K * (actual_score - expected_score)

K-factor:

New users: 40

Established users: 20

High-rated: 10

Store rating history per contest.

6. Data Model (Finalized)
users

id (UUID)

username (unique)

email

password_hash

rating (int)

created_at

contests

id

name

start_time

end_time

status (scheduled, active, ended)

submission_limit

allowed_model

temperature

seed_base

problems

id

title

statement

schema_json

time_limit_sec

scoring_config_json

testcases (hidden)

id

problem_id

input_blob

expected_output_blob

is_adversarial (bool)

submissions

id

user_id

contest_id

problem_id

prompt_text

status (queued, running, evaluated)

final_score

metrics_json

created_at

runs

id

submission_id

testcase_id

run_index

output_blob

tokens_used

latency_ms

passed_bool

rating_history

id

user_id

contest_id

rating_before

rating_after

delta

7. API Specification
Auth

POST /auth/register
POST /auth/login

Contest

GET /contests
GET /contests/{id}
GET /contests/{id}/leaderboard

Submission

POST /submissions
GET /submissions/{id}
GET /submissions/{id}/report

Admin

POST /admin/problem
POST /admin/contest
POST /admin/testcases

JWT-protected.

8. Infrastructure Layout (AWS)
ECS Cluster

Services:

api-service

worker-service

Auto scaling:

CPU > 70%

Queue depth > threshold

RDS PostgreSQL

Multi-AZ enabled

Daily backups

ElastiCache Redis

Separate instance for queue + leaderboard cache

S3

Store submission logs

Store raw LLM outputs

9. Security Model
Worker Isolation

No internet except LLM provider endpoint

No file system writes outside container

No shell execution

Prompt Injection Mitigation

Disallow tool calls

Fixed model parameters

Strip system prompt override attempts

Rate Limiting

3 submissions per problem per contest

30 per day global cap (configurable)

10. Performance Targets
Metric	Target
Submission queue wait	< 15s
Evaluation completion	< 2 min
Leaderboard update	< 1s
Worker crash rate	< 1%
11. Cost Estimation Model

If:

1 contest

1000 users

3 submissions each

20 testcases

N=5 runs

Total model calls:

1000 × 3 × 20 × 5 = 300,000 calls

This is your main scaling constraint.

You MUST:

Cap submissions

Possibly reduce N dynamically

Use mid-tier model for MVP

12. Scalability Roadmap

Phase 1:
Single region ECS

Phase 2:
Move workers to EKS
Horizontal scaling

Phase 3:
Multi-region contest replication
Read replicas

13. Engineering Risks

LLM API outage during contest
→ Pre-contest warmup + fallback model

Queue overload
→ Auto-scale workers

Scoring exploit discovered
→ Patch scoring config per contest

Cost explosion
→ Hard budget cap per contest