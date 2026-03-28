"""
Baseline inference script for Email Triage OpenEnv.
Uses OpenAI API to run a model against all 3 tasks and produce reproducible scores.

Usage:
    export OPENAI_API_KEY=your_key_here
    python baseline.py
"""

import os
import json
import time
import requests
from typing import Optional

BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:7860")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL = "gpt-3.5-turbo"

SYSTEM_PROMPT = """You are an expert email triage assistant. 
Your job is to classify incoming emails for a SaaS company support team.

You must respond with ONLY a valid JSON object — no explanation, no markdown, just JSON.

JSON format:
{
  "priority": "urgent" | "normal" | "low",
  "category": "bug" | "feature_request" | "billing" | "spam" | "support" | "other",
  "assigned_team": "engineering" | "billing" | "support" | "sales" | "ignore",
  "summary": "One sentence describing the key issue"
}

Priority rules:
- urgent: production down, security issue, revenue impact, user locked out with deadline
- normal: billing disputes, account issues, general bugs, sales inquiries
- low: feature requests, how-to questions, spam

Category rules:
- bug: technical errors, broken functionality, security vulnerabilities
- feature_request: requests for new features or improvements
- billing: invoices, refunds, payment issues, subscription questions
- spam: unsolicited promotional or scam emails
- support: how-to questions, account access, general help
- other: sales, partnerships, press, anything else

Team rules:
- engineering: bugs, feature requests, technical issues
- billing: payment, invoices, refunds, subscriptions
- support: user help, account access, how-to
- sales: upgrades, new business, partnerships
- ignore: spam"""


def call_openai(email_obs: dict) -> Optional[dict]:
    """Call OpenAI API to get a triage decision for an email."""
    if not OPENAI_API_KEY:
        # Return a simple rule-based baseline if no API key
        return rule_based_triage(email_obs)

    user_msg = f"""Please triage this email:

Subject: {email_obs['subject']}
From: {email_obs['sender']}
Body: {email_obs['body']}
Has Attachment: {email_obs['has_attachment']}
Thread Length: {email_obs['thread_length']}

Task: {email_obs['task_description']}"""

    try:
        import urllib.request
        payload = json.dumps({
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg}
            ],
            "temperature": 0.0,
            "max_tokens": 200
        }).encode()

        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            content = data["choices"][0]["message"]["content"].strip()
            # Strip markdown if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content)
    except Exception as e:
        print(f"  OpenAI call failed: {e}, using rule-based fallback")
        return rule_based_triage(email_obs)


def rule_based_triage(email_obs: dict) -> dict:
    """Simple rule-based baseline (no API key needed) — used as fallback."""
    subject = email_obs.get("subject", "").lower()
    body = email_obs.get("body", "").lower()
    sender_domain = email_obs.get("sender_domain", "").lower()
    text = subject + " " + body

    # Spam detection
    spam_signals = ["win $", "click here", "million dollar", "free prize", "act now"]
    if any(s in text for s in spam_signals) or sender_domain in ["free-prize.xyz", "totally-not-scam.xyz"]:
        return {"priority": "low", "category": "spam", "assigned_team": "ignore", "summary": "Spam email, no action needed."}

    # Priority detection
    urgent_signals = ["urgent", "production down", "500 error", "locked out", "security", "vulnerability", "revenue", "deadline", "rate limit"]
    priority = "urgent" if any(s in text for s in urgent_signals) else "normal"

    low_signals = ["feature request", "dark mode", "suggestion", "would be nice", "data export", "how do i", "cannot figure"]
    if any(s in text for s in low_signals):
        priority = "low"

    # Category detection
    if any(s in text for s in ["error", "bug", "down", "broken", "not working", "vulnerability", "xss", "rate limit"]):
        category = "bug"
        team = "engineering"
    elif any(s in text for s in ["feature", "dark mode", "suggestion", "export", "would be"]):
        category = "feature_request"
        team = "engineering"
    elif any(s in text for s in ["invoice", "refund", "billing", "charge", "payment", "subscription"]):
        category = "billing"
        team = "billing"
    elif any(s in text for s in ["upgrade", "enterprise", "plan", "partnership", "reseller", "demo", "quote"]):
        category = "other"
        team = "sales"
    elif any(s in text for s in ["locked out", "cannot login", "password", "how do i", "how to"]):
        category = "support"
        team = "support"
    else:
        category = "support"
        team = "support"

    # Generate simple summary
    summary = f"{email_obs.get('subject', 'No subject')} - requires {team} team attention."

    return {"priority": priority, "category": category, "assigned_team": team, "summary": summary}


def run_task(task_id: str) -> float:
    """Run baseline agent on a single task, return average score."""
    print(f"\n{'='*50}")
    print(f"Running task: {task_id}")
    print(f"{'='*50}")

    # Reset environment
    resp = requests.post(f"{BASE_URL}/reset", json={"task_id": task_id, "seed": 42})
    if resp.status_code != 200:
        print(f"  ERROR: reset failed: {resp.text}")
        return 0.0

    data = resp.json()
    obs = data["observation"]
    scores = []
    step_num = 0

    while True:
        if obs.get("email_id") == "done" or obs.get("body") == "Episode complete.":
            break

        step_num += 1
        print(f"\n  Email {step_num}: {obs['subject'][:60]}...")

        # Get action from model
        action = call_openai(obs)
        if action is None:
            action = {"priority": "normal", "category": "support", "assigned_team": "support", "summary": ""}

        print(f"  Action: priority={action.get('priority')}, category={action.get('category')}, team={action.get('assigned_team')}")

        # Step the environment
        step_resp = requests.post(f"{BASE_URL}/step", json=action)
        if step_resp.status_code != 200:
            print(f"  ERROR: step failed: {step_resp.text}")
            break

        step_data = step_resp.json()
        reward = step_data["reward"]["value"]
        scores.append(reward)
        print(f"  Reward: {reward:.4f}")

        obs = step_data["observation"]

        if step_data["done"]:
            break

        time.sleep(0.5)  # Rate limit protection

    avg_score = sum(scores) / len(scores) if scores else 0.0
    print(f"\n  Task {task_id} — Average Score: {avg_score:.4f} (over {len(scores)} emails)")
    return round(avg_score, 4)


def run_baseline() -> dict:
    """Run baseline on all 3 tasks and return scores dict."""
    print("=" * 60)
    print("Email Triage OpenEnv — Baseline Inference Script")
    print("=" * 60)
    print(f"Model: {MODEL if OPENAI_API_KEY else 'Rule-based (no API key)'}")
    print(f"Environment: {BASE_URL}")

    results = {}
    for task_id in ["task_easy", "task_medium", "task_hard"]:
        score = run_task(task_id)
        results[task_id] = score

    print("\n" + "=" * 60)
    print("FINAL BASELINE SCORES")
    print("=" * 60)
    for task_id, score in results.items():
        print(f"  {task_id:15s}: {score:.4f}")
    avg = sum(results.values()) / len(results)
    print(f"  {'OVERALL':15s}: {avg:.4f}")
    print("=" * 60)

    return results


if __name__ == "__main__":
    scores = run_baseline()
    # Save scores to file for reproducibility
    with open("baseline_scores.json", "w") as f:
        json.dump(scores, f, indent=2)
    print("\nScores saved to baseline_scores.json")
