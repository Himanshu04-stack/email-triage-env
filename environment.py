import random
from typing import Optional, Any
from pydantic import BaseModel

# ── Typed Models (OpenEnv spec) ──────────────────────────────────────────────

class EmailObservation(BaseModel):
    email_id: str
    subject: str
    body: str
    sender: str
    sender_domain: str
    timestamp: str
    has_attachment: bool
    thread_length: int
    task_id: str
    task_description: str

class TriageAction(BaseModel):
    priority: str          # "urgent" | "normal" | "low"
    category: str          # "bug" | "feature_request" | "billing" | "spam" | "support" | "other"
    assigned_team: str     # "engineering" | "billing" | "support" | "sales" | "ignore"
    summary: str           # one-line summary (for hard task)

class TriageReward(BaseModel):
    value: float
    breakdown: dict

# ── Email Dataset with Ground Truth ─────────────────────────────────────────

EMAILS = [
    {
        "email_id": "e001",
        "subject": "URGENT: Production payment service down - 500 errors",
        "body": "Our payment gateway has been returning 500 errors for the last 20 minutes. Multiple customers cannot complete purchases. We are losing thousands in revenue every minute. This needs immediate attention from the engineering team.",
        "sender": "oncall@acmecorp.com",
        "sender_domain": "acmecorp.com",
        "timestamp": "2024-01-15T02:30:00Z",
        "has_attachment": False,
        "thread_length": 1,
        "ground_truth": {"priority": "urgent", "category": "bug", "assigned_team": "engineering", "keywords": ["payment", "500 error", "revenue loss"]}
    },
    {
        "email_id": "e002",
        "subject": "Refund request - Order #78234",
        "body": "Hello, I ordered a laptop last week (Order #78234) but it arrived damaged. The screen has a crack. I would like a full refund of $1299. Please process this as soon as possible. My account email is john.doe@gmail.com.",
        "sender": "john.doe@gmail.com",
        "sender_domain": "gmail.com",
        "timestamp": "2024-01-15T09:15:00Z",
        "has_attachment": True,
        "thread_length": 1,
        "ground_truth": {"priority": "normal", "category": "billing", "assigned_team": "billing", "keywords": ["refund", "damaged", "order 78234"]}
    },
    {
        "email_id": "e003",
        "subject": "Feature request: Dark mode for mobile app",
        "body": "Hi team, I love your product but would really appreciate a dark mode option on the mobile app. Many users have been asking for this in the community forum too. Would be great to have it in the next update. Thanks!",
        "sender": "poweruser@outlook.com",
        "sender_domain": "outlook.com",
        "timestamp": "2024-01-15T11:00:00Z",
        "has_attachment": False,
        "thread_length": 1,
        "ground_truth": {"priority": "low", "category": "feature_request", "assigned_team": "engineering", "keywords": ["dark mode", "mobile app", "community request"]}
    },
    {
        "email_id": "e004",
        "subject": "Win $1,000,000! Click here NOW!!!",
        "body": "Congratulations! You have been selected to win ONE MILLION DOLLARS! Just click the link below and enter your credit card details to claim your prize! Limited time offer! Act NOW! www.totally-not-scam.xyz/claim",
        "sender": "winner@free-prize.xyz",
        "sender_domain": "free-prize.xyz",
        "timestamp": "2024-01-15T08:00:00Z",
        "has_attachment": False,
        "thread_length": 1,
        "ground_truth": {"priority": "low", "category": "spam", "assigned_team": "ignore", "keywords": ["spam", "scam", "no action needed"]}
    },
    {
        "email_id": "e005",
        "subject": "Cannot login to my account - locked out for 3 days",
        "body": "I have been locked out of my account for 3 days now. I tried resetting my password multiple times but the reset email never arrives. I have important data in my account and have a deadline tomorrow. This is very frustrating. My username is sarah.jones.",
        "sender": "sarah.jones@company.org",
        "sender_domain": "company.org",
        "timestamp": "2024-01-15T14:20:00Z",
        "has_attachment": False,
        "thread_length": 4,
        "ground_truth": {"priority": "urgent", "category": "support", "assigned_team": "support", "keywords": ["locked out", "password reset", "deadline"]}
    },
    {
        "email_id": "e006",
        "subject": "Invoice question for subscription renewal",
        "body": "Hi, I noticed my invoice this month shows $99 but I am on the $49 plan. Could you clarify why I was charged double? My account ID is ACC-44521. Please send a corrected invoice. Thanks.",
        "sender": "mike.chen@startup.io",
        "sender_domain": "startup.io",
        "timestamp": "2024-01-15T10:45:00Z",
        "has_attachment": True,
        "thread_length": 2,
        "ground_truth": {"priority": "normal", "category": "billing", "assigned_team": "billing", "keywords": ["wrong charge", "invoice", "account 44521"]}
    },
    {
        "email_id": "e007",
        "subject": "API rate limiting hitting our enterprise integration",
        "body": "Our enterprise integration is hitting rate limits at 1000 req/min even though our contract says 5000 req/min. This is breaking our production workflow that serves 50,000 users. Need this resolved today. Contract reference: ENT-2024-0089.",
        "sender": "devops@bigenterprise.com",
        "sender_domain": "bigenterprise.com",
        "timestamp": "2024-01-15T13:00:00Z",
        "has_attachment": False,
        "thread_length": 3,
        "ground_truth": {"priority": "urgent", "category": "bug", "assigned_team": "engineering", "keywords": ["rate limit", "enterprise", "production", "contract breach"]}
    },
    {
        "email_id": "e008",
        "subject": "Interested in upgrading to Enterprise plan",
        "body": "Hello Sales team, we are a 200-person company currently on the Business plan. We are interested in upgrading to Enterprise. Could you send us a custom quote and schedule a demo? Best time for us is next Tuesday or Wednesday afternoon.",
        "sender": "procurement@megacorp.com",
        "sender_domain": "megacorp.com",
        "timestamp": "2024-01-15T09:30:00Z",
        "has_attachment": False,
        "thread_length": 1,
        "ground_truth": {"priority": "normal", "category": "other", "assigned_team": "sales", "keywords": ["enterprise upgrade", "demo request", "200 person company"]}
    },
    {
        "email_id": "e009",
        "subject": "Data export feature suggestion",
        "body": "It would be really helpful if we could export our data in Excel format, not just CSV. Many of our team members are not technical and prefer Excel. This would save us a lot of manual conversion work every week.",
        "sender": "ops.manager@nonprofit.org",
        "sender_domain": "nonprofit.org",
        "timestamp": "2024-01-15T15:10:00Z",
        "has_attachment": False,
        "thread_length": 1,
        "ground_truth": {"priority": "low", "category": "feature_request", "assigned_team": "engineering", "keywords": ["excel export", "data export", "non-technical users"]}
    },
    {
        "email_id": "e010",
        "subject": "Security vulnerability report - XSS in user profile",
        "body": "Hello security team, I found a reflected XSS vulnerability in the user profile page. When a malicious script is inserted in the bio field, it executes for any user who views that profile. I have attached a proof of concept. Please treat this as high priority. I am happy to discuss details securely.",
        "sender": "security.researcher@bugbounty.io",
        "sender_domain": "bugbounty.io",
        "timestamp": "2024-01-15T07:00:00Z",
        "has_attachment": True,
        "thread_length": 1,
        "ground_truth": {"priority": "urgent", "category": "bug", "assigned_team": "engineering", "keywords": ["XSS vulnerability", "security", "proof of concept"]}
    },
    {
        "email_id": "e011",
        "subject": "How do I add a team member?",
        "body": "Hi, I am trying to add a new colleague to our workspace but cannot figure out how. I went to Settings but do not see an option for team members. Can you point me to the right place? Thank you.",
        "sender": "newuser@smallbiz.com",
        "sender_domain": "smallbiz.com",
        "timestamp": "2024-01-15T16:00:00Z",
        "has_attachment": False,
        "thread_length": 1,
        "ground_truth": {"priority": "low", "category": "support", "assigned_team": "support", "keywords": ["add team member", "settings", "how-to"]}
    },
    {
        "email_id": "e012",
        "subject": "Partnership opportunity - white label reseller",
        "body": "Dear team, we are a software distributor operating in Southeast Asia with 500 clients. We are interested in becoming a white-label reseller of your product. We believe we can bring significant volume. Can we schedule a call with your partnerships team?",
        "sender": "bd@asiatech.sg",
        "sender_domain": "asiatech.sg",
        "timestamp": "2024-01-15T11:30:00Z",
        "has_attachment": False,
        "thread_length": 1,
        "ground_truth": {"priority": "normal", "category": "other", "assigned_team": "sales", "keywords": ["white label", "reseller", "southeast asia", "500 clients"]}
    },
]

# ── Task Definitions ─────────────────────────────────────────────────────────

TASKS = {
    "task_easy": {
        "id": "task_easy",
        "description": "Classify the email priority only. Set priority to 'urgent', 'normal', or 'low'. Other fields can be any valid value.",
        "difficulty": "easy",
        "target_score": 0.7,
        "grading_fields": ["priority"]
    },
    "task_medium": {
        "id": "task_medium",
        "description": "Classify both the email priority ('urgent'/'normal'/'low') AND category ('bug'/'feature_request'/'billing'/'spam'/'support'/'other').",
        "difficulty": "medium",
        "target_score": 0.5,
        "grading_fields": ["priority", "category"]
    },
    "task_hard": {
        "id": "task_hard",
        "description": "Full triage: classify priority, category, assigned_team ('engineering'/'billing'/'support'/'sales'/'ignore'), AND write a concise 1-sentence summary of the key issue.",
        "difficulty": "hard",
        "target_score": 0.35,
        "grading_fields": ["priority", "category", "assigned_team", "summary"]
    }
}

# ── Environment Class ────────────────────────────────────────────────────────

class EmailTriageEnv:
    def __init__(self, task_id: str = "task_easy", seed: Optional[int] = 42):
        assert task_id in TASKS, f"task_id must be one of {list(TASKS.keys())}"
        self.task_id = task_id
        self.task = TASKS[task_id]
        self.seed = seed
        self.rng = random.Random(seed)
        self._episode_emails = []
        self._current_index = 0
        self._current_email = None
        self._done = False
        self._total_reward = 0.0
        self._steps = 0
        self._last_action = None
        self._last_reward = None

    def reset(self) -> EmailObservation:
        self.rng = random.Random(self.seed)
        shuffled = EMAILS.copy()
        self.rng.shuffle(shuffled)
        self._episode_emails = shuffled[:6]  # 6 emails per episode
        self._current_index = 0
        self._done = False
        self._total_reward = 0.0
        self._steps = 0
        self._last_action = None
        self._last_reward = None
        self._current_email = self._episode_emails[0]
        return self._make_observation()

    def step(self, action: TriageAction) -> tuple[EmailObservation, TriageReward, bool, dict]:
        if self._done:
            raise RuntimeError("Episode is done. Call reset() to start a new episode.")

        reward, breakdown = self._compute_reward(action, self._current_email)
        self._last_action = action
        self._last_reward = reward
        self._total_reward += reward
        self._steps += 1
        self._current_index += 1

        if self._current_index >= len(self._episode_emails):
            self._done = True
            obs = self._make_observation()
        else:
            self._current_email = self._episode_emails[self._current_index]
            obs = self._make_observation()

        info = {
            "step": self._steps,
            "total_reward": round(self._total_reward, 4),
            "emails_remaining": max(0, len(self._episode_emails) - self._current_index),
            "ground_truth": self._episode_emails[self._current_index - 1]["ground_truth"] if self._done else None
        }

        return obs, TriageReward(value=round(reward, 4), breakdown=breakdown), self._done, info

    def state(self) -> dict:
        return {
            "task_id": self.task_id,
            "task_description": self.task["description"],
            "difficulty": self.task["difficulty"],
            "current_email_id": self._current_email["email_id"] if self._current_email else None,
            "step": self._steps,
            "total_reward": round(self._total_reward, 4),
            "done": self._done,
            "emails_in_episode": len(self._episode_emails),
            "emails_remaining": max(0, len(self._episode_emails) - self._current_index),
        }

    def grade(self, action: TriageAction, email: dict) -> float:
        score, _ = self._compute_reward(action, email)
        return round(score, 4)

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _make_observation(self) -> EmailObservation:
        if self._done or self._current_email is None:
            # Return a dummy end-of-episode observation
            return EmailObservation(
                email_id="done",
                subject="",
                body="Episode complete.",
                sender="",
                sender_domain="",
                timestamp="",
                has_attachment=False,
                thread_length=0,
                task_id=self.task_id,
                task_description=self.task["description"]
            )
        e = self._current_email
        return EmailObservation(
            email_id=e["email_id"],
            subject=e["subject"],
            body=e["body"],
            sender=e["sender"],
            sender_domain=e["sender_domain"],
            timestamp=e["timestamp"],
            has_attachment=e["has_attachment"],
            thread_length=e["thread_length"],
            task_id=self.task_id,
            task_description=self.task["description"]
        )

    def _compute_reward(self, action: TriageAction, email: dict) -> tuple[float, dict]:
        gt = email["ground_truth"]
        breakdown = {}
        grading_fields = self.task["grading_fields"]
        total = 0.0

        # Priority (always graded, 40% weight in all tasks)
        if "priority" in grading_fields:
            p_score = 1.0 if action.priority == gt["priority"] else 0.0
            # Partial credit: urgent/low confusion is worse than urgent/normal
            if p_score == 0:
                if (action.priority == "urgent" and gt["priority"] == "low") or \
                   (action.priority == "low" and gt["priority"] == "urgent"):
                    p_score = 0.0   # completely wrong
                else:
                    p_score = 0.2   # adjacent error
            breakdown["priority"] = p_score
            total += p_score * 0.40

        # Category (medium + hard, 30% weight)
        if "category" in grading_fields:
            c_score = 1.0 if action.category == gt["category"] else 0.0
            breakdown["category"] = c_score
            total += c_score * 0.30

        # Assigned team (hard only, 20% weight)
        if "assigned_team" in grading_fields:
            t_score = 1.0 if action.assigned_team == gt["assigned_team"] else 0.0
            breakdown["assigned_team"] = t_score
            total += t_score * 0.20

        # Summary quality (hard only, 10% weight)
        if "summary" in grading_fields:
            keywords = gt.get("keywords", [])
            if keywords:
                hits = sum(1 for kw in keywords if kw.lower() in action.summary.lower())
                s_score = min(1.0, hits / max(1, len(keywords) * 0.5))
            else:
                s_score = 0.5 if len(action.summary) > 10 else 0.0
            breakdown["summary_keyword_coverage"] = round(s_score, 4)
            total += s_score * 0.10

        # Normalize to 0-1 based on task weights
        if self.task_id == "task_easy":
            total = breakdown.get("priority", 0.0)
        elif self.task_id == "task_medium":
            total = breakdown.get("priority", 0.0) * 0.5 + breakdown.get("category", 0.0) * 0.5
        # hard: already weighted above

        # Penalty: penalize very long summaries (padding behavior)
        if "summary" in grading_fields and len(action.summary) > 300:
            total *= 0.8

        return min(1.0, max(0.0, total)), breakdown
