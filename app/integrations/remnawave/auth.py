from typing import Generator

import httpx


class TokenAuth(httpx.Auth):
    def __init__(self, token) -> None:
        self.token = token

    def auth_flow(
            self,
            request: httpx.Request,
    ) -> Generator[httpx.Request, httpx.Response, None]:
        request.headers['Authorization'] = f'Bearer {self.token}'
        yield request
