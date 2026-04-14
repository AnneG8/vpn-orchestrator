import httpx
import pytest

from app.integrations.remnawave import RemnaWaveClient


@pytest.fixture
def mock_transport():
    def handler(request: httpx.Request) -> httpx.Response:
        raise NotImplementedError('Mock not configured')
    return httpx.MockTransport(handler)


@pytest.fixture
def rw_client(mock_transport):
    client = RemnaWaveClient()
    client._client = httpx.AsyncClient(
        transport=mock_transport,
        base_url='http://test',
    )
    return client
