import json
import os
import uuid
from datetime import datetime, timezone


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA = os.path.join(ROOT, "data")

CITIZENS_FILE = os.path.join(DATA, "citizens.json")
ACTIONS_FILE = os.path.join(DATA, "actions.json")


def load_json(path, default):
    if not os.path.exists(path):
        return default

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path, data):
    os.makedirs(DATA, exist_ok=True)

    temporary = path + ".tmp"

    with open(temporary, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    os.replace(temporary, path)


class ActionEngine:

    def __init__(self):

        self.population = load_json(
            CITIZENS_FILE,
            {"citizens": [], "families": []}
        )

        self.citizens = self.population.get("citizens", [])

        self.database = load_json(
            ACTIONS_FILE,
            {"actions": []}
        )

    def find_citizen(self, citizen_id):

        return next(
            (c for c in self.citizens if c["id"] == citizen_id),
            None
        )

    def execute(self, citizen_id, action, simulation_day):

        citizen = self.find_citizen(citizen_id)

        if not citizen:
            return {"error": "Citizen not found"}

        if not citizen.get("alive", False):
            return {"error": "Citizen is deceased"}

        if action not in [
            "REST",
            "HEALTHCARE",
            "SOCIALIZE",
            "CAREER",
            "EARN_MONEY",
            "SAVE_MONEY",
            "ENTERTAINMENT",
            "EXPLORE",
            "CREATE_BUSINESS"
        ]:
            return {"error": "Unsupported action"}

        result = self.perform_action(citizen, action)

        event = {
            "id": str(uuid.uuid4()),
            "citizen_id": citizen_id,
            "citizen_name": citizen["name"],
            "action": action,
            "result": result,
            "simulation_day": simulation_day,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat()
        }

        self.database["actions"].append(event)

        self.database["actions"] = (
            self.database["actions"][-1000:]
        )

        citizen.setdefault("memory", []).append({
            "event": action,
            "day": simulation_day,
            "result": result
        })

        citizen["memory"] = citizen["memory"][-100:]

        self.save()

        return event

    def perform_action(self, citizen, action):

        citizen.setdefault("wealth", 0)
        citizen.setdefault("energy", 100)
        citizen.setdefault("health", 100)
        citizen.setdefault("happiness", 50)

        if action == "REST":

            citizen["energy"] = min(
                100,
                citizen["energy"] + 25
            )

            return "Rested and recovered energy"

        if action == "HEALTHCARE":

            citizen["health"] = min(
                100,
                citizen["health"] + 15
            )

            return "Received simulated medical care"

        if action == "SOCIALIZE":

            citizen["happiness"] = min(
                100,
                citizen["happiness"] + 8
            )

            return "Participated in social activity"

        if action == "CAREER":

            if citizen.get("age", 0) < 18:
                return "Not eligible for employment"

            citizen["happiness"] = min(
                100,
                citizen["happiness"] + 3
            )

            return "Worked on career development"

        if action == "EARN_MONEY":

            if citizen.get("age", 0) < 18:
                return "Not eligible for employment"

            if citizen.get("employment_status") != "EMPLOYED":
                return "Currently unemployed"

            earnings = max(
                0,
                citizen.get("salary", 0) // 30
            )

            citizen["wealth"] += earnings

            citizen["energy"] = max(
                0,
                citizen["energy"] - 15
            )

            return f"Earned {earnings} credits"

        if action == "SAVE_MONEY":

            amount = min(
                100,
                citizen["wealth"]
            )

            citizen["wealth"] -= amount

            citizen["bank_balance"] = (
                citizen.get("bank_balance", 0) + amount
            )

            return f"Saved {amount} credits"

        if action == "ENTERTAINMENT":

            citizen["happiness"] = min(
                100,
                citizen["happiness"] + 12
            )

            citizen["energy"] = max(
                0,
                citizen["energy"] - 5
            )

            return "Enjoyed entertainment"

        if action == "EXPLORE":

            citizen["energy"] = max(
                0,
                citizen["energy"] - 10
            )

            citizen["happiness"] = min(
                100,
                citizen["happiness"] + 5
            )

            return "Explored Nova City"

        if action == "CREATE_BUSINESS":

            if citizen["wealth"] < 1000:
                return "Insufficient capital"

            return "Business planning started"

    def execute_decisions(self, decisions, simulation_day):

        results = []

        for decision in decisions:

            if "error" in decision:
                continue

            result = self.execute(
                decision["citizen_id"],
                decision["chosen_action"],
                simulation_day
            )

            results.append(result)

        return results

    def get_statistics(self):

        actions = self.database["actions"]

        action_counts = {}

        for item in actions:

            action = item["action"]

            action_counts[action] = (
                action_counts.get(action, 0) + 1
            )

        return {
            "total_actions": len(actions),
            "action_distribution": action_counts
        }

    def save(self):

        self.population["citizens"] = self.citizens

        save_json(CITIZENS_FILE, self.population)

        save_json(ACTIONS_FILE, self.database)


if __name__ == "__main__":

    engine = ActionEngine()

    print("AI LIFEVERSE ACTION ENGINE")

    print(json.dumps(
        engine.get_statistics(),
        indent=4
    ))
