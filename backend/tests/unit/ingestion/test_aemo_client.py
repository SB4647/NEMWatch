import pytest

from nemwatch.ingestion.aemo_client import AemoClient, AemoClientError


@pytest.mark.anyio
async def test_client_rejects_non_https_url() -> None:
    client = AemoClient(user_agent="NEMWatch test")
    with pytest.raises(AemoClientError, match="HTTPS"):
        await client.fetch("http://example.test/data.csv")
