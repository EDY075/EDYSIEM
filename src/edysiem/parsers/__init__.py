"""Parsers de eventos do EDY SIEM.

Cada parser implementa a interface funcional ``parse(raw_event: RawEvent) -> Result[dict]``.
O resultado e um dicionario de campos estruturados que alimenta o normalizer.

Parsers disponiveis:
- ``syslog``: parser RFC3164 (formato clássico BSD/syslog-ng)
- ``rfc5424``: parser RFC5424 (formato moderno com structured-data)

Uso:
    from edysiem.parsers import syslog, rfc5424
    result = syslog.parse(raw_event)
    if result.is_ok():
        fields = result.unwrap()
"""

from .rfc5424 import parse as parse_rfc5424
from .syslog import parse as parse_syslog

__all__ = ["parse_rfc5424", "parse_syslog"]
