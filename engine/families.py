import json
import os
import uuid
from datetime import datetime, timezone


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(ROOT, "data")

CITIZENS_FILE = os.path.join(DATA_DIR, "citizens.json")

FAMILIES_FILE = os.path.join(DATA_DIR, "families.json")


def load_json(path, default=None):

    if not os.path.exists(path):
        return default if default is not None else {}

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path, data):

    os.makedirs(DATA_DIR, exist_ok=True)

    temp_path = path + ".tmp"

    with open(temp_path, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )

    os.replace(temp_path, path)


class FamilyEngine:

    def __init__(self):

        self.population = load_json(
            CITIZENS_FILE,
            {"citizens": [], "families": []}
        )

        self.citizens = self.population.get("citizens", [])

        self.families = self.population.get("families", [])

        self.family_records = load_json(
            FAMILIES_FILE,
            {"families": [], "marriages": [], "inheritances": []}
        )

        self.marriages = self.family_records.get("marriages", [])

        self.inheritances = self.family_records.get("inheritances", [])

    def find_citizen(self, citizen_id):

        for citizen in self.citizens:

            if citizen["id"] == citizen_id:
                return citizen

        return None

    def initialize_families(self):

        existing_ids = {
            family["id"]
            for family in self.family_records["families"]
        }

        for family in self.families:

            if family["id"] in existing_ids:
                continue

            members = family.get("members", [])

            family_record = {

                "id": family["id"],

                "name": family["name"],

                "generation": 1,

                "members": members,

                "parents": [],

                "children": [],

                "marital_history": [],

                "family_wealth": 0,

                "family_status": "ACTIVE",

                "created_day": 1,

                "created_at": datetime.now(
                    timezone.utc
                ).isoformat()

            }

            self.family_records["families"].append(
                family_record
            )

            # Establish initial partner relationships.
            if len(members) >= 2:

                first = self.find_citizen(members[0])

                second = self.find_citizen(members[1])

                if first and second:

                    first["relationships"].append({
                        "citizen_id": second["id"],
                        "type": "PARTNER"
                    })

                    second["relationships"].append({
                        "citizen_id": first["id"],
                        "type": "PARTNER"
                    })

        self.save()

        return self.family_records["families"]

    def create_marriage(
        self,
        citizen_a_id,
        citizen_b_id,
        simulation_day
    ):

        person_a = self.find_citizen(citizen_a_id)

        person_b = self.find_citizen(citizen_b_id)

        if not person_a or not person_b:
            return {"error": "Citizen not found"}

        if citizen_a_id == citizen_b_id:
            return {"error": "Invalid partner selection"}

        if not person_a["alive"] or not person_b["alive"]:
            return {"error": "Both citizens must be alive"}

        if person_a["age"] < 18 or person_b["age"] < 18:
            return {"error": "Both citizens must be adults"}

        if any(
            marriage["status"] == "ACTIVE"
            and (
                citizen_a_id in marriage["partners"]
                or citizen_b_id in marriage["partners"]
            )
            for marriage in self.marriages
        ):
            return {"error": "An active marriage already exists"}

        marriage = {

            "id": str(uuid.uuid4()),

            "partners": [
                citizen_a_id,
                citizen_b_id
            ],

            "status": "ACTIVE",

            "marriage_day": simulation_day,

            "created_at": datetime.now(
                timezone.utc
            ).isoformat()

        }

        self.marriages.append(marriage)

        person_a["relationships"].append({
            "citizen_id": citizen_b_id,
            "type": "SPOUSE"
        })

        person_b["relationships"].append({
            "citizen_id": citizen_a_id,
            "type": "SPOUSE"
        })

        self.save()

        return marriage

    def add_child(
        self,
        parent_a_id,
        parent_b_id,
        child,
        simulation_day
    ):

        parent_a = self.find_citizen(parent_a_id)

        parent_b = self.find_citizen(parent_b_id)

        if not parent_a or not parent_b:
            return {"error": "Parent not found"}

        if not parent_a["alive"] or not parent_b["alive"]:
            return {"error": "Parents must be alive"}

        if parent_a_id == parent_b_id:
            return {"error": "Invalid parent records"}

        if parent_a["age"] < 18 or parent_b["age"] < 18:
            return {"error": "Parents must be adults"}

        if not isinstance(child, dict) or not child.get("id"):
            return {"error": "Invalid child record"}

        if self.find_citizen(child["id"]):
            return {"error": "Citizen already exists"}

        child["family_id"] = parent_a["family_id"]

        child["generation"] = max(
            parent_a.get("generation", 1),
            parent_b.get("generation", 1)
        ) + 1

        child["age"] = 0

        child["alive"] = True

        child["relationships"] = [
            {
                "citizen_id": parent_a_id,
                "type": "PARENT"
            },
            {
                "citizen_id": parent_b_id,
                "type": "PARENT"
            }
        ]

        child["created_day"] = simulation_day

        self.citizens.append(child)

        parent_a["relationships"].append({
            "citizen_id": child["id"],
            "type": "CHILD"
        })

        parent_b["relationships"].append({
            "citizen_id": child["id"],
            "type": "CHILD"
        })

        family = next(
            (
                item for item in self.family_records["families"]
                if item["id"] == parent_a["family_id"]
            ),
            None
        )

        if family:

            family["children"].append(child["id"])

            family["members"].append(child["id"])

        self.save()

        return {
            "message": "Child added to family",
            "child_id": child["id"],
            "generation": child["generation"]
        }

    def record_death(self, citizen_id, simulation_day):

        citizen = self.find_citizen(citizen_id)

        if not citizen:
            return {"error": "Citizen not found"}

        if not citizen["alive"]:
            return {"error": "Citizen already deceased"}

        citizen["alive"] = False

        citizen["death_day"] = simulation_day

        citizen["memory"].append({
            "event": "DEATH",
            "day": simulation_day
        })

        self.save()

        return {
            "message": "Death recorded",
            "citizen": citizen["name"]
        }

    def calculate_family_wealth(self):

        for family in self.family_records["families"]:

            total = 0

            for citizen_id in family["members"]:

                citizen = self.find_citizen(citizen_id)

                if citizen and citizen["alive"]:

                    total += citizen.get("wealth", 0)

            family["family_wealth"] = total

        self.save()

    def create_inheritance(
        self,
        deceased_id,
        heir_id,
        amount,
        simulation_day
    ):

        deceased = self.find_citizen(deceased_id)

        heir = self.find_citizen(heir_id)

        if not deceased or not heir:
            return {"error": "Citizen not found"}

        if deceased["alive"]:
            return {"error": "Inheritance requires a deceased citizen"}

        if not heir["alive"]:
            return {"error": "Heir must be alive"}

        if amount <= 0:
            return {"error": "Invalid inheritance amount"}

        if amount > deceased.get("wealth", 0):
            return {"error": "Insufficient estate balance"}

        deceased["wealth"] -= amount

        heir["wealth"] += amount

        record = {

            "id": str(uuid.uuid4()),

            "deceased": deceased_id,

            "heir": heir_id,

            "amount": amount,

            "simulation_day": simulation_day

        }

        self.inheritances.append(record)

        self.save()

        return record

    def save(self):

        save_json(
            FAMILIES_FILE,
            {
                "families": self.family_records["families"],
                "marriages": self.marriages,
                "inheritances": self.inheritances
            }
        )

        self.population["citizens"] = self.citizens

        save_json(CITIZENS_FILE, self.population)


if __name__ == "__main__":

    engine = FamilyEngine()

    families = engine.initialize_families()

    print("AI LIFEVERSE FAMILY ENGINE")

    print("Families:", len(families))

    print("Marriage records:", len(engine.marriages))

    print("Family system initialized.")
