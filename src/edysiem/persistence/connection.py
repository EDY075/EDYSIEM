"""Connection Manager da camada de persistencia.

Gerencia conexoes SQLite (stdlib) com:
- WAL mode + foreign keys ON
- ``check_same_thread=False`` para acesso cross-thread
- pool simples de conexoes (uma por thread)
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

from .exceptions import ConnectionError


class ConnectionManager:
    """Gerencia conexoes SQLite.

    Args:
        path: Caminho do arquivo de banco. ``":memory:"`` para banco em memoria.
        timeout: Timeout de lock do SQLite (segundos).
    """

    def __init__(self, path: str = ":memory:", timeout: float = 10.0) -> None:
        self._path = ":memory:" if path == ":memory:" else str(Path(path))
        self._timeout = timeout
        self._local = threading.local()
        self._lock = threading.RLock()

    @property
    def path(self) -> str:
        """Caminho do arquivo de banco."""
        return self._path

    def connect(self) -> sqlite3.Connection:
        """Abre (ou reutiliza) uma conexao para a thread corrente."""
        cached_conn = getattr(self._local, "conn", None)
        if cached_conn is not None and isinstance(cached_conn, sqlite3.Connection):
            return cached_conn

        try:
            conn: sqlite3.Connection = sqlite3.connect(
                self._path,
                timeout=self._timeout,
                check_same_thread=False,
            )
        except sqlite3.Error as exc:
            raise ConnectionError(f"falha ao abrir banco {self._path}: {exc}") from exc

        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        self._local.conn = conn
        return conn

    def close(self) -> None:
        """Fecha a conexao da thread corrente."""
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            conn.close()
            self._local.conn = None

    def close_all(self) -> None:
        """Fecha todas as conexoes gerenciadas."""
        with self._lock:
            self.close()


__all__ = ["ConnectionManager"]
