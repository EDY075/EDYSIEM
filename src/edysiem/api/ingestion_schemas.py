"""Executable EDY Shield event contract v1.

This module freezes the external payload boundary without implementing transport,
authentication, persistence, or an HTTP endpoint.  The normative documentation lives in
``docs/integration/EVENT_CONTRACT_V1.md``.
"""

from __future__ import annotations

import ipaddress
import json
import re
from datetime import UTC, datetime, timedelta
from math import isfinite
from typing import ClassVar, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SCHEMA_VERSION_V1 = "1.0"
MAX_BATCH_BYTES = 1024 * 1024
MAX_EVENT_BYTES = 64 * 1024
MAX_EXTENSION_BYTES = 16 * 1024
MAX_EXTENSION_KEYS = 32
MAX_EXTENSION_DEPTH = 4
MAX_GENERIC_STRING_LENGTH = 1024

EventTypeV1 = Literal[
    "shield.fim.baseline.created",
    "shield.fim.scan.completed",
    "shield.fim.file.added",
    "shield.fim.file.modified",
    "shield.fim.file.removed",
    "shield.hash.verified",
    "shield.hash.mismatch",
    "shield.alert.created",
    "shield.alert.updated",
]
SeverityV1 = Literal["info", "low", "medium", "high", "critical"]
SourceComponentV1 = Literal["fim", "hash_checker", "scanner", "alert_engine"]
HashAlgorithmV1 = Literal["md5", "sha1", "sha256", "sha512"]
BaselineStatusV1 = Literal[
    "not_applicable",
    "created",
    "matched",
    "added",
    "modified",
    "removed",
    "invalid",
]

_UTC_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"
)
_SEMVER_RE = re.compile(
    r"^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
_HEX_RE = re.compile(r"^[0-9a-f]+$")
_HASH_LENGTHS = {"md5": 32, "sha1": 40, "sha256": 64, "sha512": 128}


def _serialized_size(value: object) -> int:
    """Return compact UTF-8 JSON size for an already decoded payload."""

    try:
        encoded = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("value must contain JSON-compatible data") from exc
    return len(encoded)


def _validate_uuid(value: str, *, version: int | None = None) -> str:
    try:
        parsed = UUID(value)
    except (AttributeError, ValueError) as exc:
        raise ValueError("value must be a canonical UUID") from exc
    if str(parsed) != value:
        raise ValueError("UUID must use canonical lowercase representation")
    if version is not None and parsed.version != version:
        raise ValueError(f"UUID must be version {version}")
    return value


def _parse_utc_timestamp(value: str) -> datetime:
    if not _UTC_TIMESTAMP_RE.fullmatch(value):
        raise ValueError("timestamp must be RFC 3339 UTC and end in Z")
    try:
        return datetime.fromisoformat(f"{value[:-1]}+00:00")
    except ValueError as exc:
        raise ValueError("timestamp is not a valid calendar instant") from exc


def _validate_extension_tree(value: object, *, depth: int = 0) -> None:
    if depth > MAX_EXTENSION_DEPTH:
        raise ValueError(f"extension depth must be <= {MAX_EXTENSION_DEPTH}")
    if value is None:
        raise ValueError("null is not allowed; omit unknown or inapplicable fields")
    if isinstance(value, str):
        if len(value) > MAX_GENERIC_STRING_LENGTH:
            raise ValueError(
                f"extension strings must be <= {MAX_GENERIC_STRING_LENGTH} characters"
            )
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("extension keys must be strings")
            if len(key) > MAX_GENERIC_STRING_LENGTH:
                raise ValueError("extension key is too long")
            _validate_extension_tree(item, depth=depth + 1)
        return
    if isinstance(value, list):
        for item in value:
            _validate_extension_tree(item, depth=depth + 1)
        return
    if isinstance(value, float) and not isfinite(value):
        raise ValueError("extension numbers must be finite JSON values")
    if not isinstance(value, (bool, int, float)):
        raise ValueError("extension values must be JSON-compatible")


def _require_mapping(value: object, *, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


class StrictContractModel(BaseModel):
    """Base for contract objects that must reject unknown fields and coercion."""

    model_config = ConfigDict(extra="forbid", strict=True)


class ShieldSourceV1(StrictContractModel):
    """Immutable producer identity included in every event."""

    product: Literal["edy-shield"]
    product_version: str = Field(min_length=1, max_length=32)
    instance_id: str
    component: SourceComponentV1

    @field_validator("product_version")
    @classmethod
    def validate_product_version(cls, value: str) -> str:
        if not _SEMVER_RE.fullmatch(value):
            raise ValueError("product_version must be valid SemVer")
        return value

    @field_validator("instance_id")
    @classmethod
    def validate_instance_id(cls, value: str) -> str:
        return _validate_uuid(value)


class ShieldAssetV1(StrictContractModel):
    """Endpoint asset affected by the event."""

    asset_id: str = Field(min_length=1, max_length=255)
    hostname: str = Field(min_length=1, max_length=255)
    ip: str | None = Field(default=None, min_length=2, max_length=45)
    os: str | None = Field(default=None, min_length=1, max_length=255)

    _OPTIONAL_FIELDS: ClassVar[frozenset[str]] = frozenset({"ip", "os"})

    @model_validator(mode="before")
    @classmethod
    def reject_explicit_nulls(cls, value: object) -> object:
        data = _require_mapping(value, name="asset")
        for field_name in cls._OPTIONAL_FIELDS:
            if field_name in data and data[field_name] is None:
                raise ValueError(f"asset.{field_name} must be omitted instead of null")
        return value

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, value: str | None) -> str | None:
        if value is None:
            return value
        try:
            ipaddress.ip_address(value)
        except ValueError as exc:
            raise ValueError("ip must be a valid IPv4 or IPv6 address") from exc
        return value


class ShieldEvidenceV1(StrictContractModel):
    """Typed evidence with a bounded extension object."""

    file_path: str | None = Field(default=None, min_length=1, max_length=4096)
    hash_algorithm: HashAlgorithmV1 | None = None
    previous_hash: str | None = None
    current_hash: str | None = None
    baseline_id: str | None = Field(default=None, min_length=1, max_length=255)
    baseline_status: BaselineStatusV1 | None = None
    scan_id: str | None = Field(default=None, min_length=1, max_length=255)
    file_size_bytes: int | None = Field(default=None, ge=0)
    mtime: str | None = None
    details: dict[str, object]

    _OPTIONAL_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {
            "file_path",
            "hash_algorithm",
            "previous_hash",
            "current_hash",
            "baseline_id",
            "baseline_status",
            "scan_id",
            "file_size_bytes",
            "mtime",
        }
    )

    @model_validator(mode="before")
    @classmethod
    def validate_raw_evidence(cls, value: object) -> object:
        data = _require_mapping(value, name="evidence")
        for field_name in cls._OPTIONAL_FIELDS:
            if field_name in data and data[field_name] is None:
                raise ValueError(f"evidence.{field_name} must be omitted instead of null")
        details = data.get("details")
        if not isinstance(details, dict):
            raise ValueError("evidence.details is required and must be an object")
        if len(details) > MAX_EXTENSION_KEYS:
            raise ValueError(f"evidence.details must have <= {MAX_EXTENSION_KEYS} keys")
        if _serialized_size(details) > MAX_EXTENSION_BYTES:
            raise ValueError(f"evidence.details must be <= {MAX_EXTENSION_BYTES} bytes")
        _validate_extension_tree(details)
        return value

    @field_validator("mtime")
    @classmethod
    def validate_mtime(cls, value: str | None) -> str | None:
        if value is not None:
            _parse_utc_timestamp(value)
        return value

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if "\\" in value:
            raise ValueError("file_path must use forward slashes")
        if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
            raise ValueError("file_path must be relative to the monitored root")
        if "\x00" in value or any(part in {"", ".", ".."} for part in value.split("/")):
            raise ValueError("file_path cannot contain empty, dot, parent, or NUL segments")
        return value

    @model_validator(mode="after")
    def validate_hashes(self) -> Self:
        hashes = [item for item in (self.previous_hash, self.current_hash) if item is not None]
        if hashes and self.hash_algorithm is None:
            raise ValueError("hash_algorithm is required when a hash is present")
        if self.hash_algorithm is None:
            return self
        expected_length = _HASH_LENGTHS[self.hash_algorithm]
        for digest in hashes:
            if len(digest) != expected_length or not _HEX_RE.fullmatch(digest):
                raise ValueError(
                    f"{self.hash_algorithm} hashes require {expected_length} lowercase "
                    "hexadecimal characters"
                )
        return self


class ShieldMetadataV1(BaseModel):
    """Bounded correlation metadata with namespaced extension keys."""

    model_config = ConfigDict(extra="allow", strict=True)

    correlation_id: str | None = Field(default=None, min_length=1, max_length=1024)
    tags: list[str] | None = Field(default=None, max_length=32)
    shield_alert_id: str | None = Field(default=None, min_length=1, max_length=1024)
    rule_id: str | None = Field(default=None, min_length=1, max_length=1024)
    dedup_fingerprint: str | None = Field(default=None, min_length=1, max_length=1024)

    _KNOWN_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {"correlation_id", "tags", "shield_alert_id", "rule_id", "dedup_fingerprint"}
    )

    @model_validator(mode="before")
    @classmethod
    def validate_raw_metadata(cls, value: object) -> object:
        data = _require_mapping(value, name="metadata")
        if len(data) > MAX_EXTENSION_KEYS:
            raise ValueError(f"metadata must have <= {MAX_EXTENSION_KEYS} keys")
        if _serialized_size(data) > MAX_EXTENSION_BYTES:
            raise ValueError(f"metadata must be <= {MAX_EXTENSION_BYTES} bytes")
        for key, item in data.items():
            if item is None:
                raise ValueError(f"metadata.{key} must be omitted instead of null")
            if key not in cls._KNOWN_FIELDS and not key.startswith("x_"):
                raise ValueError(f"unknown metadata key {key!r} must use the x_ prefix")
        _validate_extension_tree(data)
        return value

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        if any(not tag or len(tag) > 64 for tag in value):
            raise ValueError("tags must contain 1 to 64 characters")
        return value


class ShieldEventV1(StrictContractModel):
    """One EDY Shield telemetry fact conforming to schema 1.0."""

    event_id: str
    schema_version: Literal["1.0"]
    timestamp: str
    sequence: int = Field(ge=1)
    source: ShieldSourceV1
    event_type: EventTypeV1
    severity: SeverityV1
    asset: ShieldAssetV1
    evidence: ShieldEvidenceV1
    metadata: ShieldMetadataV1

    @model_validator(mode="before")
    @classmethod
    def validate_event_size(cls, value: object) -> object:
        data = _require_mapping(value, name="event")
        if _serialized_size(data) > MAX_EVENT_BYTES:
            raise ValueError(f"event must be <= {MAX_EVENT_BYTES} bytes")
        return value

    @field_validator("event_id")
    @classmethod
    def validate_event_id(cls, value: str) -> str:
        return _validate_uuid(value, version=4)

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        parsed = _parse_utc_timestamp(value)
        if parsed > datetime.now(UTC) + timedelta(minutes=5):
            raise ValueError("timestamp cannot be more than 5 minutes in the future")
        return value

    @model_validator(mode="after")
    def validate_event_type_requirements(self) -> Self:
        evidence = self.evidence
        metadata = self.metadata

        required_by_type: dict[str, tuple[str, ...]] = {
            "shield.fim.baseline.created": (
                "baseline_id",
                "hash_algorithm",
                "baseline_status",
            ),
            "shield.fim.scan.completed": ("scan_id", "baseline_id"),
            "shield.fim.file.added": (
                "file_path",
                "current_hash",
                "hash_algorithm",
                "baseline_id",
                "scan_id",
                "baseline_status",
            ),
            "shield.fim.file.modified": (
                "file_path",
                "previous_hash",
                "current_hash",
                "hash_algorithm",
                "baseline_id",
                "scan_id",
                "baseline_status",
            ),
            "shield.fim.file.removed": (
                "file_path",
                "previous_hash",
                "hash_algorithm",
                "baseline_id",
                "scan_id",
                "baseline_status",
            ),
            "shield.hash.verified": (
                "file_path",
                "previous_hash",
                "current_hash",
                "hash_algorithm",
                "baseline_status",
            ),
            "shield.hash.mismatch": (
                "file_path",
                "previous_hash",
                "current_hash",
                "hash_algorithm",
                "baseline_status",
            ),
        }
        missing = [
            field_name
            for field_name in required_by_type.get(self.event_type, ())
            if getattr(evidence, field_name) is None
        ]
        if missing:
            raise ValueError(
                f"{self.event_type} requires evidence fields: {', '.join(missing)}"
            )

        expected_status: dict[str, str] = {
            "shield.fim.baseline.created": "created",
            "shield.fim.file.added": "added",
            "shield.fim.file.modified": "modified",
            "shield.fim.file.removed": "removed",
            "shield.hash.verified": "matched",
        }
        wanted_status = expected_status.get(self.event_type)
        if wanted_status is not None and evidence.baseline_status != wanted_status:
            raise ValueError(
                f"{self.event_type} requires baseline_status={wanted_status}"
            )
        if self.event_type == "shield.hash.mismatch" and evidence.baseline_status not in {
            "modified",
            "not_applicable",
        }:
            raise ValueError(
                "shield.hash.mismatch requires baseline_status=modified or not_applicable"
            )

        if self.event_type == "shield.fim.file.removed" and evidence.current_hash is not None:
            raise ValueError("shield.fim.file.removed forbids current_hash")
        if self.event_type in {"shield.fim.file.modified", "shield.hash.mismatch"}:
            if evidence.previous_hash == evidence.current_hash:
                raise ValueError("changed events require different previous and current hashes")

        if self.event_type == "shield.fim.baseline.created":
            self._require_nonnegative_detail("file_count")
        if self.event_type == "shield.fim.scan.completed":
            for key in ("added", "modified", "removed", "unchanged", "ignored", "duration_ms"):
                self._require_nonnegative_detail(key)
        if self.event_type == "shield.alert.created":
            if metadata.shield_alert_id is None or metadata.rule_id is None:
                raise ValueError(
                    "shield.alert.created requires metadata.shield_alert_id and metadata.rule_id"
                )
            self._require_string_detail("title")
            self._require_string_detail("description")
        if self.event_type == "shield.alert.updated":
            if metadata.shield_alert_id is None:
                raise ValueError("shield.alert.updated requires metadata.shield_alert_id")
            self._require_string_detail("previous_status")
            self._require_string_detail("current_status")
        return self

    def _require_nonnegative_detail(self, key: str) -> None:
        value = self.evidence.details.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"evidence.details.{key} must be an integer >= 0")

    def _require_string_detail(self, key: str) -> None:
        value = self.evidence.details.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"evidence.details.{key} must be a non-empty string")


class ShieldEventBatchV1(StrictContractModel):
    """Transport-neutral validation model for one v1 batch envelope."""

    batch_id: str
    sent_at: str
    events: list[ShieldEventV1] = Field(min_length=1, max_length=100)

    @model_validator(mode="before")
    @classmethod
    def validate_batch_size(cls, value: object) -> object:
        data = _require_mapping(value, name="batch")
        if _serialized_size(data) > MAX_BATCH_BYTES:
            raise ValueError(f"batch must be <= {MAX_BATCH_BYTES} bytes")
        return value

    @field_validator("batch_id")
    @classmethod
    def validate_batch_id(cls, value: str) -> str:
        return _validate_uuid(value, version=4)

    @field_validator("sent_at")
    @classmethod
    def validate_sent_at(cls, value: str) -> str:
        _parse_utc_timestamp(value)
        return value


__all__ = [
    "MAX_BATCH_BYTES",
    "MAX_EVENT_BYTES",
    "MAX_EXTENSION_BYTES",
    "MAX_EXTENSION_DEPTH",
    "MAX_EXTENSION_KEYS",
    "SCHEMA_VERSION_V1",
    "BaselineStatusV1",
    "EventTypeV1",
    "HashAlgorithmV1",
    "SeverityV1",
    "ShieldAssetV1",
    "ShieldEventBatchV1",
    "ShieldEventV1",
    "ShieldEvidenceV1",
    "ShieldMetadataV1",
    "ShieldSourceV1",
    "SourceComponentV1",
]
