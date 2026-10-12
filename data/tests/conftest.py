import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class FakeClient:
    """Replays canned JSON responses. `routes` is a list of (predicate, response) pairs."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def get_json(self, url, params=None):
        params = params or {}
        self.calls.append((url, params))
        for predicate, response in self.routes:
            if predicate(url, params):
                return response(params) if callable(response) else response
        raise AssertionError(f"unexpected request {url} {params}")
