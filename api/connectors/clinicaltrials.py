"""
ClinicalTrials.gov API v2 Connector
"""

import os
from typing import Optional

import backoff
import requests
from loguru import logger


CLINICALTRIALS_BASE = "https://clinicaltrials.gov/api/v2/studies"


class ClinicalTrialsConnector:
    """
    Connector for the ClinicalTrials.gov REST API v2.
    No API key required, but include email in requests as courtesy.
    """

    def __init__(self):
        self.email = os.getenv("CLINICALTRIALS_EMAIL", "")

    @backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=5)
    def _fetch_page(self, params: dict) -> dict:
        resp = requests.get(CLINICALTRIALS_BASE, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _parse_study(self, study: dict) -> dict:
        """Flatten a ClinicalTrials study JSON into a flat record dict."""
        try:
            proto = study.get("protocolSection", {})
            id_module = proto.get("identificationModule", {})
            status_module = proto.get("statusModule", {})
            design_module = proto.get("designModule", {})
            conditions_module = proto.get("conditionsModule", {})
            interventions_module = proto.get("armsInterventionsModule", {})
            contacts_module = proto.get("contactsLocationsModule", {})
            sponsor_module = proto.get("sponsorCollaboratorsModule", {})
            eligibility_module = proto.get("eligibilityModule", {})

            conditions = conditions_module.get("conditions", [])
            interventions = interventions_module.get("interventions", [])
            intervention_names = [i.get("name", "") for i in interventions] if interventions else []
            locations = contacts_module.get("locations", [])
            countries = list(set(loc.get("country", "") for loc in locations if loc.get("country")))

            phases = design_module.get("phases", [])
            enrollment = design_module.get("enrollmentInfo", {}).get("count")

            return {
                "nct_id": id_module.get("nctId", ""),
                "title": id_module.get("briefTitle", ""),
                "official_title": id_module.get("officialTitle", ""),
                "status": status_module.get("overallStatus", ""),
                "start_date": status_module.get("startDateStruct", {}).get("date", ""),
                "completion_date": status_module.get("completionDateStruct", {}).get("date", ""),
                "phase": "; ".join(phases) if phases else "Not Applicable",
                "study_type": design_module.get("studyType", ""),
                "enrollment": enrollment,
                "conditions": "; ".join(conditions),
                "interventions": "; ".join(intervention_names),
                "countries": "; ".join(countries),
                "sponsor": sponsor_module.get("leadSponsor", {}).get("name", ""),
                "sponsor_class": sponsor_module.get("leadSponsor", {}).get("class", ""),
                "min_age": eligibility_module.get("minimumAge", ""),
                "max_age": eligibility_module.get("maximumAge", ""),
                "gender": eligibility_module.get("sex", ""),
                "location_count": len(locations),
                "country_count": len(countries),
            }
        except Exception as e:
            logger.warning(f"Failed to parse study: {e}")
            return {}

    def fetch(
        self,
        condition: str,
        intervention: Optional[str] = None,
        status: Optional[list[str]] = None,
        max_results: int = 200,
    ) -> list[dict]:
        """Fetch clinical trial records matching the given criteria."""
        params = {
            "query.cond": condition,
            "pageSize": min(max_results, 100),
            "format": "json",
        }
        if intervention:
            params["query.intr"] = intervention
        if status:
            params["filter.overallStatus"] = ",".join(status)

        records = []
        next_page_token = None
        fetched = 0

        while fetched < max_results:
            if next_page_token:
                params["pageToken"] = next_page_token

            data = self._fetch_page(params)
            studies = data.get("studies", [])
            for study in studies:
                parsed = self._parse_study(study)
                if parsed:
                    records.append(parsed)
                    fetched += 1
                    if fetched >= max_results:
                        break

            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break

        logger.info(f"ClinicalTrials fetch complete: {len(records)} records for condition='{condition}'")
        return records
