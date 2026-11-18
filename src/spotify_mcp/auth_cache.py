"""Private token files shared by the login command and MCP runtime."""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from filelock import FileLock, Timeout
from spotipy.cache_handler import CacheFileHandler

from spotify_mcp.config import Settings

_MARKER = "_spotify_mcp"


class TokenCacheError(RuntimeError):
    """The token cache could not be used or saved."""


class TokenCacheBusy(TokenCacheError):
    """A different login or refresh is using the cache."""


class TokenCache:
    """Read and atomically replace a cache for one OAuth mode and client."""

    def __init__(self, settings: Settings) -> None:
        self.path = Path(
            CacheFileHandler(cache_path=settings.cache_path).cache_path
        ).resolve()
        self._lock = FileLock(f"{self.path}.lock", timeout=15, mode=0o600)
        self._marker = (
            {"version": 1, "client_id": settings.client_id}
            if settings.auth_mode == "pkce"
            else None
        )

    def read(self) -> dict[str, Any] | None:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        except (OSError, ValueError):
            raise self._incompatible("Could not read") from None

        if not isinstance(raw, dict):
            raise self._incompatible("Invalid")
        if self._marker is None:
            matches = _MARKER not in raw
        else:
            matches = raw.get(_MARKER) == self._marker
        if not matches:
            raise self._incompatible("Incompatible")

        raw.pop(_MARKER, None)
        return raw

    def write(self, token: dict[str, Any]) -> None:
        with self.lock():
            self._write(token)

    @contextmanager
    def lock(self) -> Iterator[None]:
        """Serialize refresh and login commits across processes sharing this file."""
        try:
            self.path.parent.mkdir(mode=0o700, exist_ok=True, parents=True)
            acquired = self._lock.acquire()
        except Timeout:
            raise TokenCacheBusy(
                "Spotify authorization is busy. Try again."
            ) from None
        except OSError:
            raise TokenCacheError(
                f"Could not write Spotify token cache at {self.path}. "
                "Check the directory and file permissions."
            ) from None
        with acquired:
            yield

    def _write(self, token: dict[str, Any]) -> None:
        self.read()
        data = dict(token)
        data.pop(_MARKER, None)
        if self._marker is not None:
            data[_MARKER] = self._marker

        temp_path = None
        try:
            with NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.path.parent, delete=False
            ) as temp:
                temp_path = Path(temp.name)
                json.dump(data, temp)
                temp.flush()
                os.fsync(temp.fileno())
            os.replace(temp_path, self.path)
        except (OSError, TypeError, ValueError):
            raise TokenCacheError(
                f"Could not write Spotify token cache at {self.path}. "
                "Check the directory and file permissions."
            ) from None
        finally:
            if temp_path is not None:
                with suppress(OSError):
                    temp_path.unlink(missing_ok=True)

    def _incompatible(self, prefix: str) -> TokenCacheError:
        return TokenCacheError(
            f"{prefix} Spotify token cache at {self.path}. "
            "Choose a different cache path or move the old file aside."
        )
