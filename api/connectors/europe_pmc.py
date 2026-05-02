"""
Europe PMC API Connector
Provides open-access full-text article data.
"""

import os
from typing import Optional

import backoff
import requests
from loguru import logger


EUROPE_PMC_BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest"


class EuropePMCConnector:
    """
    Connector for the Europe PMC REST API.
    No API key required.
    """

    def __init__(self):
        self.email = os.getenv("EUROPE_PMC_EMAIL", "")

    @backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=5)
    def _search_page(self, query: str, page_size: int, cursor_mark: str) -> dict:
        params = {
            "query": query,
            "format": "json",
            "pageSize": page_size,
            "cursorMark": cursor_mark,
            "resultType": "core",
        }
        if self.email:
            params["email"] = self.email

        resp = requests.get(f"{EUROPE_PMC_BASE}/search", params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def fetch(
        self,
        query: str,
        max_results: int = 200,
    ) -> list[dict]:
        """Fetch article records from Europe PMC."""
        records = []
        cursor_mark = "*"
        page_size = min(max_results, 100)

        while len(records) < max_results:
            data = self._search_page(query, page_size, cursor_mark)
            result_list = data.get("resultList", {}).get("result", [])
            if not result_list:
                break

            for article in result_list:
                author_string = article.get("authorString", "")
                record = {
                    "pmid": article.get("pmid", ""),
                    "title": article.get("title", ""),
                    "journal": article.get("journalTitle", ""),
                    "year": article.get("pubYear"),
                    "authors": author_string,
                    "doi": article.get("doi", ""),
                    "is_open_access": article.get("isOpenAccess", "N") == "Y",
                    "citation_count": article.get("citedByCount", 0),
                    "abstract": article.get("abstractText", ""),
                    "keywords": article.get("keywordList", {}).get("keyword", []),
                }
                if isinstance(record["keywords"], list):
                    record["keywords"] = "; ".join(record["keywords"])
                records.append(record)
                if len(records) >= max_results:
                    break

            next_cursor = data.get("nextCursorMark")
            if not next_cursor or next_cursor == cursor_mark:
                break
            cursor_mark = next_cursor

        logger.info(f"Europe PMC fetch complete: {len(records)} records")
        return records
