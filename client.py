import requests

class EmailTriageClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def reset(self, task_id="task_easy", seed=42):
        r = requests.post(f"{self.base_url}/reset", json={"task_id": task_id, "seed": seed})
        return r.json()

    def step(self, priority, category, assigned_team, summary=""):
        r = requests.post(f"{self.base_url}/step", json={
            "priority": priority, "category": category,
            "assigned_team": assigned_team, "summary": summary
        })
        return r.json()

    def state(self):
        return requests.get(f"{self.base_url}/state").json()
