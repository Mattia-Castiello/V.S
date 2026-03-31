import asyncio
import logging
import random
import time

import httpx

from backend.config import get_settings

logger = logging.getLogger("vinted_intelligence")

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
]

MAX_COOKIE_RETRIES = 3
BACKOFF_BASE_SECONDS = 2


class VintedSession:
    def __init__(self):
        settings = get_settings()
        self.base_url = settings.vinted_base_url
        self.refresh_interval = settings.vinted_session_refresh_minutes * 60
        self._access_token: str | None = None
        self._user_agent: str = random.choice(USER_AGENTS)
        self._last_refresh: float = 0
        self._client: httpx.AsyncClient | None = None

    def _get_headers(self) -> dict:
        headers = {
            "User-Agent": self._user_agent,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Referer": f"{self.base_url}/",
            "Origin": self.base_url,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        return headers

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                limits=httpx.Limits(max_connections=10),
            )
        return self._client

    async def _fetch_access_token(self):
        """Fetch a fresh access token from Vinted homepage with retry."""
        client = await self._get_client()

        for attempt in range(1, MAX_COOKIE_RETRIES + 1):
            try:
                response = await client.get(
                    self.base_url,
                    headers={
                        "User-Agent": self._user_agent,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
                        "Accept-Encoding": "gzip, deflate",
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "Sec-Fetch-Dest": "document",
                        "Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "none",
                        "Sec-Fetch-User": "?1",
                        "Upgrade-Insecure-Requests": "1",
                    },
                )
                response.raise_for_status()

                # Extract access_token_web from cookies
                access_token = response.cookies.get("access_token_web")
                if access_token:
                    self._access_token = access_token
                    self._last_refresh = time.time()
                    logger.info("Vinted access token refreshed")
                    return

                # Try from set-cookie headers
                for header_val in response.headers.get_list("set-cookie"):
                    if "access_token_web=" in header_val:
                        cookie_part = header_val.split(";")[0]
                        if "=" in cookie_part:
                            token = cookie_part.split("=", 1)[1]
                            if token:  # skip empty clear-cookie values
                                self._access_token = token
                                self._last_refresh = time.time()
                                logger.info("Vinted access token refreshed from header")
                                return

                logger.warning(
                    f"Access token not found in response (attempt {attempt}/{MAX_COOKIE_RETRIES})"
                )

            except httpx.HTTPStatusError as e:
                logger.warning(
                    f"HTTP {e.response.status_code} fetching token (attempt {attempt}/{MAX_COOKIE_RETRIES})"
                )
            except httpx.HTTPError as e:
                logger.warning(
                    f"Network error fetching token (attempt {attempt}/{MAX_COOKIE_RETRIES}): {e}"
                )

            if attempt < MAX_COOKIE_RETRIES:
                wait = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
                logger.info(f"Retrying token fetch in {wait}s...")
                await asyncio.sleep(wait)

        logger.error(
            f"Failed to obtain Vinted access token after {MAX_COOKIE_RETRIES} attempts"
        )

    async def ensure_session(self):
        """Ensure we have a valid access token, refreshing if needed."""
        now = time.time()
        if not self._access_token or (now - self._last_refresh) > self.refresh_interval:
            await self._fetch_access_token()
            if not self._access_token:
                raise RuntimeError(
                    "Unable to establish Vinted session — token fetch failed after all retries"
                )

    async def get(self, path: str, params: dict | None = None) -> dict | None:
        """Make an authenticated GET request to Vinted API."""
        from backend.utils.rate_limiter import vinted_limiter

        await vinted_limiter.acquire()
        await self.ensure_session()
        client = await self._get_client()

        url = f"{self.base_url}{path}"
        response = await client.get(url, headers=self._get_headers(), params=params)

        if response.status_code == 401 or response.status_code == 403:
            logger.info("Session expired, refreshing...")
            self._access_token = None
            await self.ensure_session()
            response = await client.get(url, headers=self._get_headers(), params=params)

        if response.status_code != 200:
            logger.error(f"Vinted API error: {response.status_code} for {path}")
            return None

        return response.json()

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
