"""Normalizador de eventos do EDY SIEM.

O normalizer converte ``ParsedEvent`` em ``CanonicalEvent`` aplicando
uma estrategia especifica por tipo de fonte (source_type).

Arquitetura:
- ``Normalizer`` (Protocol): interface do normalizer
- ``StrategyNormalizer``: implementacao com registro de estrategias
- ``Registry``: descoberta de normalizers por source_type

Uso:
    from edysiem.normalization import StrategyNormalizer, register_default_normalizers
    normalizer = StrategyNormalizer()
    register_default_normalizers(normalizer)
    result = normalizer.normalize(parsed_event)
"""

from .normalizer import Normalizer, StrategyNormalizer
from .registry import Registry, register_default_normalizers

__all__ = ["Normalizer", "Registry", "StrategyNormalizer", "register_default_normalizers"]
