"""Minimal drop-in replacement for the subset of django-environ that the
project relies on.

The real django-environ package is preferred, but Apple's system Python may
have an older, Python 2-only ``environ`` module on sys.path which takes
precedence and raises SyntaxErrors when imported. Dropping this helper in the
repository keeps ``import environ`` working without forcing a particular
package installation strategy.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Iterator, MutableMapping, Optional
from urllib.parse import parse_qsl, unquote, urlparse

_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}


class Env(MutableMapping[str, str]):
    """Small helper that mimics the features used by settings.py."""

    def __init__(self) -> None:
        self._store = os.environ

    # --- Mapping interface -------------------------------------------------
    def __getitem__(self, key: str) -> str:
        return self._store[key]

    def __setitem__(self, key: str, value: str) -> None:
        self._store[key] = value

    def __delitem__(self, key: str) -> None:
        del self._store[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._store)

    def __len__(self) -> int:
        return len(self._store)

    # --- Convenience helpers ----------------------------------------------
    def __call__(self, key: str, default: Optional[Any] = None, *, cast=None) -> Any:
        value = self._store.get(key)
        if value is None:
            return default
        if cast is not None:
            return cast(value)
        return value

    def bool(self, key: str, default: bool = False) -> bool:
        value = self._store.get(key)
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        lowered = value.strip().lower()
        if lowered in _TRUE_VALUES:
            return True
        if lowered in _FALSE_VALUES:
            return False
        raise ValueError(f"Cannot interpret '{value}' as boolean")

    def list(
        self,
        key: str,
        default: Optional[Any] = None,
        *,
        delimiter: str = ",",
    ) -> list[str]:
        value = self._store.get(key)
        if value is None:
            if default is None:
                return []
            if isinstance(default, str):
                value = default
            else:
                return list(default)
        if value == "":
            return []
        return [item.strip() for item in value.split(delimiter) if item.strip()]

    def db(self, url: Optional[str] = None, *, key: str = "DATABASE_URL") -> Dict[str, Any]:
        database_url = url or self._store.get(key)
        if not database_url:
            return {}
        parsed = urlparse(database_url)
        scheme = parsed.scheme.lower()
        engine = self._engine_for_scheme(scheme)

        if engine.endswith("sqlite3"):
            name = parsed.path[1:] if parsed.path != "/" else parsed.path
            if not name:
                name = parsed.netloc
            if name in ("", ":memory:"):
                name = ":memory:"
        else:
            name = parsed.path.lstrip("/") or ""

        options = dict(parse_qsl(parsed.query))
        config: Dict[str, Any] = {
            "ENGINE": engine,
            "NAME": unquote(name),
            "USER": unquote(parsed.username or ""),
            "PASSWORD": unquote(parsed.password or ""),
            "HOST": parsed.hostname or "",
            "PORT": str(parsed.port) if parsed.port else "",
        }
        if options:
            config["OPTIONS"] = options
        return config

    def read_env(self, path: Optional[str | os.PathLike[str]] = None) -> None:
        env_path = Path(path or ".env")
        if not env_path.exists():
            return
        for raw_line in env_path.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export ") :].lstrip()
            key, sep, value = line.partition("=")
            if not sep:
                continue
            key = key.strip()
            value = self._strip_quotes(value.strip())
            self._store.setdefault(key, value)

    @staticmethod
    def _strip_quotes(value: str) -> str:
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            return value[1:-1]
        return value

    @staticmethod
    def _engine_for_scheme(scheme: str) -> str:
        mapping = {
            "postgres": "django.db.backends.postgresql",
            "postgresql": "django.db.backends.postgresql",
            "postgresql_psycopg2": "django.db.backends.postgresql",
            "psql": "django.db.backends.postgresql",
            "mysql": "django.db.backends.mysql",
            "mysql2": "django.db.backends.mysql",
            "sqlite": "django.db.backends.sqlite3",
            "sqlite3": "django.db.backends.sqlite3",
        }
        return mapping.get(scheme, f"django.db.backends.{scheme}")


__all__ = ["Env"]
