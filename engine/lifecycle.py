import json
import os
import uuid
import random
from datetime import datetime, timezone


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(ROOT, "data")

CITIZENS_FILE = os.path.join(DATA_DIR, "citizens.json")
LIFECYCLE_FILE = os.path.join(DATA_DIR, "lifecycle.json")


def load_json(path, default):

    if not os.path.exists(path):
        return default

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path, data):

    os.makedirs(DATA_DIR, exist_ok=True)

    temporary = path + ".tmp"

    with open(temporary, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    os.replace(temporary, path)


class LifecycleEngine:

    def __init__(self):

        self.population = load_json(
            CITIZENS_FILE,
            {"citizens": [], "families": []}
        )

        self.citizens = self.population.get("citizens", [])

        self.database = load_json(
            LIFECYCLE_FILE,
            {
                "births": [],
                "deaths": [],
                "illnesses": [],
                "milestones": []
            }
        )

    def find_citizen(self, citizen_id):

        return next(
            (
                c for c in self.citizens
                if c["id"] == citizen_id
            ),
            None
        )

    def create_child(
        self,
        parent_a_id,
        parent_b_id,
        simulation_day
    ):

        parent_a = self.find_citizen(parent_a_id)
        parent_b = self.find_citizen(parent_b_id)

        if not parent_a or not parent_b:
            return {"error": "Parent not found"}

        if not parent_a.get("alive") or not parent_b.get("alive"):
            return {"error": "Both parents must be alive"}

        if parent_a["age"] < 18 or parent_b["age"] < 18:
            return {"error": "Parents must be adults"}

        child_id = str(uuid.uuid4())

        child = {

            "id": child_id,

            "name": "Newborn " + child_id[:5],

            "family_id": parent_a["family_id"],

            "gender": random.choice(["Male", "Female"]),

            "age": 0,

            "generation": max(
                parent_a.get("generation", 1),
                parent_b.get("generation", 1)
            ) + 1,

            "alive": True,

            "health": 100,

            "happiness": 50,

            "energy": 100,

            "wealth": 0,

            "bank_balance": 0,

            "intelligence": random.randint(40, 70),

            "creativity": random.randint(40, 70),

            "emotional_intelligence": random.randint(40, 70),

            "personality": [],

            "skills": {},

            "goals": [],

            "career": None,

            "employment_status": "NOT_ELIGIBLE",

            "relationships": [
                {
                    "citizen_id": parent_a_id,
                    "type": "PARENT"
                },
                {
                    "citizen_id": parent_b_id,
                    "type": "PARENT"
                }
            ],

            "memory": [],

            "life_stage": "INFANT",

            "education": "NOT_STARTED",

            "birth_day": simulation_day,

            "created_at": datetime.now(
                timezone.utc
            ).isoformat()

        }

        self.citizens.append(child)

        parent_a.setdefault("relationships", []).append({
            "citizen_id": child_id,
            "type": "CHILD"
        })

        parent_b.setdefault("relationships", []).append({
            "citizen_id": child_id,
            "type": "CHILD"
        })

        event = {
            "citizen_id": child_id,
            "parents": [parent_a_id, parent_b_id],
            "day": simulation_day
        }

        self.database["births"].append(event)

        self.save()

        return {
            "message": "New citizen born",
            "citizen": child
        }

    def update_life_stage(self, citizen):

        age = citizen["age"]

        if age < 3:
            stage = "INFANT"

        elif age < 13:
            stage = "CHILD"

        elif age < 18:
            stage = "TEENAGER"

        elif age < 60:
            stage = "ADULT"

        elif age < 80:
            stage = "SENIOR"

        else:
            stage = "ELDER"

        old_stage = citizen.get("life_stage")

        citizen["life_stage"] = stage

        if old_stage != stage:

            self.database["milestones"].append({

                "citizen_id": citizen["id"],

                "event": "LIFE_STAGE_CHANGED",

                "from": old_stage,

                "to": stage

            })

            if stage == "ADULT":

                citizen["employment_status"] = "UNEMPLOYED"

                citizen["education"] = "COMPLETED"

                self.database["milestones"].append({

                    "citizen_id": citizen["id"],

                    "event": "BECAME_ADULT"

                })

    def update_education(self, citizen):

        age = citizen["age"]

        if age < 3:
            education = "EARLY_CHILDHOOD"

        elif age < 6:
            education = "PRESCHOOL"

        elif age < 13:
            education = "PRIMARY_SCHOOL"

        elif age < 18:
            education = "SECONDARY_SCHOOL"

        else:
            education = "COMPLETED"

        citizen["education"] = education

    def age_population(self, simulation_day):

        if simulation_day <= 0 or simulation_day % 365 != 0:
            return []

        aged = []

        for citizen in self.citizens:

            if not citizen.get("alive"):
                continue

            citizen["age"] += 1

            self.update_life_stage(citizen)

            self.update_education(citizen)

            aged.append(citizen["id"])

        self.save()

        return aged

    def process_health(self, simulation_day):

        events = []

        for citizen in self.citizens:

            if not citizen.get("alive"):
                continue

            health = citizen.get("health", 100)

            if health < 100 and random.random() < 0.15:

                citizen["health"] = min(
                    100,
                    health + random.randint(1, 5)
                )

            if random.random() < 0.005:

                damage = random.randint(2, 10)

                citizen["health"] = max(
                    0,
                    citizen["health"] - damage
                )

                event = {

                    "citizen_id": citizen["id"],

                    "type": "ILLNESS",

                    "day": simulation_day,

                    "severity": damage

                }

                self.database["illnesses"].append(event)

                events.append(event)

        self.save()

        return events

    def process_mortality(self, simulation_day):

        deaths = []

        for citizen in self.citizens:

            if not citizen.get("alive"):
                continue

            age = citizen.get("age", 0)

            health = citizen.get("health", 100)

            death_probability = 0

            if health <= 0:
                death_probability = 1.0

            elif age >= 100:
                death_probability = 0.02

            elif age >= 90:
                death_probability = 0.005

            elif age >= 80:
                death_probability = 0.001

            if random.random() < death_probability:

                citizen["alive"] = False

                citizen["death_day"] = simulation_day

                citizen["life_stage"] = "DECEASED"

                event = {

                    "citizen_id": citizen["id"],

                    "name": citizen["name"],

                    "age": age,

                    "day": simulation_day,

                    "cause": (
                        "Critical illness"
                        if health <= 0
                        else "Natural causes"
                    )

                }

                self.database["deaths"].append(event)

                deaths.append(event)

        self.save()

        return deaths

    def get_statistics(self):

        alive = [
            c for c in self.citizens
            if c.get("alive")
        ]

        return {

            "total_population": len(self.citizens),

            "living": len(alive),

            "deceased": len(self.citizens) - len(alive),

            "births": len(self.database["births"]),

            "deaths": len(self.database["deaths"]),

            "children": sum(
                1 for c in alive
                if c.get("age", 0) < 18
            ),

            "adults": sum(
                1 for c in alive
                if c.get("age", 0) >= 18
            )

        }

    def save(self):

        self.population["citizens"] = self.citizens

        save_json(CITIZENS_FILE, self.population)

        save_json(LIFECYCLE_FILE, self.database)


if __name__ == "__main__":

    engine = LifecycleEngine()

    print("AI LIFEVERSE LIFE CYCLE ENGINE")

    print(json.dumps(
        engine.get_statistics(),
        indent=4
    ))
