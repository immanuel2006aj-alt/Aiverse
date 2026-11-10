import json
import os
import uuid
import random
from datetime import datetime, timezone


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(ROOT, "data")

CITIZENS_FILE = os.path.join(DATA_DIR, "citizens.json")
ECONOMY_FILE = os.path.join(DATA_DIR, "economy.json")


CAREERS = {
    "Teacher": 25000,
    "Engineer": 45000,
    "Doctor": 60000,
    "Farmer": 18000,
    "Entrepreneur": 35000,
    "Developer": 50000,
    "Artist": 22000,
    "Banker": 40000,
    "Researcher": 42000,
    "Designer": 30000,
    "Accountant": 32000,
    "Business Owner": 40000
}


DAILY_EXPENSES = {
    "food": 150,
    "transport": 50,
    "utilities": 75,
    "personal": 50
}


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


class EconomyEngine:

    def __init__(self):

        self.population = load_json(
            CITIZENS_FILE,
            {"citizens": [], "families": []}
        )

        self.citizens = self.population.get("citizens", [])

        self.economy = load_json(
            ECONOMY_FILE,
            {
                "currency": "NOVA CREDITS",
                "total_transactions": 0,
                "businesses": [],
                "transactions": [],
                "tax_revenue": 0,
                "total_money_created": 0
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

    def create_wallet(self, citizen):

        citizen.setdefault("wealth", 1000)

        citizen.setdefault("bank_balance", 0)

        citizen.setdefault("salary", 0)

        citizen.setdefault("employment_status", "UNEMPLOYED")

    def record_transaction(
        self,
        citizen_id,
        transaction_type,
        amount,
        description
    ):

        transaction = {
            "id": str(uuid.uuid4()),
            "citizen_id": citizen_id,
            "type": transaction_type,
            "amount": amount,
            "description": description,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat()
        }

        self.economy["transactions"].append(transaction)

        self.economy["transactions"] = (
            self.economy["transactions"][-500:]
        )

        self.economy["total_transactions"] += 1

    def find_job(self, citizen):

        interests = citizen.get("career_interest", [])

        available_jobs = [
            job for job in interests
            if job in CAREERS
        ]

        if not available_jobs:
            return random.choice(list(CAREERS.keys()))

        return random.choice(available_jobs)

    def employ_citizen(self, citizen_id):

        citizen = self.find_citizen(citizen_id)

        if not citizen:
            return {"error": "Citizen not found"}

        if not citizen.get("alive", False):
            return {"error": "Citizen is deceased"}

        if citizen.get("age", 0) < 18:
            return {"error": "Citizen is not an adult"}

        self.create_wallet(citizen)

        if citizen["employment_status"] == "EMPLOYED":
            return {"error": "Citizen already employed"}

        job = self.find_job(citizen)

        salary = CAREERS[job]

        citizen["career"] = job

        citizen["salary"] = salary

        citizen["employment_status"] = "EMPLOYED"

        citizen["employer_id"] = "CITY_EMPLOYMENT"

        self.record_transaction(
            citizen_id,
            "EMPLOYMENT",
            salary,
            f"Employed as {job}"
        )

        self.save()

        return {
            "citizen": citizen["name"],
            "job": job,
            "monthly_salary": salary
        }

    def employ_population(self):

        results = []

        for citizen in self.citizens:

            if not citizen.get("alive", False):
                continue

            if citizen.get("age", 0) < 18:
                continue

            if citizen.get("employment_status") == "EMPLOYED":
                continue

            results.append(
                self.employ_citizen(citizen["id"])
            )

        return results

    def pay_salary(self, simulation_day):

        if simulation_day % 30 != 0:
            return []

        payments = []

        for citizen in self.citizens:

            if not citizen.get("alive", False):
                continue

            if citizen.get("employment_status") != "EMPLOYED":
                continue

            salary = citizen.get("salary", 0)

            if salary <= 0:
                continue

            self.create_wallet(citizen)

            citizen["wealth"] += salary

            payments.append({
                "citizen": citizen["name"],
                "salary": salary
            })

            self.record_transaction(
                citizen["id"],
                "SALARY",
                salary,
                "Monthly salary payment"
            )

        return payments

    def daily_expenses(self, simulation_day):

        expenses = []

        for citizen in self.citizens:

            if not citizen.get("alive", False):
                continue

            self.create_wallet(citizen)

            if citizen.get("age", 0) < 18:
                continue

            total = sum(DAILY_EXPENSES.values())

            paid = min(
                citizen["wealth"],
                total
            )

            citizen["wealth"] -= paid

            expenses.append({
                "citizen": citizen["name"],
                "amount": paid,
                "day": simulation_day
            })

            self.record_transaction(
                citizen["id"],
                "DAILY_EXPENSE",
                paid,
                "Daily living expenses"
            )

        return expenses

    def create_business(
        self,
        owner_id,
        business_name,
        business_type,
        investment
    ):

        owner = self.find_citizen(owner_id)

        if not owner:
            return {"error": "Owner not found"}

        if not owner.get("alive", False):
            return {"error": "Owner is deceased"}

        if owner.get("age", 0) < 18:
            return {"error": "Owner must be an adult"}

        if not isinstance(business_name, str) or not business_name.strip():
            return {"error": "Invalid business name"}

        if business_type not in [
            "Retail",
            "Technology",
            "Agriculture",
            "Healthcare",
            "Education",
            "Food",
            "Finance",
            "Manufacturing"
        ]:
            return {"error": "Invalid business type"}

        if investment <= 0 or investment > owner.get("wealth", 0):
            return {"error": "Invalid investment"}

        owner["wealth"] -= investment

        business = {
            "id": str(uuid.uuid4()),
            "name": business_name.strip()[:80],
            "type": business_type,
            "owner_id": owner_id,
            "capital": investment,
            "employees": [],
            "revenue": 0,
            "status": "ACTIVE",
            "created_at": datetime.now(
                timezone.utc
            ).isoformat()
        }

        self.economy["businesses"].append(business)

        self.record_transaction(
            owner_id,
            "BUSINESS_INVESTMENT",
            investment,
            f"Started {business_name}"
        )

        self.save()

        return business

    def pay_tax(self, citizen_id, tax_rate=0.05):

        citizen = self.find_citizen(citizen_id)

        if not citizen:
            return {"error": "Citizen not found"}

        if not citizen.get("alive", False):
            return {"error": "Citizen is deceased"}

        self.create_wallet(citizen)

        if not 0 <= tax_rate <= 0.5:
            return {"error": "Invalid tax rate"}

        tax = int(
            citizen["wealth"] * tax_rate
        )

        citizen["wealth"] -= tax

        self.economy["tax_revenue"] += tax

        self.record_transaction(
            citizen_id,
            "TAX",
            tax,
            "Civilization tax payment"
        )

        self.save()

        return {
            "citizen": citizen["name"],
            "tax_paid": tax
        }

    def get_statistics(self):

        living = [
            c for c in self.citizens
            if c.get("alive", False)
        ]

        total_wealth = sum(
            c.get("wealth", 0)
            + c.get("bank_balance", 0)
            for c in living
        )

        employed = sum(
            1 for c in living
            if c.get("employment_status") == "EMPLOYED"
        )

        return {
            "currency": self.economy["currency"],
            "population": len(living),
            "employed": employed,
            "unemployed": len(living) - employed,
            "businesses": len(self.economy["businesses"]),
            "total_wealth": total_wealth,
            "tax_revenue": self.economy["tax_revenue"],
            "transactions": self.economy["total_transactions"]
        }

    def save(self):

        self.population["citizens"] = self.citizens

        save_json(CITIZENS_FILE, self.population)

        save_json(ECONOMY_FILE, self.economy)


if __name__ == "__main__":

    engine = EconomyEngine()

    print("AI LIFEVERSE ECONOMY ENGINE")

    print("Initial employment started...")

    results = engine.employ_population()

    print("New employees:", len(results))

    print("\nECONOMY STATISTICS")

    print(json.dumps(
        engine.get_statistics(),
        indent=4
    ))
