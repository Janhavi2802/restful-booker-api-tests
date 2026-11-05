"""Reusable HTTP layer: one session, default headers, timeouts and request logging.

Every service client (auth, booking) inherits from this, so tests never call
`requests` directly.
"""
import json
import logging

import allure
import requests

from api.config import EnvConfig

log = logging.getLogger("api")


class BaseClient:
    def __init__(self, config: EnvConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.config.base_url}{path}"
        kwargs.setdefault("timeout", self.config.timeout)

        response = self.session.request(method, url, **kwargs)

        log.info("%s %s -> %s (%.0f ms)", method, url, response.status_code,
                 response.elapsed.total_seconds() * 1000)
        self._attach_to_allure(method, url, kwargs, response)
        return response

    @staticmethod
    def _attach_to_allure(method, url, kwargs, response):
        body = kwargs.get("json") or kwargs.get("data")
        request_text = f"{method} {url}\n\n{json.dumps(body, indent=2) if body else ''}"
        allure.attach(request_text, "request", allure.attachment_type.TEXT)
        allure.attach(
            f"{response.status_code}\n\n{response.text}",
            "response",
            allure.attachment_type.TEXT,
        )

    def get(self, path, **kw):
        return self.request("GET", path, **kw)

    def post(self, path, **kw):
        return self.request("POST", path, **kw)

    def put(self, path, **kw):
        return self.request("PUT", path, **kw)

    def patch(self, path, **kw):
        return self.request("PATCH", path, **kw)

    def delete(self, path, **kw):
        return self.request("DELETE", path, **kw)
