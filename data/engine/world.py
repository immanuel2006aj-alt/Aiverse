import json
import os
from datetime import datetime, timezone


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_PATH = os.path.join(ROOT, "data", "world.json")
STATE_PATH = os.path.join(ROOT, "data", "world_state.json")


class WorldEngine:

    def __init__(self):

        self.config = self.load_config()
        self.state = self.load_state()

    def load_config(self):

        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            return json.load(file)

    def load_state(self):

        if os.path.exists(STATE_PATH):

            with open(STATE_PATH, "r", encoding="utf-8") as file:
                return json.load(file)

        return self.create_initial_state()

    def create_initial_state(self):

        world = self.config["world"]
        civilization = self.config["civilization"]

        return {

            "world_id": world["id"],

            "world_name": world["name"],

            "city_name": self.config["geography"]["city_name"],

            "status": "CREATED",

            "simulation_day": 1,

            "simulation_year": 1,

            "hour": 6,

            "minute": 0,

            "population": civilization["initial_population"],

            "families": civilization["initial_families"],

            "generation": 1,

            "weather": "SUNNY",

            "created_at": datetime.now(timezone.utc).isoformat(),

            "last_updated": datetime.now(timezone.utc).isoformat()

        }

    def save_state(self):

        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)

        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()

        temp_path = STATE_PATH + ".tmp"

        with open(temp_path, "w", encoding="utf-8") as file:

            json.dump(
                self.state,
                file,
                indent=4,
                ensure_ascii=False
            )

        os.replace(temp_path, STATE_PATH)

    def advance_time(self, minutes=60):

        total_minutes = (
            self.state["hour"] * 60
            + self.state["minute"]
            + minutes
        )

        days_passed, remaining = divmod(total_minutes, 1440)

        self.state["hour"] = remaining // 60

        self.state["minute"] = remaining % 60

        if days_passed > 0:

            self.state["simulation_day"] += days_passed

            self.state["simulation_year"] = (
                (self.state["simulation_day"] - 1) // 365
            ) + 1

        self.update_day_cycle()

        self.save_state()

    def update_day_cycle(self):

        hour = self.state["hour"]

        if 5 <= hour < 12:

            period = "MORNING"

        elif 12 <= hour < 17:

            period = "AFTERNOON"

        elif 17 <= hour < 20:

            period = "EVENING"

        else:

            period = "NIGHT"

        self.state["period"] = period

    def get_world_info(self):

        return {

            "world": self.state["world_name"],

            "city": self.state["city_name"],

            "status": self.state["status"],

            "day": self.state["simulation_day"],

            "year": self.state["simulation_year"],

            "time": (
                f'{self.state["hour"]:02d}:'
                f'{self.state["minute"]:02d}'
            ),

            "period": self.state.get("period", "MORNING"),

            "population": self.state["population"],

            "families": self.state["families"],

            "generation": self.state["generation"]

        }


if __name__ == "__main__":

    world = WorldEngine()

    print("AI LIFEVERSE WORLD ENGINE")

    print(json.dumps(
        world.get_world_info(),
        indent=4
    ))
