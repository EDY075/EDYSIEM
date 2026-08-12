"""Golden-contract tests for EDY Shield telemetry schema 1.0."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from edysiem.api.ingestion_schemas import (
    MAX_BATCH_BYTES,
    MAX_EVENT_BYTES,
    SCHEMA_VERSION_V1,
    ShieldEventBatchV1,
    ShieldEventV1,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "shield_events" / "v1"
VALID_FIXTURES = FIXTURES / "valid"
INVALID_FIXTURES = FIXTURES / "invalid"
CONTRACT_DOC = ROOT / "docs" / "integration" / "EVENT_CONTRACT_V1.md"

VALID_CASES = {
    "file_created.json": "shield.fim.file.added",
    "file_modified.json": "shield.fim.file.modified",
    "file_deleted.json": "shield.fim.file.removed",
    "hash_changed.json": "shield.hash.mismatch",
    "baseline_created.json": "shield.fim.baseline.created",
    "scan_completed.json": "shield.fim.scan.completed",
    "critical_security_alert.json": "shield.alert.created",
}
DOC_EXAMPLES = {
    "Arquivo modificado": "file_modified.json",
    "Hash alterado/diferente do esperado": "hash_changed.json",
    "Novo arquivo": "file_created.json",
    "Arquivo removido": "file_deleted.json",
    "Scan concluído": "scan_completed.json",
    "Alerta crítico local": "critical_security_alert.json",
    "Baseline criada": "baseline_created.json",
}


def load_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def valid_event(name: str = "baseline_created.json") -> dict[str, object]:
    return load_object(VALID_FIXTURES / name)


def object_field(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload[key]
    assert isinstance(value, dict)
    return value


def valid_batch(events: list[dict[str, object]] | None = None) -> dict[str, object]:
    return {
        "batch_id": "e1b5d849-a2d8-45f3-b679-92a13584bc08",
        "sent_at": "2026-08-11T18:50:00.000Z",
        "events": events if events is not None else [valid_event()],
    }


@pytest.mark.parametrize(("filename", "event_type"), VALID_CASES.items())
def test_all_seven_valid_fixtures_match_the_contract(filename: str, event_type: str) -> None:
    payload = load_object(VALID_FIXTURES / filename)

    event = ShieldEventV1.model_validate(payload)

    assert event.schema_version == SCHEMA_VERSION_V1
    assert event.event_type == event_type
    assert event.model_dump(mode="json", exclude_none=True) == payload


def test_critical_security_alert_is_explicitly_critical() -> None:
    event = ShieldEventV1.model_validate(valid_event("critical_security_alert.json"))

    assert event.event_type == "shield.alert.created"
    assert event.severity == "critical"


@pytest.mark.parametrize("path", sorted(INVALID_FIXTURES.glob("*.json")))
def test_invalid_fixtures_are_rejected(path: Path) -> None:
    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate(load_object(path))


def test_documentation_examples_equal_versioned_fixtures() -> None:
    markdown = CONTRACT_DOC.read_text(encoding="utf-8")
    pattern = re.compile(
        r"^### 13\.\d+ (?P<title>[^\n]+)\n.*?```json\s*"
        r"(?P<payload>\{.*?\})\s*```",
        re.MULTILINE | re.DOTALL,
    )
    examples = {
        match.group("title"): json.loads(match.group("payload"))
        for match in pattern.finditer(markdown)
    }

    assert set(examples) == set(DOC_EXAMPLES)
    for title, fixture_name in DOC_EXAMPLES.items():
        assert examples[title] == load_object(VALID_FIXTURES / fixture_name)
        ShieldEventV1.model_validate(examples[title])


def test_generated_schema_freezes_required_root_fields_and_version() -> None:
    schema = ShieldEventV1.model_json_schema()

    assert set(schema["required"]) == {
        "event_id",
        "schema_version",
        "timestamp",
        "sequence",
        "source",
        "event_type",
        "severity",
        "asset",
        "evidence",
        "metadata",
    }
    assert schema["properties"]["schema_version"]["const"] == "1.0"
    assert schema["additionalProperties"] is False


def test_optional_fields_must_be_omitted_and_extensions_are_namespaced() -> None:
    payload = valid_event()
    asset = object_field(payload, "asset")
    asset.pop("ip")
    asset.pop("os")
    payload["metadata"] = {"x_lab_scenario": {"name": "offline"}}

    event = ShieldEventV1.model_validate(payload)

    assert event.asset.ip is None
    assert event.metadata.model_extra == {"x_lab_scenario": {"name": "offline"}}


@pytest.mark.parametrize("severity", ["info", "low", "medium", "high", "critical"])
def test_all_severity_values_are_accepted(severity: str) -> None:
    payload = valid_event()
    payload["severity"] = severity

    assert ShieldEventV1.model_validate(payload).severity == severity


def test_remaining_event_types_are_executable() -> None:
    verified = valid_event("hash_changed.json")
    verified["event_type"] = "shield.hash.verified"
    object_field(verified, "evidence")["baseline_status"] = "matched"

    updated = valid_event("critical_security_alert.json")
    updated["event_type"] = "shield.alert.updated"
    details = object_field(object_field(updated, "evidence"), "details")
    details.update({"previous_status": "new", "current_status": "acknowledged"})

    assert ShieldEventV1.model_validate(verified).event_type == "shield.hash.verified"
    assert ShieldEventV1.model_validate(updated).event_type == "shield.alert.updated"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("event_id", "not-a-uuid"),
        ("event_id", "D0A4C738-91C7-44F2-A568-81F02473AB07"),
        ("event_id", "d0a4c738-91c7-14f2-a568-81f02473ab07"),
        ("timestamp", "2026-02-30T12:00:00Z"),
        ("sequence", 0),
    ],
)
def test_invalid_root_formats_are_rejected(field: str, value: object) -> None:
    payload = valid_event()
    payload[field] = value

    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate(payload)


def test_future_timestamp_is_rejected() -> None:
    payload = valid_event()
    future = datetime.now(UTC) + timedelta(minutes=6)
    payload["timestamp"] = future.isoformat(timespec="seconds").replace("+00:00", "Z")

    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("product_version", "2"),
        ("instance_id", "invalid"),
        ("component", "network"),
        ("product", "other-agent"),
    ],
)
def test_invalid_source_values_are_rejected(field: str, value: object) -> None:
    payload = valid_event()
    object_field(payload, "source")[field] = value

    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate(payload)


@pytest.mark.parametrize(("field", "value"), [("ip", "999.1.1.1"), ("hostname", "")])
def test_invalid_asset_values_are_rejected(field: str, value: object) -> None:
    payload = valid_event()
    object_field(payload, "asset")[field] = value

    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate(payload)


def test_unknown_fields_are_rejected_outside_extension_points() -> None:
    payload = valid_event()
    object_field(payload, "source")["extra"] = "no"

    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate(payload)

    payload = valid_event()
    object_field(payload, "evidence")["extra"] = "no"
    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate(payload)

    payload = valid_event()
    payload["metadata"] = {"custom": "missing-prefix"}
    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate(payload)


@pytest.mark.parametrize(
    "mutation",
    [
        {"details": None},
        {"details": []},
        {"details": {f"key_{index}": index for index in range(33)}},
        {"details": {"nested": {"a": {"b": {"c": {"d": "too deep"}}}}}},
        {"details": {"null_value": None}},
        {"details": {"long": "x" * 1025}},
        {"mtime": "2026-08-11 18:40:00", "details": {"file_count": 1243}},
    ],
)
def test_invalid_evidence_extensions_are_rejected(mutation: dict[str, object]) -> None:
    payload = valid_event()
    object_field(payload, "evidence").update(mutation)

    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate(payload)


@pytest.mark.parametrize(
    "file_path",
    [
        "/etc/shadow",
        "C:/Users/alice/secret.txt",
        "Windows\\System32\\hosts",
        "../secret.txt",
        "safe/../secret.txt",
        "./relative.txt",
        "safe//file.txt",
        "safe/\x00file.txt",
    ],
)
def test_file_path_must_be_canonical_and_relative(file_path: str) -> None:
    payload = valid_event("file_modified.json")
    object_field(payload, "evidence")["file_path"] = file_path

    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate(payload)


@pytest.mark.parametrize("non_finite", [float("nan"), float("inf"), float("-inf")])
def test_extensions_reject_non_finite_numbers(non_finite: float) -> None:
    payload = valid_event()
    object_field(payload, "evidence")["details"] = {
        "file_count": 1243,
        "score": non_finite,
    }

    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate(payload)


def test_non_json_evidence_value_is_rejected() -> None:
    payload = valid_event()
    object_field(payload, "evidence")["details"] = {"object": object()}

    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate(payload)


@pytest.mark.parametrize(
    "metadata",
    [
        {f"x_key_{index}": index for index in range(33)},
        {"correlation_id": None},
        {"x_long": "x" * 1025},
        {"tags": ["x" * 65]},
        {"tags": [f"tag-{index}" for index in range(33)]},
    ],
)
def test_invalid_metadata_is_rejected(metadata: dict[str, object]) -> None:
    payload = valid_event()
    payload["metadata"] = metadata

    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate(payload)


def test_extension_size_limits_are_enforced() -> None:
    payload = valid_event()
    details = {f"key_{index}": "x" * 1000 for index in range(17)}
    object_field(payload, "evidence")["details"] = details
    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate(payload)

    payload = valid_event()
    payload["metadata"] = {f"x_key_{index}": "x" * 1000 for index in range(17)}
    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate(payload)


def test_hash_validation_requires_algorithm_length_hex_and_real_change() -> None:
    payload = valid_event("file_modified.json")
    evidence = object_field(payload, "evidence")
    evidence.pop("hash_algorithm")
    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate(payload)

    payload = valid_event("file_modified.json")
    object_field(payload, "evidence")["current_hash"] = "a" * 63
    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate(payload)

    payload = valid_event("file_modified.json")
    object_field(payload, "evidence")["current_hash"] = "G" * 64
    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate(payload)

    payload = valid_event("file_modified.json")
    evidence = object_field(payload, "evidence")
    evidence["current_hash"] = evidence["previous_hash"]
    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate(payload)


@pytest.mark.parametrize(
    ("filename", "field"),
    [
        ("baseline_created.json", "baseline_id"),
        ("scan_completed.json", "scan_id"),
        ("file_created.json", "current_hash"),
        ("file_modified.json", "previous_hash"),
        ("file_deleted.json", "previous_hash"),
        ("hash_changed.json", "file_path"),
    ],
)
def test_conditional_required_evidence_fields(filename: str, field: str) -> None:
    payload = valid_event(filename)
    object_field(payload, "evidence").pop(field)

    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate(payload)


@pytest.mark.parametrize(
    ("filename", "status"),
    [
        ("baseline_created.json", "modified"),
        ("file_created.json", "matched"),
        ("file_modified.json", "added"),
        ("file_deleted.json", "modified"),
        ("hash_changed.json", "created"),
    ],
)
def test_conditional_baseline_status(filename: str, status: str) -> None:
    payload = valid_event(filename)
    object_field(payload, "evidence")["baseline_status"] = status

    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate(payload)


def test_removed_file_forbids_current_hash() -> None:
    payload = valid_event("file_deleted.json")
    object_field(payload, "evidence")["current_hash"] = "a" * 64

    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate(payload)


@pytest.mark.parametrize(
    ("filename", "detail"),
    [("baseline_created.json", "file_count"), ("scan_completed.json", "duration_ms")],
)
def test_required_numeric_details(filename: str, detail: str) -> None:
    payload = valid_event(filename)
    details = object_field(object_field(payload, "evidence"), "details")
    details[detail] = -1

    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate(payload)


def test_alert_conditional_metadata_and_details() -> None:
    payload = valid_event("critical_security_alert.json")
    object_field(payload, "metadata").pop("rule_id")
    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate(payload)

    payload = valid_event("critical_security_alert.json")
    object_field(object_field(payload, "evidence"), "details").pop("title")
    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate(payload)

    payload = valid_event("critical_security_alert.json")
    payload["event_type"] = "shield.alert.updated"
    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate(payload)


def test_event_and_batch_size_limits_are_executable() -> None:
    oversized_event = valid_event()
    oversized_event["unexpected"] = "x" * MAX_EVENT_BYTES
    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate(oversized_event)

    large_event = valid_event()
    object_field(large_event, "evidence")["details"] = {
        f"key_{index}": "x" * 900 for index in range(12)
    }
    large_event["metadata"] = {f"x_key_{index}": "x" * 900 for index in range(12)}
    oversized_batch = valid_batch([deepcopy(large_event) for _ in range(100)])
    assert len(json.dumps(oversized_batch).encode("utf-8")) > MAX_BATCH_BYTES
    with pytest.raises(ValidationError):
        ShieldEventBatchV1.model_validate(oversized_batch)


def test_batch_envelope_accepts_one_to_one_hundred_events() -> None:
    one = ShieldEventBatchV1.model_validate(valid_batch())
    hundred = ShieldEventBatchV1.model_validate(valid_batch([valid_event()] * 100))

    assert len(one.events) == 1
    assert len(hundred.events) == 100

    with pytest.raises(ValidationError):
        ShieldEventBatchV1.model_validate(valid_batch([]))
    with pytest.raises(ValidationError):
        ShieldEventBatchV1.model_validate(valid_batch([valid_event()] * 101))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("batch_id", "invalid"),
        ("batch_id", "e1b5d849-a2d8-15f3-b679-92a13584bc08"),
        ("sent_at", "2026-08-11 18:50:00"),
    ],
)
def test_invalid_batch_identity_and_timestamp(field: str, value: object) -> None:
    payload = valid_batch()
    payload[field] = value

    with pytest.raises(ValidationError):
        ShieldEventBatchV1.model_validate(payload)


def test_models_reject_non_object_payloads() -> None:
    with pytest.raises(ValidationError):
        ShieldEventV1.model_validate([])
    with pytest.raises(ValidationError):
        ShieldEventBatchV1.model_validate([])
