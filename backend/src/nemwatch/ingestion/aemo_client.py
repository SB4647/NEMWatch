import asyncio
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class AemoClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class AemoClient:
    user_agent: str
    connect_timeout: float = 5.0
    read_timeout: float = 15.0
    max_response_bytes: int = 10_000_000
    max_attempts: int = 3

    async def fetch(self, url: str) -> bytes:
        if urlparse(url).scheme != "https":
            raise AemoClientError("AEMO source must use HTTPS")
        last_error: Exception | None = None
        for attempt in range(self.max_attempts):
            try:
                return await asyncio.to_thread(self._fetch_once, url)
            except (HTTPError, URLError, TimeoutError, OSError, AemoClientError) as error:
                last_error = error
                if isinstance(error, AemoClientError) or attempt == self.max_attempts - 1:
                    break
                await asyncio.to_thread(time.sleep, 0.25 * (2**attempt))
        raise AemoClientError(f"AEMO request failed after {self.max_attempts} attempts") from last_error

    def _fetch_once(self, url: str) -> bytes:
        request = Request(url, headers={"User-Agent": self.user_agent})
        with urlopen(request, timeout=self.connect_timeout) as response:  # noqa: S310
            if urlparse(response.geturl()).scheme != "https":
                raise AemoClientError("AEMO redirect must remain on HTTPS")
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > self.max_response_bytes:
                raise AemoClientError("AEMO response exceeds the configured size limit")
            socket = getattr(getattr(getattr(response, "fp", None), "raw", None), "_sock", None)
            if socket is not None:
                socket.settimeout(self.read_timeout)
            content = response.read(self.max_response_bytes + 1)
            if len(content) > self.max_response_bytes:
                raise AemoClientError("AEMO response exceeds the configured size limit")
            return content
