"""Parser Syslog RFC3164.

Implementa o parsing de mensagens syslog no formato clássico BSD/BSD/syslog-ng
(RFC3164). Extrai priority, facility, severity, timestamp, hostname, process,
pid e message do payload bruto.

O parser é uma função pura: recebe um ``RawEvent`` e retorna um
``Result[ParsedEvent]``. Nunca levanta exceções para cima.

Formato RFC3164:
    <PRIORITY>TIMESTAMP HOSTNAME PROCESS[PID]: MESSAGE

Exemplo:
    <13>Aug  3 12:00:00 wks-01 sshd[1234]: Accepted password for admin
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from re import Pattern

from ..domain import RawEvent
from ..result import Error, ErrorCode, Failure, Result, ok

_FACILITY_NAMES: dict[int, str] = {
    0: "kernel",
    1: "user",
    2: "mail",
    3: "daemon",
    4: "auth",
    5: "syslog",
    6: "lpr",
    7: "news",
    8: "uucp",
    9: "cron",
    10: "authpriv",
    11: "ftp",
    12: "ntp",
    13: "security",
    14: "console",
    15: "solaris-cron",
    16: "local0",
    17: "local1",
    18: "local2",
    19: "local3",
    20: "local4",
    21: "local5",
    22: "local6",
    23: "local7",
}

_SEVERITY_NAMES: dict[int, str] = {
    0: "emergency",
    1: "alert",
    2: "critical",
    3: "error",
    4: "warning",
    5: "notice",
    6: "informational",
    7: "debug",
}

_RFC3164_PATTERN: Pattern[str] = re.compile(
    r"^<(\d+)>"
    r"(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})"
    r"\s+(\S+)"
    r"\s+(\S+?)(?:\[(\d+)\])?"
    r":\s+(.*)$"
)


def _decode_priority(priority: int) -> tuple[int, int]:
    """Decodifica o campo priority em facility e severity.

    RFC3164: priority = facility * 8 + severity.
    """
    facility = priority // 8
    severity = priority % 8
    return facility, severity


def _parse_timestamp(ts: str, year: int = 2026) -> datetime:
    """Converte o timestamp RFC3164 para datetime UTC.

    RFC3164 timestamps nao incluem ano; assume-se o ano corrente.
    """
    try:
        dt = datetime.strptime(f"{year} {ts}", "%Y %b %d %H:%M:%S")
        return dt.replace(tzinfo=UTC)
    except ValueError:
        return datetime.now(tz=UTC)


def parse(raw_event: RawEvent) -> Result[dict[str, object]]:
    """Analisa um ``RawEvent`` no formato RFC3164.

    Args:
        raw_event: Evento bruto com payload syslog.

    Returns:
        ``Success(dict)`` com os campos extraidos em caso de sucesso;
        ``Failure`` com ``ErrorCode.PLUGIN_ERROR`` se o formato nao
        for reconhecido.
    """
    payload = raw_event.raw_payload
    if isinstance(payload, bytes):
        try:
            text = payload.decode("utf-8", errors="replace")
        except Exception:
            text = str(payload)
    else:
        text = payload

    match = _RFC3164_PATTERN.match(text)
    if match is None:
        return Failure[dict[str, object]](
            Error(
                ErrorCode.PLUGIN_ERROR,
                f"formato RFC3164 nao reconhecido: {text[:80]!r}",
            )
        )

    priority = int(match.group(1))
    facility, severity = _decode_priority(priority)
    timestamp = _parse_timestamp(match.group(2))
    hostname = match.group(3)
    process = match.group(4)
    pid = match.group(5)
    message = match.group(6)

    fields: dict[str, object] = {
        "facility": _FACILITY_NAMES.get(facility, f"facility-{facility}"),
        "severity": _SEVERITY_NAMES.get(severity, f"severity-{severity}"),
        "facility_code": facility,
        "severity_code": severity,
        "timestamp": timestamp.isoformat(),
        "hostname": hostname,
        "process": process,
        "pid": pid,
        "message": message,
        "event_category": _categorize(process, message),
        "event_action": _extract_action(message),
    }

    return ok(fields)


def _categorize(process: str, message: str) -> str:
    """Classifica a categoria do evento com base no processo e mensagem."""
    auth_procs = {"sshd", "login", "su", "sudo", "auth", "cron", "systemd"}
    net_procs = {"kernel", "dhclient", "NetworkManager", "firewall", "iptables"}
    proc_procs = {"cron", "systemd", "init", "crond"}

    process_lower = process.lower()
    if process_lower in auth_procs:
        return "auth"
    if process_lower in net_procs:
        return "network"
    if process_lower in proc_procs:
        return "process"
    if "login" in message.lower() or "authentication" in message.lower():
        return "auth"
    if "denied" in message.lower() or "failed" in message.lower():
        return "auth"
    return "system"


def _extract_action(message: str) -> str:
    """Extrai a acao do evento da mensagem."""
    lower = message.lower()
    if "accepted" in lower:
        return "accept"
    if "failed" in lower or "denied" in lower or "refused" in lower:
        return "reject"
    if "started" in lower or "starting" in lower:
        return "start"
    if "stopped" in lower or "stopping" in lower:
        return "stop"
    if "error" in lower or "fatal" in lower or "critical" in lower:
        return "error"
    if "warning" in lower or "warn" in lower:
        return "warn"
    return "info"


__all__ = ["_FACILITY_NAMES", "_RFC3164_PATTERN", "_SEVERITY_NAMES", "parse"]
