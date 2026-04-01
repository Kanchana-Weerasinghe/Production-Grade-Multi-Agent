import yaml
from .models import Budget

def load_budget(profile: str = "default") -> Budget:
    with open("app/policies/budget_profiles.yaml") as f:
        data = yaml.safe_load(f)
    return Budget(**data[profile])
