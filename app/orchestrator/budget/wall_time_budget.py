# app/orchestrator/budget/wall_time_budget.py

import time

class WallTimeBudget:
    def __init__(self):
        self.start_time = time.time()

    def elapsed(self) -> float:
        return time.time() - self.start_time

    def within_budget(self, max_seconds: int) -> bool:
        return self.elapsed() < max_seconds
