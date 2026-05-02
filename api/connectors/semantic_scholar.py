"""
Semantic Scholar API Connector
Provides citation counts and open-access paper data.
"""

import os
import time
from typing import Optional

import backoff
import requests
from loguru import logger


SEMANTIC_SCHOLAR_BASE = "https://api.semanticscholar.org/graph/v1"


class SemanticScholarConnector:
    """
    Connector for the Semantic Scholar Graph API.
    Free tier: 100 requests per 5 minutes.
    """

    def __init__(self):
        self.api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
        self.requests_per_minute = int(os.getenv("SEMANTIC_SCHOLAR_REQUESTS_PER_MINUTE", 100))
        self._last_request_time = 0.0

    def _headers(self) -> dict:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    def _rate_limit(self):
        """Basic rate limiting."""
        min_interval = 60.0 / self.requests_per_minute
        elapsed = time.time() - self._last_request_time
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_request_time = time.time()

    @backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=5)
    def _search(self, query: str, fields: list[str], limit: int, offset: int) -> dict:
        self._rate_limit()
        params = {
            "query": query,
            "fields": ",".join(fields),
            "limit": min(limit, 100),
            "offset": offset,
        }
        resp = requests.get(
            f"{SEMANTIC_SCHOLAR_BASE}/paper/search",
            params=params,
            headers=self._headers(),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def fetch(
        self,
        query: str,
        max_results: int = 100,
        fields: Optional[list[str]] = None,
    ) -> list[dict]:
        """Fetch paper records from Semantic Scholar."""
        if fields is None:
            fields = ["title", "year", "citationCount", "authors", "venue", "isOpenAccess", "externalIds"]

        records = []
        offset = 0
        batch_size = 100

        while len(records) < max_results:
            data = self._search(query, fields, batch_size, offset)
            papers = data.get("data", [])
            if not papers:
                break

            for paper in papers:
                authors = paper.get("authors", [])
                author_names = [a.get("name", "") for a in authors]
                external_ids = paper.get("externalIds", {}) or {}

                record = {
                    "title": paper.get("title", ""),
                    "year": paper.get("year"),
                    "citation_count": paper.get("citationCount", 0),
                    "venue": paper.get("venue", ""),
                    "is_open_access": paper.get("isOpenAccess", False),
                    "authors": "; ".join(author_names),
                    "author_count": len(author_names),
                    "doi": external_ids.get("DOI", ""),
                    "pubmed_id": external_ids.get("PubMed", ""),
                }
                records.append(record)
                if len(records) >= max_results:
                    break

            offset += len(papers)
            total = data.get("total", 0)
            if offset >= total:
                break

        logger.info(f"Semantic Scholar fetch complete: {len(records)} records")
        return records
