import json
import os
import random
import uuid
from datetime import datetime, timezone


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(ROOT, "data")

ENVIRONMENT_FILE = os.path.join(
    DATA_DIR,
    "environment.json"
)


WEATHER_TYPES = [
    "SUNNY",
    "CLOUDY",
    "RAINY",
    "WINDY",
    "STORMY",
    "FOGGY"
]

SEASONS = [
    "SPRING",
    "SUMMER",
    "MONSOON",
    "WINTER"
]


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


class EnvironmentEngine:

    def __init__(self):

        self.environment = load_json(
            ENVIRONMENT_FILE,
            {
                "weather": "SUNNY",
                "temperature": 28,
                "humidity": 55,
                "pollution": 10,
                "rainfall": 0,
                "wind_speed": 8,
                "season": "SPRING",
                "events": [],
                "daylight": "MORNING"
            }
        )

    def update_weather(self):

        previous = self.environment["weather"]

        self.environment["weather"] = random.choices(
            WEATHER_TYPES,
            weights=[35, 20, 20, 10, 10, 5]
        )[0]

        if previous != self.environment["weather"]:

            self.record_event(
                "WEATHER_CHANGE",
                f"Weather changed from {previous} "
                f"to {self.environment['weather']}"
            )

        return self.environment["weather"]

    def update_temperature(self):

        weather = self.environment["weather"]

        season = self.environment["season"]

        temperature = {
            "SPRING": 26,
            "SUMMER": 34,
            "MONSOON": 28,
            "WINTER": 20
        }.get(season, 27)

        variation = random.randint(-4, 4)

        if weather == "RAINY":
            variation -= 4

        elif weather == "STORMY":
            variation -= 6

        elif weather == "SUNNY":
            variation += 3

        self.environment["temperature"] = max(
            0,
            min(50, temperature + variation)
        )

    def update_humidity(self):

        weather = self.environment["weather"]

        humidity = random.randint(35, 85)

        if weather in ["RAINY", "STORMY", "FOGGY"]:
            humidity = min(100, humidity + 15)

        self.environment["humidity"] = humidity

    def update_rainfall(self):

        weather = self.environment["weather"]

        rainfall = 0

        if weather == "RAINY":
            rainfall = random.randint(5, 25)

        elif weather == "STORMY":
            rainfall = random.randint(20, 60)

        self.environment["rainfall"] = rainfall

    def update_pollution(self):

        current = self.environment["pollution"]

        change = random.randint(-2, 3)

        if self.environment["weather"] == "RAINY":
            change -= 3

        self.environment["pollution"] = max(
            0,
            min(100, current + change)
        )

    def update_season(self, simulation_day):

        year_day = (simulation_day - 1) % 365

        if year_day < 90:
            season = "SPRING"

        elif year_day < 180:
            season = "SUMMER"

        elif year_day < 270:
            season = "MONSOON"

        else:
            season = "WINTER"

        self.environment["season"] = season

    def update_daylight(self, hour):

        if 5 <= hour < 12:
            period = "MORNING"

        elif 12 <= hour < 17:
            period = "AFTERNOON"

        elif 17 <= hour < 20:
            period = "EVENING"

        else:
            period = "NIGHT"

        self.environment["daylight"] = period

        return period

    def generate_natural_event(self, simulation_day):

        event = None

        # Low-probability fictional simulation events.
        if random.random() < 0.002:

            event_type = random.choice([
                "HEAVY_RAIN",
                "HEATWAVE",
                "STRONG_WINDS",
                "MINOR_EARTHQUAKE",
                "FLOOD_WARNING"
            ])

            event = {

                "id": str(uuid.uuid4()),

                "type": event_type,

                "day": simulation_day,

                "status": "ACTIVE",

                "description": (
                    f"{event_type.replace('_', ' ').title()} "
                    "reported in Nova City."
                )

            }

            self.environment["events"].append(event)

            self.environment["events"] = (
                self.environment["events"][-100:]
            )

        return event

    def record_event(self, event_type, description):

        self.environment["events"].append({

            "id": str(uuid.uuid4()),

            "type": event_type,

            "description": description,

            "timestamp": datetime.now(
                timezone.utc
            ).isoformat()

        })

        self.environment["events"] = (
            self.environment["events"][-100:]
        )

    def advance_day(
        self,
        simulation_day,
        hour=12
    ):

        self.update_season(simulation_day)

        self.update_weather()

        self.update_temperature()

        self.update_humidity()

        self.update_rainfall()

        self.update_pollution()

        self.update_daylight(hour)

        natural_event = self.generate_natural_event(
            simulation_day
        )

        self.save()

        return {
            "day": simulation_day,
            "weather": self.environment["weather"],
            "temperature": self.environment["temperature"],
            "humidity": self.environment["humidity"],
            "rainfall": self.environment["rainfall"],
            "pollution": self.environment["pollution"],
            "season": self.environment["season"],
            "daylight": self.environment["daylight"],
            "natural_event": natural_event
        }

    def get_status(self):

        return self.environment

    def save(self):

        save_json(
            ENVIRONMENT_FILE,
            self.environment
        )


if __name__ == "__main__":

    engine = EnvironmentEngine()

    result = engine.advance_day(
        simulation_day=1,
        hour=12
    )

    print("AI LIFEVERSE ENVIRONMENT ENGINE")

    print(json.dumps(
        result,
        indent=4
    ))
