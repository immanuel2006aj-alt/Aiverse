import json
import os
import uuid
import random
from datetime import datetime, timezone


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(ROOT, "data")

CITIZENS_FILE = os.path.join(DATA_DIR, "citizens.json")

RELATIONSHIPS_FILE = os.path.join(
    DATA_DIR,
    "relationships.json"
)


def load_json(path, default):

    if not os.path.exists(path):
        return default

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path, data):

    os.makedirs(DATA_DIR, exist_ok=True)

    temp = path + ".tmp"

    with open(temp, "w", encoding="utf-8") as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )

    os.replace(temp, path)


class RelationshipEngine:

    def __init__(self):

        self.population = load_json(
            CITIZENS_FILE,
            {"citizens": [], "families": []}
        )

        self.citizens = self.population.get(
            "citizens", []
        )

        self.database = load_json(
            RELATIONSHIPS_FILE,
            {
                "relationships": [],
                "interactions": [],
                "conflicts": []
            }
        )

        self.relationships = self.database["relationships"]

        self.interactions = self.database["interactions"]

        self.conflicts = self.database["conflicts"]

    def find_citizen(self, citizen_id):

        return next(
            (
                c for c in self.citizens
                if c["id"] == citizen_id
            ),
            None
        )

    def find_relationship(self, a_id, b_id):

        return next(
            (
                r for r in self.relationships
                if set(r["people"]) == {a_id, b_id}
                and r["status"] == "ACTIVE"
            ),
            None
        )

    def compatibility(self, a, b):

        score = 0

        personality_a = set(
            a.get("personality", [])
        )

        personality_b = set(
            b.get("personality", [])
        )

        shared = personality_a & personality_b

        score += len(shared) * 15

        intelligence_difference = abs(
            a.get("intelligence", 50)
            - b.get("intelligence", 50)
        )

        score += max(
            0,
            25 - intelligence_difference // 2
        )

        emotional_difference = abs(
            a.get("emotional_intelligence", 50)
            - b.get("emotional_intelligence", 50)
        )

        score += max(
            0,
            25 - emotional_difference // 2
        )

        return min(100, score)

    def create_relationship(
        self,
        person_a_id,
        person_b_id,
        relationship_type="FRIENDSHIP"
    ):

        a = self.find_citizen(person_a_id)

        b = self.find_citizen(person_b_id)

        if not a or not b:
            return {"error": "Citizen not found"}

        if person_a_id == person_b_id:
            return {"error": "Cannot relate to yourself"}

        if not a.get("alive") or not b.get("alive"):
            return {"error": "Both citizens must be alive"}

        if relationship_type not in [
            "FRIENDSHIP",
            "ROMANTIC",
            "FAMILY"
        ]:
            return {"error": "Invalid relationship type"}

        existing = self.find_relationship(
            person_a_id,
            person_b_id
        )

        if existing:
            return {"error": "Relationship already exists"}

        if relationship_type == "ROMANTIC":

            if a.get("age", 0) < 18 or b.get("age", 0) < 18:
                return {"error": "Both citizens must be adults"}

            if (
                not a.get("romantic_interest")
                or not b.get("romantic_interest")
            ):
                return {"error": "Mutual romantic consent required"}

        score = self.compatibility(a, b)

        relationship = {

            "id": str(uuid.uuid4()),

            "people": [
                person_a_id,
                person_b_id
            ],

            "type": relationship_type,

            "compatibility": score,

            "trust": 50,

            "affection": 30,

            "status": "ACTIVE",

            "created_day": 1,

            "history": []

        }

        self.relationships.append(relationship)

        self.save()

        return relationship

    def interact(
        self,
        person_a_id,
        person_b_id,
        interaction_type="CONVERSATION",
        simulation_day=1
    ):

        a = self.find_citizen(person_a_id)

        b = self.find_citizen(person_b_id)

        if not a or not b:
            return {"error": "Citizen not found"}

        if not a.get("alive") or not b.get("alive"):
            return {"error": "Both citizens must be alive"}

        if person_a_id == person_b_id:
            return {"error": "Invalid interaction"}

        if interaction_type not in [
            "CONVERSATION",
            "HELP",
            "ARGUMENT",
            "ACTIVITY"
        ]:
            return {"error": "Invalid interaction type"}

        relationship = self.find_relationship(
            person_a_id,
            person_b_id
        )

        if not relationship:

            result = self.create_relationship(
                person_a_id,
                person_b_id
            )

            if "error" in result:
                return result

            relationship = result

        changes = {

            "CONVERSATION": (5, 3),

            "HELP": (10, 5),

            "ARGUMENT": (-12, -8),

            "ACTIVITY": (7, 4)

        }

        trust_change, affection_change = changes[
            interaction_type
        ]

        # Both participants have their own response.
        relationship["trust"] = max(
            0,
            min(
                100,
                relationship["trust"] + trust_change
            )
        )

        relationship["affection"] = max(
            0,
            min(
                100,
                relationship["affection"] + affection_change
            )
        )

        event = {

            "id": str(uuid.uuid4()),

            "people": [
                person_a_id,
                person_b_id
            ],

            "type": interaction_type,

            "simulation_day": simulation_day,

            "created_at": datetime.now(
                timezone.utc
            ).isoformat()

        }

        self.interactions.append(event)

        relationship["history"].append(event)

        relationship["history"] = (
            relationship["history"][-50:]
        )

        if interaction_type == "ARGUMENT":

            self.conflicts.append({

                "id": str(uuid.uuid4()),

                "people": [
                    person_a_id,
                    person_b_id
                ],

                "status": "UNRESOLVED",

                "simulation_day": simulation_day

            })

        # Individual memories.
        a.setdefault("memory", []).append({
            "event": interaction_type,
            "with": b["id"],
            "day": simulation_day
        })

        b.setdefault("memory", []).append({
            "event": interaction_type,
            "with": a["id"],
            "day": simulation_day
        })

        a["memory"] = a["memory"][-100:]

        b["memory"] = b["memory"][-100:]

        self.save()

        return {
            "relationship": relationship,
            "interaction": event
        }

    def resolve_conflict(self, relationship_id):

        relationship = next(
            (
                r for r in self.relationships
                if r["id"] == relationship_id
            ),
            None
        )

        if not relationship:
            return {"error": "Relationship not found"}

        if relationship["trust"] < 20:
            return {"error": "Trust is too low"}

        relationship["trust"] = min(
            100,
            relationship["trust"] + 15
        )

        relationship["status"] = "ACTIVE"

        for conflict in self.conflicts:

            if (
                set(conflict["people"])
                == set(relationship["people"])
                and conflict["status"] == "UNRESOLVED"
            ):

                conflict["status"] = "RESOLVED"

        self.save()

        return {
            "message": "Conflict resolved",
            "trust": relationship["trust"]
        }

    def end_relationship(self, relationship_id):

        relationship = next(
            (
                r for r in self.relationships
                if r["id"] == relationship_id
            ),
            None
        )

        if not relationship:
            return {"error": "Relationship not found"}

        relationship["status"] = "ENDED"

        self.save()

        return {
            "message": "Relationship ended",
            "relationship_id": relationship_id
        }

    def get_social_statistics(self):

        active = [
            r for r in self.relationships
            if r["status"] == "ACTIVE"
        ]

        return {

            "total_relationships": len(self.relationships),

            "active_relationships": len(active),

            "friendships": sum(
                1 for r in active
                if r["type"] == "FRIENDSHIP"
            ),

            "romantic_relationships": sum(
                1 for r in active
                if r["type"] == "ROMANTIC"
            ),

            "conflicts": len(self.conflicts),

            "interactions": len(self.interactions)

        }

    def save(self):

        self.population["citizens"] = self.citizens

        save_json(
            CITIZENS_FILE,
            self.population
        )

        save_json(
            RELATIONSHIPS_FILE,
            self.database
        )


if __name__ == "__main__":

    engine = RelationshipEngine()

    print("AI LIFEVERSE SOCIAL ENGINE")

    print(json.dumps(
        engine.get_social_statistics(),
        indent=4
    ))
