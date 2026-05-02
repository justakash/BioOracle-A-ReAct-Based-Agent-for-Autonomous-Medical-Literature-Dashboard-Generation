"""
PubMed / NCBI E-utilities Connector
Handles all communication with NCBI APIs with rate limiting and caching.
"""

import os
import time
from typing import Optional

import backoff
import requests
import xmltodict
from loguru import logger


NCBI_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class PubMedConnector:
    """
    Connector for NCBI E-utilities (ESearch + EFetch).
    Respects rate limits: 10 req/sec with API key, 3 req/sec without.
    """

    def __init__(self):
        self.api_key = os.getenv("NCBI_API_KEY", "")
        self.email = os.getenv("NCBI_EMAIL", "")
        self.requests_per_second = int(os.getenv("NCBI_REQUESTS_PER_SECOND", 10))
        self._last_request_time = 0.0

    def _rate_limit(self):
        """Enforce NCBI rate limits."""
        min_interval = 1.0 / self.requests_per_second
        elapsed = time.time() - self._last_request_time
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_request_time = time.time()

    def _base_params(self) -> dict:
        params = {"retmode": "json"}
        if self.api_key:
            params["api_key"] = self.api_key
        if self.email:
            params["email"] = self.email
        return params

    @backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=5)
    def _esearch(self, query: str, max_results: int, date_from: Optional[str], date_to: Optional[str]) -> list[str]:
        """Search PubMed and return list of PMIDs."""
        self._rate_limit()
        params = self._base_params()
        params.update({
            "db": "pubmed",
            "term": query,
            "retmax": min(max_results, 10000),
            "usehistory": "y",
        })
        if date_from:
            params["mindate"] = date_from
        if date_to:
            params["maxdate"] = date_to
        if date_from or date_to:
            params["datetype"] = "pdat"

        resp = requests.get(f"{NCBI_BASE_URL}/esearch.fcgi", params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        pmids = data.get("esearchresult", {}).get("idlist", [])
        total = int(data.get("esearchresult", {}).get("count", 0))
        logger.info(f"PubMed ESearch: {total} total results, fetching {len(pmids)}")
        return pmids

    @backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=5)
    def _efetch_batch(self, pmids: list[str]) -> list[dict]:
        """Fetch metadata for a batch of PMIDs."""
        self._rate_limit()
        params = self._base_params()
        params.update({
            "db": "pubmed",
            "id": ",".join(pmids),
            "rettype": "abstract",
            "retmode": "xml",
        })

        resp = requests.get(f"{NCBI_BASE_URL}/efetch.fcgi", params=params, timeout=60)
        resp.raise_for_status()

        parsed = xmltodict.parse(resp.text)
        articles = parsed.get("PubmedArticleSet", {}).get("PubmedArticle", [])
        if isinstance(articles, dict):
            articles = [articles]

        return articles

    def _parse_article(self, article: dict, fields: list[str]) -> dict:
        """Extract requested fields from a raw PubMed article dict."""
        try:
            medline = article.get("MedlineCitation", {})
            article_data = medline.get("Article", {})
            record = {}

            if "pmid" in fields:
                record["pmid"] = str(medline.get("PMID", {}).get("#text", medline.get("PMID", "")))

            if "title" in fields:
                record["title"] = article_data.get("ArticleTitle", "")
                if isinstance(record["title"], dict):
                    record["title"] = record["title"].get("#text", "")

            if "date" in fields:
                pub_date = article_data.get("Journal", {}).get("JournalIssue", {}).get("PubDate", {})
                year = pub_date.get("Year", pub_date.get("MedlineDate", "")[:4] if "MedlineDate" in pub_date else "")
                month = pub_date.get("Month", "01")
                record["year"] = int(year) if year else None
                record["month"] = month

            if "journal" in fields:
                record["journal"] = article_data.get("Journal", {}).get("Title", "")

            if "abstract" in fields:
                abstract = article_data.get("Abstract", {}).get("AbstractText", "")
                if isinstance(abstract, list):
                    abstract = " ".join([
                        a.get("#text", a) if isinstance(a, dict) else a for a in abstract
                    ])
                elif isinstance(abstract, dict):
                    abstract = abstract.get("#text", "")
                record["abstract"] = abstract

            if "authors" in fields:
                author_list = article_data.get("AuthorList", {}).get("Author", [])
                if isinstance(author_list, dict):
                    author_list = [author_list]
                authors = []
                for a in author_list:
                    last = a.get("LastName", "")
                    first = a.get("ForeName", "")
                    if last:
                        authors.append(f"{last}, {first}".strip(", "))
                record["authors"] = "; ".join(authors)
                record["author_count"] = len(authors)
                record["first_author"] = authors[0] if authors else ""

            if "mesh" in fields:
                mesh_list = medline.get("MeshHeadingList", {})
                if mesh_list:
                    headings = mesh_list.get("MeshHeading", [])
                    if isinstance(headings, dict):
                        headings = [headings]
                    mesh_terms = [
                        h.get("DescriptorName", {}).get("#text", "") or h.get("DescriptorName", "")
                        for h in headings
                    ]
                    record["mesh_terms"] = "; ".join([t for t in mesh_terms if t])
                else:
                    record["mesh_terms"] = ""

            if "doi" in fields:
                ids = article.get("PubmedData", {}).get("ArticleIdList", {}).get("ArticleId", [])
                if isinstance(ids, dict):
                    ids = [ids]
                doi = next((i.get("#text", "") for i in ids if i.get("@IdType") == "doi"), "")
                record["doi"] = doi

            return record

        except Exception as e:
            logger.warning(f"Failed to parse article: {e}")
            return {}

    def fetch(
        self,
        query: str,
        max_results: int = 500,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        fields: Optional[list[str]] = None,
    ) -> list[dict]:
        """
        Full fetch pipeline: ESearch -> batch EFetch -> parse to list of dicts.
        Returns raw parsed records (NOT a DataFrame - that is the ETL's job).
        """
        if fields is None:
            fields = ["pmid", "title", "date", "journal", "authors", "mesh"]

        pmids = self._esearch(query, max_results, date_from, date_to)
        if not pmids:
            logger.warning(f"No results found for query: {query}")
            return []

        records = []
        batch_size = 200
        for i in range(0, len(pmids), batch_size):
            batch = pmids[i: i + batch_size]
            logger.debug(f"Fetching batch {i // batch_size + 1} ({len(batch)} PMIDs)")
            articles = self._efetch_batch(batch)
            for article in articles:
                parsed = self._parse_article(article, fields)
                if parsed:
                    records.append(parsed)

        logger.info(f"PubMed fetch complete: {len(records)} records")
        return records
