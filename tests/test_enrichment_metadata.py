"""Testes do PluginMetadata e PluginPriority."""

from __future__ import annotations

import pytest

from edysiem.enrichment import PluginMetadata, PluginPriority


def test_plugin_metadata_creation() -> None:
    metadata = PluginMetadata(
        id="test-enricher",
        name="Test Enricher",
        version="1.0.0",
        author="Test Team",
        description="Test plugin",
        priority=PluginPriority.HIGH,
    )
    assert metadata.id == "test-enricher"
    assert metadata.name == "Test Enricher"
    assert metadata.version == "1.0.0"
    assert metadata.author == "Test Team"
    assert metadata.priority == PluginPriority.HIGH
    assert metadata.enabled is True


def test_plugin_metadata_defaults() -> None:
    metadata = PluginMetadata(
        id="test",
        name="Test",
        version="1.0.0",
        author="Test",
    )
    assert metadata.priority == PluginPriority.NORMAL
    assert metadata.dependencies == frozenset()
    assert metadata.supported_event_categories == frozenset()
    assert metadata.cache_policy == "none"
    assert metadata.timeout_seconds == 0.0
    assert metadata.tags == frozenset()
    assert metadata.enabled is True


def test_plugin_metadata_requires_id() -> None:
    with pytest.raises(ValueError, match="id não pode ser vazio"):
        PluginMetadata(id="", name="Test", version="1.0.0", author="Test")


def test_plugin_metadata_requires_name() -> None:
    with pytest.raises(ValueError, match="name não pode ser vazio"):
        PluginMetadata(id="test", name="", version="1.0.0", author="Test")


def test_plugin_metadata_requires_version() -> None:
    with pytest.raises(ValueError, match="version não pode ser vazio"):
        PluginMetadata(id="test", name="Test", version="", author="Test")


def test_plugin_metadata_requires_author() -> None:
    with pytest.raises(ValueError, match="author não pode ser vazio"):
        PluginMetadata(id="test", name="Test", version="1.0.0", author="")


def test_plugin_priority_ordering() -> None:
    assert PluginPriority.CRITICAL.value < PluginPriority.HIGH.value
    assert PluginPriority.HIGH.value < PluginPriority.NORMAL.value
    assert PluginPriority.NORMAL.value < PluginPriority.LOW.value
    assert PluginPriority.LOW.value < PluginPriority.BACKGROUND.value


def test_plugin_metadata_with_dependencies() -> None:
    metadata = PluginMetadata(
        id="composite",
        name="Composite",
        version="1.0.0",
        author="Team",
        dependencies=frozenset(["asset", "geo"]),
    )
    assert "asset" in metadata.dependencies
    assert "geo" in metadata.dependencies


def test_plugin_metadata_supported_categories() -> None:
    metadata = PluginMetadata(
        id="auth-only",
        name="Auth Only",
        version="1.0.0",
        author="Team",
        supported_event_categories=frozenset(["auth", "network"]),
    )
    assert "auth" in metadata.supported_event_categories
    assert "network" in metadata.supported_event_categories
    assert "process" not in metadata.supported_event_categories
