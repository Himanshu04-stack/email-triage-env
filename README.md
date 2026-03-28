# Email Triage OpenEnv

An **OpenEnv-compliant environment** that simulates real-world email triage for a SaaS company support team.

An AI agent receives incoming support emails and must classify them by **priority**, **category**, and **assigned team** — exactly as a human support manager would do every day.

---

## Environment Description & Motivation

Email triage is one of the most common, high-volume tasks in any company's support operation. A typical support team receives hundreds of emails daily and must:
1. Decide how urgent each email is (urgent → normal → low)
2. Identify what the email is about (bug, billing issue, feature request, spam, etc.)
3. Route it to the right team (engineering, billing, support, sales)

Automating this accurately with AI agents has massive real-world impact — it reduces response time, prevents critical issues from being missed, and lets human agents focus on complex problems.

This environment gives AI agents a realistic simulation of this task, with 12 hand-crafted emails spanning all priority levels and categories, and a meaningful reward signal that rewards partial progress.

---

## Action Space

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `priority` | string | `urgent`, `normal`, `low` | How urgently this email needs attention |
| `category` | string | `bug`, `feature_request`, `billing`, `spam`, `support`, `other` | Topic category |
| `assigned_team` | string | `engineering`, `billing`, `support`, `sales`, `ignore` | Which team should handle it |
| `summary` | string | Any text | One-sentence summary of the key issue (scored in task_hard) |

---

## Observation Space

| Field | Type | Description |
|-------|------|-------------|
| `email_id` | string | Unique email identifier |
| `subject` | string | Email subject line |
| `body` | string | Full email body |
| `sender` | string | Sender's email address |
| `sender_domain` | string | Domain of the sender |
| `timestamp` | string | ISO 8601 timestamp |
| `has_attachment` | boolean | Whether the email has attachments |
| `thread_length` | integer | Number of messages in the email thread |
| `task_id` | string | Current active task |
| `task_description` | string | Natural language description of what the agent must do |

---

## Tasks

### Task 1 — Easy (`task_easy`)
**Goal:** Classify the email priority only (`urgent` / `normal` / `low`).

Reward: `1.0` for correct priority, `0.2` for adjacent error (e.g., urgent predicted as normal), `0.0` for max error (urgent predicted as low).

Target baseline score: **0.70**

### Task 2 — Medium (`task_medium`)
**Goal:** Classify both priority and category correctly.

Reward: `priority_score × 0.5 + category_score × 0.5`

Target baseline score: **0.50**

### Task 3 — Hard (`task_hard`)
**Goal:** Full triage — priority (40%) + category (30%) + assigned team (20%) + summary keyword coverage (10%).

Penalty: summaries over 300 characters are penalized (−20%) to discourage padding.

Target baseline score: **0.35**

---

## Reward Function

The reward is always in `[0.0, 1.0]` and provides partial progress signals throughout the episode (not just at the end).

- **Partial credit for priority:** adjacent errors (urgent vs normal, or normal vs low) score 0.2, maximum errors score 0.0
- **Summary scoring:** keyword coverage — how many key terms from the ground truth appear in the summary
- **Penalty:** excessively long summaries are penalized to discourage padding behavior

---

## Episode Structure

Each episode consists of **6 emails** sampled from the dataset (shuffled by seed for reproducibility). The agent receives one email per step, submits a triage action, and receives a reward. The episode ends after all 6 emails are triaged.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/reset` | Start a new episode. Body: `{"task_id": "task_easy", "seed": 42}` |
| `POST` | `/step` | Submit a triage action. Body: `{"priority": "...", "category": "...", "assigned_team": "...", "summary": "..."}` |
| `GET` | `/state` | Get current environment state |
| `GET` | `/tasks` | List all tasks and the full action schema |
| `POST` | `/grader` | Score a specific action against a specific email |
| `POST` | `/baseline` | Run the full baseline inference script |
| `GET` | `/health` | Health check (returns 200) |

---

## Setup Instructions

### Local Development

```bash
# Clone / download the files
cd email_triage_env

# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py

# Server runs at http://localhost:7860
```

### Run Baseline

```bash
# Without OpenAI API key (rule-based fallback)
python baseline.py

# With OpenAI API key
export OPENAI_API_KEY=sk-your-key-here
python baseline.py
```

### Docker

```bash
docker build -t email-triage-env .
docker run -p 7860:7860 email-triage-env
```

### Example API Usage

```python
import requests

BASE = "http://localhost:7860"

# Reset for medium task
obs = requests.post(f"{BASE}/reset", json={"task_id": "task_medium", "seed": 42}).json()
print(obs["observation"]["subject"])

# Submit a triage action
result = requests.post(f"{BASE}/step", json={
    "priority": "urgent",
    "category": "bug",
    "assigned_team": "engineering",
    "summary": "Production payment service is returning 500 errors affecting all customers."
}).json()
print(f"Reward: {result['reward']['value']}")
```

---

## Baseline Scores

Run with `gpt-3.5-turbo` (temperature=0) and rule-based fallback:

| Task | Score |
|------|-------|
| task_easy | 0.72 |
| task_medium | 0.51 |
| task_hard | 0.38 |
| **Overall** | **0.54** |

---

## Pre-Submission Checklist

- [x] HF Space deploys and responds to `/reset`
- [x] OpenEnv spec compliant: `step()`, `reset()`, `state()`, `openenv.yaml`
- [x] 3 tasks with graders (easy → medium → hard)
- [x] Meaningful reward with partial progress signals
- [x] Baseline inference script with reproducible scores
- [x] Dockerfile builds and runs
- [x] `/baseline`, `/grader`, `/tasks` endpoints exposed
- [x] README with full documentation
