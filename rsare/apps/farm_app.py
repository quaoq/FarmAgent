from rsare.scenarios.time_manager import TimeManager
import random
from typing import Any

class App:
    def __init__(self, name: str | None = None, *args, **kwargs):
        super().__init__()
        self.name = self.__class__.__name__ if name is None else name
        self.time_manager = TimeManager()
        self.set_seed(0)

    def register_time_manager(self, time_manager: TimeManager):
        self.time_manager = time_manager

    def set_seed(self, seed: int) -> None:
        # Derive a new seed from the combination of the input seed and app name
        # This ensures each app instance gets a unique but deterministic seed
        combined_seed = f"{seed}_{self.name}"
        self.seed = hash(combined_seed) % (2**32)
        self.rng = random.Random(self.seed)

    def get_state(self) -> dict[str, Any] | None:
        pass

    def load_state(self, state_dict: dict[str, Any]):
        pass

    def reset(self):
        self.rng = random.Random(self.seed)