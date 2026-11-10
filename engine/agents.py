import json
import random
import uuid
import os
from datetime import datetime, timezone


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CITIZENS_PATH = os.path.join(ROOT, "data", "citizens.json")


FIRST_NAMES = [
    "Arun", "Meera", "Kavin", "Priya",
    "David", "Sarah", "Daniel", "Anu",
    "Vijay", "Divya", "John", "Mary",
    "Rahul", "Nila", "Thomas", "Esther",
    "Adrian", "Sophia", "Michael", "Emma",
    "Nathan", "Olivia", "Samuel", "Grace"
]


LAST_NAMES = [
    "Thomas", "Joseph", "Kumar", "Raj",
    "Williams", "Martin", "Anderson",
    "Wilson", "David", "James",
    "Benjamin", "Christopher"
]


PERSONALITIES = [
    "Ambitious",
    "Kind",
    "Introverted",
    "Extroverted",
    "Creative",
    "Analytical",
    "Adventurous",
    "Calm",
    "Competitive",
    "Empathetic",
    "Curious",
    "Independent"
]


GOALS = [
    "Become financially independent",
    "Build a successful career",
    "Start a business",
    "Help the community",
    "Become highly educated",
    "Travel the world",
    "Build a happy family",
    "Become an artist",
    "Discover new knowledge",
    "Become a respected leader"
]


SKILLS = [
    "Communication",
    "Programming",
    "Management",
    "Creativity",
    "Agriculture",
    "Teaching",
    "Healthcare",
    "Finance",
    "Engineering",
    "Research",
    "Marketing",
    "Design"
]


CAREERS = [
    "Teacher",
    "Engineer",
    "Doctor",
    "Farmer",
    "Entrepreneur",
    "Developer",
    "Artist",
    "Banker",
    "Researcher",
    "Designer",
    "Accountant",
    "Business Owner"
]


def random_trait():
    return random.randint(30, 100)


def create_citizen(family_id, index):

    gender = random.choice(["Male", "Female"])

    citizen = {

        "id": str(uuid.uuid4()),

        "name": (
            random.choice(FIRST_NAMES)
            + " "
            + random.choice(LAST_NAMES)
        ),

        "family_id": family_id,

        "gender": gender,

        "age": random.randint(21, 40),

        "generation": 1,

        "alive": True,

        "personality": random.sample(
            PERSONALITIES, 3
        ),

        "intelligence": random_trait(),

        "creativity": random_trait(),

        "emotional_intelligence": random_trait(),

        "decision_style": random.choice([
            "Risk Taker",
            "Balanced",
            "Cautious"
        ]),

        "career": random.choice(CAREERS),

        "career_interest": random.sample(
            CAREERS, 3
        ),

        "skills": {
            skill: random.randint(1, 5)
            for skill in random.sample(SKILLS, 4)
        },

        "goals": random.sample(GOALS, 3),

        "health": 100,

        "happiness": random.randint(40, 80),

        "wealth": random.randint(500, 3000),

        "energy": 100,

        "relationships": [],

        "memory": [],

        "daily_routine": [
            "Wake up",
            "Have breakfast",
            "Work or study",
            "Social interaction",
            "Dinner",
            "Sleep"
        ],

        "created_at": datetime.now(
            timezone.utc
        ).isoformat()

    }

    return citizen


def create_population(families_count=100):

    citizens = []
    families = []

    for index in range(families_count):

        family_id = str(uuid.uuid4())

        members = []

        for _ in range(2):

            citizen = create_citizen(
                family_id,
                len(citizens)
            )

            citizens.append(citizen)

            members.append(citizen["id"])

        families.append({

            "id": family_id,

            "name": f"Family {index + 1}",

            "members": members,

            "generation": 1,

            "created_day": 1

        })

    return citizens, families


def save_population(citizens, families):

    os.makedirs(
        os.path.dirname(CITIZENS_PATH),
        exist_ok=True
    )

    data = {

        "total_citizens": len(citizens),

        "total_families": len(families),

        "citizens": citizens,

        "families": families

    }

    with open(
        CITIZENS_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


def load_population():

    if not os.path.exists(CITIZENS_PATH):

        return [], []

    with open(
        CITIZENS_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    return (
        data.get("citizens", []),
        data.get("families", [])
    )


if __name__ == "__main__":

    citizens, families = create_population(100)

    save_population(citizens, families)

    print("AI LIFEVERSE POPULATION CREATED")

    print("Families:", len(families))

    print("Citizens:", len(citizens))

    print("\nFIRST CITIZEN")

    print(json.dumps(
        citizens[0],
        indent=4
    ))
