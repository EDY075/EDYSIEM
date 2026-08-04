"""Parser Syslog RFC5424.

Implementa o parsing de mensagens syslog no formato RFC5424.
Extrai version, timestamp, hostname, app-name, procid, msgid,
structured-data e msg do payload bruto.

O parser e uma funcao pura: recebe um ``RawEvent`` e retorna um
``Result[dict]``. Nunca levanta excecoes para cima.

Formato RFC5424:
    <PRIORITY>VERSION TIMESTAMP HOSTNAME APP-NAME PROCID MSGID STRUCTURED-DATA MSG

Exemplo:
    <165>1 2026-08-03T12:00:00.000Z wks-01 sshd - - [meta sequenceId="1"]
    User admin logged in
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from re import Pattern

from ..domain import RawEvent
from ..result import Error, ErrorCode, Failure, Result, ok

_RFC5424_PATTERN: Pattern[str] = re.compile(
    r"^<(\d+)>"
    r"(\d+)"
    r"\s+(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)"
    r"\s+(\S+)"
    r"\s+(\S+)"
    r"\s+(\S+)"
    r"\s+(\S+)"
    r"\s+(.*)$"
)

_STRUCTURED_DATA_PATTERN: Pattern[str] = re.compile(r"\[([^\]]+)\]")

_KEY_VALUE_PATTERN: Pattern[str] = re.compile(r'(\w+)=("(?:[^"\\]|\\.)*"|\S+)')


def _decode_priority(priority: int) -> tuple[int, int]:
    """Decodifica o campo priority em facility e severity."""
    facility = priority // 8
    severity = priority % 8
    return facility, severity


def _parse_timestamp(ts: str) -> datetime:
    """Converte o timestamp RFC5424 para datetime UTC."""
    try:
        # Remove trailing Z and parse
        ts_clean = ts.rstrip("Z")
        if "." in ts_clean:
            dt = datetime.fromisoformat(ts_clean)
        else:
            dt = datetime.fromisoformat(ts_clean)
        if ts.endswith("Z"):
            dt = dt.replace(tzinfo=UTC)
        elif dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except (ValueError, TypeError):
        return datetime.now(UTC)


def _parse_structured_data(sd_str: str) -> dict[str, dict[str, str]]:
    """Analisa o campo structured-data do RFC5424.

    Retorna um dicionario de dicionarios: {sd_id: {key: value}}.
    """
    result: dict[str, dict[str, str]] = {}
    for match in _STRUCTURED_DATA_PATTERN.finditer(sd_str):
        sd_content = match.group(1)
        sd_id = sd_content.split()[0] if sd_content else ""
        params: dict[str, str] = {}
        for kv_match in _KEY_VALUE_PATTERN.finditer(sd_content):
            key = kv_match.group(1)
            value = kv_match.group(2)
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
            params[key] = value
        if sd_id:
            result[sd_id] = params
    return result


def parse(raw_event: RawEvent) -> Result[dict[str, object]]:
    """Analisa um ``RawEvent`` no formato RFC5424.

    Args:
        raw_event: Evento bruto com payload syslog RFC5424.

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

    match = _RFC5424_PATTERN.match(text)
    if match is None:
        return Failure[dict[str, object]](
            Error(
                ErrorCode.PLUGIN_ERROR,
                f"formato RFC5424 nao reconhecido: {text[:80]!r}",
            )
        )

    priority = int(match.group(1))
    version = int(match.group(2))
    timestamp = _parse_timestamp(match.group(3))
    hostname = match.group(4)
    app_name = match.group(5)
    proc_id = match.group(6)
    msg_id = match.group(7)
    rest = match.group(8)

    # Separate structured-data from message
    sd_match = _STRUCTURED_DATA_PATTERN.match(rest)
    structured_data_str = sd_match.group(0) if sd_match else ""
    message = rest[sd_match.end() :].strip() if sd_match else rest.strip()

    structured_data = _parse_structured_data(structured_data_str)

    facility, severity = _decode_priority(priority)

    fields: dict[str, object] = {
        "version": version,
        "timestamp": timestamp.isoformat(),
        "hostname": hostname,
        "facility": _facility_name(facility),
        "severity": _severity_name(severity),
        "facility_code": facility,
        "severity_code": severity,
        "app_name": app_name,
        "proc_id": proc_id,
        "msg_id": msg_id,
        "structured_data": structured_data,
        "message": message,
        "event_category": _categorize(app_name, message),
        "event_action": _extract_action(message),
    }

    return ok(fields)


def _facility_name(facility: int) -> str:
    """Retorna o nome da facility."""
    names = {
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
    return names.get(facility, f"facility-{facility}")


def _severity_name(severity: int) -> str:
    """Retorna o nome da severity."""
    names = {
        0: "emergency",
        1: "alert",
        2: "critical",
        3: "error",
        4: "warning",
        5: "notice",
        6: "informational",
        7: "debug",
    }
    return names.get(severity, f"severity-{severity}")


def _categorize(app_name: str, message: str) -> str:
    """Classifica a categoria do evento."""
    auth_apps = {"sshd", "login", "su", "sudo", "auth", "cron", "systemd"}
    if app_name in auth_apps:
        return "auth"
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


__all__ = ["_RFC5424_PATTERN", "_STRUCTURED_DATA_PATTERN", "parse"]
