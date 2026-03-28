import os, json, requests

BASE_URL = os.getenv("SPACE_URL", "http://localhost:7860")

def run():
    results = {}
    for task_id in ["task_easy", "task_medium", "task_hard"]:
        requests.post(f"{BASE_URL}/reset", json={"task_id": task_id, "seed": 42})
        total, steps = 0.0, 0
        for _ in range(6):
            r = requests.post(f"{BASE_URL}/step", json={
                "priority": "normal",
                "category": "support", 
                "assigned_team": "support",
                "summary": "User needs assistance."
            })
            d = r.json()
            total += d["reward"]["value"]
            steps += 1
            if d["done"]:
                break
        results[task_id] = round(total/steps, 4)
    print(json.dumps(results, indent=2))
    return results

if __name__ == "__main__":
    run()
