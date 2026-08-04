"""Fingerprint Engine do Alert Framework.

Gera um fingerprint deterministico (SHA-256) a partir de campos-chave
de um alerta. Eventos iguais produzem o mesmo fingerprint.

A identidade padrao inclui ``rule_id`` + campos de identidade do evento
(ip_src, user, source_host, asset). A ordenacao dos campos e estavel para
garantir determinismo.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from ..domain import EnrichedEvent
from .models import AlertFingerprint


class FingerprintEngine:
    """Calcula fingerprints deterministicos de alertas.

    Args:
        identity_fields: Campos do evento usados na identidade.
            Default: ``("rule_id", "ip_src", "ip_dst", "user", "source_host")``.
    """

    _DEFAULT_IDENTITY_FIELDS = (
        "rule_id",
        "ip_src",
        "ip_dst",
        "user",
        "source_host",
    )

    def __init__(self, identity_fields: tuple[str, ...] | None = None) -> None:
        self._identity_fields = identity_fields or self._DEFAULT_IDENTITY_FIELDS

    def compute(
        self, rule_id: str, event: EnrichedEvent | None, identity: dict[str, Any] | None = None
    ) -> AlertFingerprint:
        """Calcula o fingerprint de um alerta.

        Args:
            rule_id: Regra que gerou o alerta.
            event: Evento de origem (para extrair campos de identidade).
            identity: Campos adicionais de identidade (sobrescreve/estende).

        Returns:
            ``AlertFingerprint`` com hash SHA-256.
        """
        values: dict[str, Any] = {}

        if event is not None:
            for field in self._identity_fields:
                if field == "rule_id":
                    values["rule_id"] = rule_id
                    continue
                value = getattr(event, field, None)
                if value is not None:
                    values[field] = value

        # rule_id sempre presente
        values.setdefault("rule_id", rule_id)

        if identity:
            values.update(identity)

        # Serializacao canonica (chaves ordenadas, separadores estaveis)
        payload = json.dumps(values, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

        return AlertFingerprint(
            hash=digest,
            rule_id=rule_id,
            identity=frozenset(self._identity_fields),
        )


__all__ = ["FingerprintEngine"]
