"""HTTP client for the official PyPI JSON API."""

import json
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen


class RegistryClientError(RuntimeError):
    """The official registry could not provide a usable response."""


class PyPIClient:
    BASE_URL = "https://pypi.org/pypi"

    def __init__(self, opener: Callable[..., Any] = urlopen, timeout: float = 10.0) -> None:
        self._opener = opener
        self._timeout = timeout

    def get_package_metadata(self, package_name: str) -> dict[str, str] | None:
        url = f"{self.BASE_URL}/{quote(package_name, safe='')}/json"
        try:
            with self._opener(url, timeout=self._timeout) as response:
                status = getattr(response, "status", None)
                if status is None:
                    status = response.getcode()
                if status != 200:
                    raise RegistryClientError("PyPI returned an unexpected HTTP status")
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            if error.code == 404:
                error.close()
                return None
            error.close()
            raise RegistryClientError(f"PyPI returned HTTP {error.code}") from error
        except (OSError, TimeoutError, URLError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RegistryClientError(f"PyPI request failed: {error}") from error

        try:
            info = payload["info"]
            name = info["name"]
            version = info["version"]
        except (KeyError, TypeError) as error:
            raise RegistryClientError("PyPI returned malformed package metadata") from error
        if not isinstance(name, str) or not isinstance(version, str):
            raise RegistryClientError("PyPI returned malformed package metadata")
        return {"name": name, "version": version}
