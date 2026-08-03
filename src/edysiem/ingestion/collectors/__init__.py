"""Coletores da infraestrutura de ingestão.

Atualmente expõe apenas o contrato Enterprise de coletores
(``CollectorPlugin`` e tipos de suporte). Implementações reais de coletores
(syslog, file, windows, ...) são sprints futuras.
"""

from .base import CollectorCapability, CollectorMetadata, CollectorPlugin

__all__ = ["CollectorCapability", "CollectorMetadata", "CollectorPlugin"]
