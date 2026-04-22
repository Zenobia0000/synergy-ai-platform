"""
Tests that verify scenario fixture JSON files use only valid field_ids
as defined in data/schemas/questionnaire.json.
"""
import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "scenarios"
SCHEMA_PATH = Path(__file__).parents[2] / "data" / "schemas" / "questionnaire.json"


def _all_field_ids() -> set[str]:
    data = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    ids = set()
    for section in data["sections"]:
        for field in section["fields"]:
            ids.add(field["field_id"])
    return ids


def _required_field_ids() -> set[str]:
    data = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    ids = set()
    for section in data["sections"]:
        for field in section["fields"]:
            if field.get("required"):
                ids.add(field["field_id"])
    return ids


@pytest.mark.parametrize(
    "fixture_name",
    [
        "male_45_overweight",
        "female_35_sleep_issue",
        "senior_62_chronic",
    ],
)
def test_scenario_fixture_uses_valid_field_ids(fixture_name: str) -> None:
    """All field_ids in fixture must exist in questionnaire schema."""
    fixture_path = FIXTURES_DIR / f"{fixture_name}.json"
    assert fixture_path.exists(), f"Fixture file not found: {fixture_path}"

    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert "answers" in fixture, "Fixture must have 'answers' key"

    valid_ids = _all_field_ids()
    used_ids = set(fixture["answers"].keys())
    invalid = used_ids - valid_ids
    assert not invalid, (
        f"Fixture '{fixture_name}' uses unknown field_ids: {sorted(invalid)}\n"
        f"Valid field_ids: {sorted(valid_ids)}"
    )


@pytest.mark.parametrize(
    "fixture_name",
    [
        "male_45_overweight",
        "female_35_sleep_issue",
        "senior_62_chronic",
    ],
)
def test_scenario_fixture_covers_required_fields(fixture_name: str) -> None:
    """All required fields in schema must be present in fixture answers."""
    fixture_path = FIXTURES_DIR / f"{fixture_name}.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

    required_ids = _required_field_ids()
    used_ids = set(fixture["answers"].keys())
    missing = required_ids - used_ids
    assert not missing, (
        f"Fixture '{fixture_name}' is missing required field_ids: {sorted(missing)}"
    )


@pytest.mark.parametrize(
    "fixture_name",
    [
        "male_45_overweight",
        "female_35_sleep_issue",
        "senior_62_chronic",
    ],
)
def test_scenario_fixture_has_scenario_metadata(fixture_name: str) -> None:
    """Fixture should have a _scenario description for documentation."""
    fixture_path = FIXTURES_DIR / f"{fixture_name}.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert "_scenario" in fixture, (
        f"Fixture '{fixture_name}' should have '_scenario' description key"
    )
    assert fixture["_scenario"], "_scenario description must not be empty"
