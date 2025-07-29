"""Minimal requests-like HTTP wrapper for offline testing."""
import urllib.request
import urllib.parse
from urllib.error import URLError

class Response:
    def __init__(self, data: bytes, status: int = 200):
        self._data = data
        self.status_code = status

    def json(self):
        import json
        return json.loads(self._data.decode())

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise Exception(f"HTTP {self.status_code}")

class Session:
    def __init__(self):
        self.headers = {}

    def get(self, url, params=None, timeout=10):
        if params:
            url += '?' + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
                return Response(data, resp.status)
        except URLError as e:
            raise RequestException(e)

    def post(self, url, json=None, timeout=10):
        data = None
        if json is not None:
            import json as _json
            data = _json.dumps(json).encode()
            headers = {'Content-Type': 'application/json', **self.headers}
        else:
            headers = self.headers
        req = urllib.request.Request(url, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return Response(resp.read(), resp.status)
        except URLError as e:
            raise RequestException(e)

def get(url, params=None, timeout=10):
    return Session().get(url, params=params, timeout=timeout)

def post(url, json=None, timeout=10):
    return Session().post(url, json=json, timeout=timeout)

class RequestException(Exception):
    pass
