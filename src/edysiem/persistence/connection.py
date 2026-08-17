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
        self._connections: set[sqlite3.Connection] = set()

    @property
    def path(self) -> str:
        """Caminho do arquivo de banco."""
        return self._path

    @property
    def active_connections(self) -> int:
        """Numero de conexoes abertas controladas pelo manager."""
        with self._lock:
            return len(self._connections)

    def connect(self) -> sqlite3.Connection:
        """Abre (ou reutiliza) uma conexao para a thread corrente."""
        with self._lock:
            cached_conn = getattr(self._local, "conn", None)
            if isinstance(cached_conn, sqlite3.Connection) and cached_conn in self._connections:
                return cached_conn
            self._local.conn = None

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
            self._connections.add(conn)
            self._local.conn = conn
            return conn

    def close(self) -> None:
        """Fecha a conexao da thread corrente."""
        with self._lock:
            conn = getattr(self._local, "conn", None)
            self._local.conn = None
            if isinstance(conn, sqlite3.Connection):
                self._connections.discard(conn)
                conn.close()

    def close_all(self) -> None:
        """Fecha todas as conexoes gerenciadas."""
        with self._lock:
            connections = tuple(self._connections)
            self._connections.clear()
            self._local.conn = None
            for connection in connections:
                connection.close()


__all__ = ["ConnectionManager"]
