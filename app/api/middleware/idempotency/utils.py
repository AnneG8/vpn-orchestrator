import hashlib
import json

from fastapi import Request


async def build_fingerprint(request: Request) -> str:
    body = await request.body()

    normalized_body = _normalize_body(body)

    payload = (
        f'{request.method}:'
        f'{request.url.path}:'
        f'{normalized_body}'
    )

    return hashlib.sha256(payload.encode()).hexdigest()


def _normalize_body(body: bytes) -> str:
    if not body:
        return ''

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        return body.decode()

    return json.dumps(
        parsed,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
    )
