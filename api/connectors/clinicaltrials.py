"""
ClinicalTrials.gov API v2 Connector
No API key required. Government open data.
Fetches trial records, patient matching, endpoint analysis, investigators, and sponsor pipelines.
"""

import os
import re
import time
from collections import Counter, defaultdict
from typing import Optional

import backoff
import requests
from loguru import logger


CLINICALTRIALS_BASE = "https://clinicaltrials.gov/api/v2/studies"


class ClinicalTrialsConnector:
    """
    Connector for the ClinicalTrials.gov REST API v2.
    No API key required. Include email in requests as courtesy.
    """

    def __init__(self):
        self.email = os.getenv("CLINICALTRIALS_EMAIL", "")

    def _get_json(self, url: str, params: dict = None) -> dict:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        time.sleep(0.15)
        return resp.json()

    def _extract(self, study: dict, path: list, default=None):
        cur = study
        for p in path:
            if isinstance(cur, dict):
                cur = cur.get(p)
            elif isinstance(cur, list) and isinstance(p, int) and len(cur) > p:
                cur = cur[p]
            else:
                return default
        return cur if cur is not None else default

    def _normalize_phase(self, phase) -> Optional[str]:
        if not phase:
            return None
        p = str(phase).upper().replace(" ", "")
        if "1" in p: return "PHASE1"
        if "2" in p: return "PHASE2"
        if "3" in p: return "PHASE3"
        if "4" in p: return "PHASE4"
        return None

    def _clean_text(self, text: str) -> str:
        if not text:
            return "No reason provided"
        return re.sub(r"\s+", " ", text).strip()

    @backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=5)
    def _fetch_page(self, params: dict) -> dict:
        resp = requests.get(CLINICALTRIALS_BASE, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _parse_study(self, study: dict) -> dict:
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
        status: Optional[list] = None,
        max_results: int = 200,
    ) -> list[dict]:
        """Core fetch for the agent pipeline. Returns flat record dicts."""
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

    def search_trials(
        self,
        condition: str = None,
        intervention: str = None,
        location: str = None,
        status: str = None,
        sponsor: str = None,
        max_results: int = 50,
    ) -> list[dict]:
        """Flexible search with automatic keyword fallback if structured search returns nothing."""
        params = {"pageSize": max_results}
        if condition: params["query.cond"] = condition
        if intervention: params["query.intr"] = intervention
        if location: params["query.location"] = location
        if status: params["filter.overallStatus"] = status.upper()

        data = self._get_json(CLINICALTRIALS_BASE, params)
        studies = data.get("studies", [])

        if len(studies) == 0:
            logger.warning("Structured search returned 0. Trying keyword fallback.")
            params = {"pageSize": max_results}
            if condition: params["query.term"] = condition
            if sponsor: params["query.term"] = sponsor
            if location: params["query.location"] = location
            if status: params["filter.overallStatus"] = status.upper()
            data = self._get_json(CLINICALTRIALS_BASE, params)
            studies = data.get("studies", [])

        rows = []
        for st in studies:
            rows.append({
                "nct_id": self._extract(st, ["protocolSection", "identificationModule", "nctId"]),
                "title": self._extract(st, ["protocolSection", "identificationModule", "briefTitle"]),
                "status": self._extract(st, ["protocolSection", "statusModule", "overallStatus"]),
                "phase": self._extract(st, ["protocolSection", "designModule", "phaseList", 0, "phase"]),
                "sponsor": self._extract(st, ["protocolSection", "sponsorCollaboratorsModule", "leadSponsor", "name"]),
            })

        logger.info(f"search_trials returned {len(rows)} results")
        return rows

    def get_trial_details(self, nct_id: str) -> dict:
        """Fetch deep details for a single trial by NCT ID."""
        study = self._get_json(f"{CLINICALTRIALS_BASE}/{nct_id}")
        ps = study.get("protocolSection", {})
        return {
            "nct_id": self._extract(ps, ["identificationModule", "nctId"]),
            "title": self._extract(ps, ["identificationModule", "briefTitle"]),
            "eligibility_criteria": self._extract(ps, ["eligibilityModule", "eligibilityCriteria"]),
            "min_age": self._extract(ps, ["eligibilityModule", "minimumAge"]),
            "max_age": self._extract(ps, ["eligibilityModule", "maximumAge"]),
            "sex": self._extract(ps, ["eligibilityModule", "gender"]),
            "primary_outcomes": self._extract(ps, ["outcomesModule", "primaryOutcomes"], []),
            "secondary_outcomes": self._extract(ps, ["outcomesModule", "secondaryOutcomes"], []),
            "locations": self._extract(ps, ["contactsLocationsModule", "locations"], []),
            "investigators": self._extract(ps, ["contactsLocationsModule", "overallOfficials"], []),
            "sponsor": self._extract(ps, ["sponsorCollaboratorsModule", "leadSponsor", "name"]),
        }

    def match_patient(
        self,
        condition: str,
        age: int = None,
        sex: str = None,
        location: str = None,
    ) -> list[dict]:
        """Match a patient to eligible recruiting trials by age and sex."""
        def parse_age(a):
            try:
                return int(str(a).split()[0])
            except Exception:
                return None

        trials = self.search_trials(condition=condition, location=location, status="RECRUITING", max_results=200)
        if not trials:
            logger.warning("No recruiting trials found for patient matching.")
            return []

        results = []
        for row in trials:
            nct = row.get("nct_id")
            if not nct:
                continue
            d = self.get_trial_details(nct)
            score = 0

            if age:
                min_a = parse_age(d.get("min_age"))
                max_a = parse_age(d.get("max_age"))
                if min_a and age >= min_a: score += 1
                if max_a and age <= max_a: score += 1
                if not min_a and not max_a: score += 0.5

            if sex:
                if d.get("sex") in ("All", sex, None): score += 1

            results.append({
                "nct_id": d.get("nct_id"),
                "title": d.get("title"),
                "min_age": d.get("min_age"),
                "max_age": d.get("max_age"),
                "sex": d.get("sex"),
                "sponsor": d.get("sponsor"),
                "match_score": score,
            })

        results.sort(key=lambda x: x["match_score"], reverse=True)
        logger.info(f"Patient matching complete: {len(results)} trials evaluated")
        return results

    def analyze_endpoints(self, condition: str, max_trials: int = 100) -> dict:
        """Analyze most common primary and secondary endpoints across trials."""
        trials = self.search_trials(condition=condition, max_results=max_trials)
        primary_outcomes = []
        secondary_outcomes = []

        for row in trials:
            nct = row.get("nct_id")
            if not nct:
                continue
            d = self.get_trial_details(nct)
            for o in d.get("primary_outcomes", []):
                if o.get("measure"): primary_outcomes.append(o["measure"])
            for o in d.get("secondary_outcomes", []):
                if o.get("measure"): secondary_outcomes.append(o["measure"])

        logger.info(f"Endpoint analysis complete for condition='{condition}'")
        return {
            "primary": Counter(primary_outcomes).most_common(10),
            "secondary": Counter(secondary_outcomes).most_common(10),
        }

    def search_investigators(
        self,
        condition: str = None,
        location: str = None,
        max_trials: int = 100,
    ) -> list[dict]:
        """Find principal investigators for trials matching a condition."""
        trials = self.search_trials(condition=condition, location=location, max_results=max_trials)
        investigators = []

        for row in trials:
            nct = row.get("nct_id")
            if not nct:
                continue
            d = self.get_trial_details(nct)
            for inv in d.get("investigators", []):
                investigators.append({
                    "name": inv.get("name"),
                    "role": inv.get("role"),
                    "affiliation": inv.get("affiliation"),
                    "nct_id": nct,
                })

        logger.info(f"Investigator search complete: {len(investigators)} found")
        return investigators

    def search_by_sponsor(self, sponsor: str, max_results: int = 200) -> list[dict]:
        """Return all trials associated with a given sponsor name."""
        trials = self.search_trials(sponsor=sponsor, max_results=max_results)
        if not trials:
            logger.warning(f"No trials found for sponsor='{sponsor}'")
        return trials

    def fetch_terminated_trials(self, condition: str) -> dict:
        """Fetch terminated trials with phase-wise counts and top termination reasons."""
        studies = []
        page_token = None

        while True:
            params = {
                "query.cond": condition,
                "filter.overallStatus": "TERMINATED",
                "pageSize": 100,
            }
            if page_token:
                params["pageToken"] = page_token

            data = self._get_json(CLINICALTRIALS_BASE, params)
            studies.extend(data.get("studies", []))
            page_token = data.get("nextPageToken")
            if not page_token:
                break

        phase_counts = defaultdict(int)
        reasons_by_phase = defaultdict(list)

        for study in studies:
            phases = (
                study.get("protocolSection", {})
                .get("designModule", {})
                .get("phases", [])
            )
            phase_label = "/".join(phases) if phases else "Unknown"
            reason = self._clean_text(
                study.get("protocolSection", {})
                .get("statusModule", {})
                .get("whyStopped", "")
            )
            phase_counts[phase_label] += 1
            reasons_by_phase[phase_label].append(reason)

        summary = {}
        for phase, reasons in reasons_by_phase.items():
            summary[phase] = {
                "count": phase_counts[phase],
                "top_reasons": Counter(reasons).most_common(5),
            }

        logger.info(f"Terminated trials analysis: {len(studies)} trials for condition='{condition}'")
        return summary