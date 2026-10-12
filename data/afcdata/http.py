"""A polite JSON client: identifies itself, waits between calls, retries on 429/5xx."""

import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from . import USER_AGENT


class RateLimited(Exception):
    """The API refused the request because of its rate limit."""


class Client:
    def __init__(self, min_interval: float = 0.5, timeout: float = 30.0, headers: dict | None = None):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT
        if headers:
            self.session.headers.update(headers)
        retry = Retry(
            total=4,
            backoff_factor=2,
            status_forcelist=(500, 502, 503, 504),
            allowed_methods=("GET", "POST"),
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.min_interval = min_interval
        self.timeout = timeout
        self._last = 0.0

    def _wait(self) -> None:
        delay = self.min_interval - (time.monotonic() - self._last)
        if delay > 0:
            time.sleep(delay)
        self._last = time.monotonic()

    def get_json(self, url: str, params: dict | None = None) -> dict:
        self._wait()
        response = self.session.get(url, params=params, timeout=self.timeout)
        if response.status_code == 429:
            raise RateLimited(f"{url}: HTTP 429 ({response.headers.get('Retry-After', '?')}s)")
        response.raise_for_status()
        return response.json()

    def post_form(self, url: str, data: dict) -> dict:
        self._wait()
        response = self.session.post(url, data=data, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def get_stream(self, url: str) -> requests.Response:
        self._wait()
        response = self.session.get(url, stream=True, timeout=self.timeout)
        if response.status_code == 429:
            raise RateLimited(f"{url}: HTTP 429")
        response.raise_for_status()
        return response
