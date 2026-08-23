"""HTTP client for the official npm registry API."""

import json
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen

from .pypi_client import RegistryClientError


class NpmClient:
    BASE_URL = "https://registry.npmjs.org"

    def __init__(self, opener: Callable[..., Any] = urlopen, timeout: float = 10.0) -> None:
        self._opener = opener
        self._timeout = timeout

    def get_package_metadata(self, package_name: str) -> dict[str, str] | None:
        url = f"{self.BASE_URL}/{quote(package_name, safe='@/')}"
        try:
            with self._opener(url, timeout=self._timeout) as response:
                status = getattr(response, "status", None)
                if status is None:
                    status = response.getcode()
                if status != 200:
                    raise RegistryClientError("npm returned an unexpected HTTP status")
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            if error.code == 404:
                error.close()
                return None
            error.close()
            raise RegistryClientError(f"npm returned HTTP {error.code}") from error
        except (OSError, TimeoutError, URLError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RegistryClientError(f"npm request failed: {error}") from error

        try:
            name = payload["name"]
            version = payload["dist-tags"]["latest"]
        except (KeyError, TypeError) as error:
            raise RegistryClientError("npm returned malformed package metadata") from error
        if not isinstance(name, str) or not isinstance(version, str):
            raise RegistryClientError("npm returned malformed package metadata")
        return {"name": name, "version": version}
