
import yaml


def load_companies(path="config/companies.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["companies"]
