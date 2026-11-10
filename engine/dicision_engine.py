import json
import os
import random
import uuid
from datetime import datetime, timezone


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(ROOT, "data")

CITIZENS_FILE = os.path.join(DATA_DIR, "citizens.json")

DECISIONS_FILE = os.path.join(DATA_DIR, "decisions.json")


def load_json(path, default):

    if not os.path.exists(path):
        return default

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path, data):

    os.makedirs(DATA_DIR, exist_ok=True)

    temporary = path + ".tmp"

    with open(temporary, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )

    os.replace(temporary, path)


class DecisionEngine:

    def __init__(self):

        self.population = load_json(
            CITIZENS_FILE,
            {"citizens": [], "families": []}
        )

        self.citizens = self.population.get(
            "citizens", []
        )

        self.database = load_json(
            DECISIONS_FILE,
            {
                "decisions": [],
                "daily_actions": [],
                "goal_history": []
            }
        )

    def find_citizen(self, citizen_id):

        return next(
            (
                citizen for citizen in self.citizens
                if citizen["id"] == citizen_id
            ),
            None
        )

    def get_needs(self, citizen):

        age = citizen.get("age", 0)

        return {

            "health": citizen.get("health", 100),

            "happiness": citizen.get("happiness", 50),

            "energy": citizen.get("energy", 100),

            "wealth": citizen.get("wealth", 0),

            "social": min(
                100,
                len(citizen.get("relationships", [])) * 15
            ),

            "career": (
                100
                if citizen.get("employment_status") == "EMPLOYED"
                else 30
            ),

            "education": (
                100 if age >= 18 else 60
            )

        }

    def calculate_priorities(self, citizen):

        needs = self.get_needs(citizen)

        priorities = {

            "REST": max(0, 100 - needs["energy"]),

            "HEALTHCARE": max(0, 100 - needs["health"]),

            "SOCIALIZE": max(0, 75 - needs["social"]),

            "EARN_MONEY": max(0, 5000 - needs["wealth"]) / 50,

            "CAREER": max(0, 100 - needs["career"]),

            "ENTERTAINMENT": max(0, 80 - needs["happiness"])

        }

        return priorities

    def personality_modifier(self, citizen, action):

        personality = citizen.get("personality", [])

        decision_style = citizen.get(
            "decision_style",
            "Balanced"
        )

        modifier = 0

        if action == "SOCIALIZE":

            if "Extroverted" in personality:
                modifier += 25

            if "Introverted" in personality:
                modifier -= 15

        elif action == "CAREER":

            if "Ambitious" in personality:
                modifier += 25

            if "Independent" in personality:
                modifier += 10

        elif action == "EXPLORE":

            if "Adventurous" in personality:
                modifier += 30

            if "Curious" in personality:
                modifier += 20

        elif action == "CREATE_BUSINESS":

            if "Entrepreneurial" in personality:
                modifier += 30

            if decision_style == "Risk Taker":
                modifier += 15

            if decision_style == "Cautious":
                modifier -= 15

        return modifier

    def available_actions(self, citizen):

        age = citizen.get("age", 0)

        actions = [
            "REST",
            "ENTERTAINMENT",
            "SOCIALIZE",
            "EXPLORE"
        ]

        if age >= 18:

            actions.extend([
                "CAREER",
                "EARN_MONEY",
                "SAVE_MONEY",
                "CREATE_BUSINESS"
            ])

        if citizen.get("health", 100) < 60:

            actions.insert(0, "HEALTHCARE")

        return actions

    def evaluate_action(self, citizen, action):

        priorities = self.calculate_priorities(citizen)

        base_scores = {

            "REST": priorities["REST"],

            "HEALTHCARE": priorities["HEALTHCARE"],

            "SOCIALIZE": priorities["SOCIALIZE"],

            "CAREER": priorities["CAREER"],

            "EARN_MONEY": priorities["EARN_MONEY"],

            "ENTERTAINMENT": priorities["ENTERTAINMENT"],

            "SAVE_MONEY": max(
                0,
                100 - citizen.get("wealth", 0) / 100
            ),

            "CREATE_BUSINESS": (
                citizen.get("intelligence", 50) * 0.5
                + citizen.get("creativity", 50) * 0.5
            ),

            "EXPLORE": 40

        }

        score = base_scores.get(action, 0)

        score += self.personality_modifier(
            citizen,
            action
        )

        # Intelligence can improve planning.
        score += (
            citizen.get("intelligence", 50) - 50
        ) * 0.1

        # Energy limits physically demanding decisions.
        if action in [
            "CAREER",
            "EARN_MONEY",
            "EXPLORE"
        ]:

            score *= (
                0.5 + citizen.get("energy", 100) / 200
            )

        # Memories influence future decisions.
        recent_memory = citizen.get("memory", [])[-10:]

        negative_events = sum(
            1 for event in recent_memory
            if event.get("event") in [
                "CONFLICT",
                "FAILURE",
                "ILLNESS"
            ]
        )

        if action == "SOCIALIZE":
            score -= negative_events * 3

        return max(0, min(150, score))

    def decide(self, citizen_id, simulation_day):

        citizen = self.find_citizen(citizen_id)

        if not citizen:
            return {"error": "Citizen not found"}

        if not citizen.get("alive", False):
            return {"error": "Citizen is deceased"}

        if citizen.get("health", 100) <= 0:
            return {"error": "Citizen needs emergency healthcare"}

        actions = self.available_actions(citizen)

        scored_actions = []

        for action in actions:

            score = self.evaluate_action(
                citizen,
                action
            )

            # Small variation avoids identical behaviour.
            score += random.uniform(-5, 5)

            scored_actions.append({
                "action": action,
                "score": round(score, 2)
            })

        scored_actions.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        selected = scored_actions[0]

        decision = {

            "id": str(uuid.uuid4()),

            "citizen_id": citizen_id,

            "citizen_name": citizen["name"],

            "simulation_day": simulation_day,

            "chosen_action": selected["action"],

            "score": selected["score"],

            "alternatives": scored_actions[1:4],

            "reason": (
                f"Selected based on personal needs, "
                f"personality and current circumstances."
            ),

            "created_at": datetime.now(
                timezone.utc
            ).isoformat()

        }

        self.database["decisions"].append(decision)

        self.database["decisions"] = (
            self.database["decisions"][-1000:]
        )

        citizen.setdefault("memory", []).append({

            "event": "DECISION",

            "action": selected["action"],

            "day": simulation_day

        })

        citizen["memory"] = citizen["memory"][-100:]

        self.save()

        return decision

    def decide_for_population(self, simulation_day):

        results = []

        for citizen in self.citizens:

            if not citizen.get("alive", False):
                continue

            result = self.decide(
                citizen["id"],
                simulation_day
            )

            results.append(result)

        return results

    def get_statistics(self):

        decisions = self.database["decisions"]

        action_counts = {}

        for decision in decisions:

            action = decision["chosen_action"]

            action_counts[action] = (
                action_counts.get(action, 0) + 1
            )

        return {

            "total_decisions": len(decisions),

            "actions": action_counts

        }

    def save(self):

        self.population["citizens"] = self.citizens

        save_json(
            CITIZENS_FILE,
            self.population
        )

        save_json(
            DECISIONS_FILE,
            self.database
        )


if __name__ == "__main__":

    engine = DecisionEngine()

    print("AI LIFEVERSE DECISION ENGINE")

    if engine.citizens:

        citizen = random.choice(engine.citizens)

        result = engine.decide(
            citizen["id"],
            simulation_day=1
        )

        print(json.dumps(
            result,
            indent=4
        ))

    else:

        print("No citizens found.")

    print("\nENGINE STATISTICS")

    print(json.dumps(
        engine.get_statistics(),
        indent=4
    ))
