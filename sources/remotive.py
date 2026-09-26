import html
import logging
import re
from typing import Any, Callable, Dict, List, Optional, Set
import requests

from .base import BaseJobSource, UnifiedJob

logger = logging.getLogger(__name__)


class RemotiveSource(BaseJobSource):
    """Remotive public tech and remote job board source adapter."""

    BASE_URL = "https://remotive.com/api/remote-jobs"

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
    }

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)

    @property
    def source_name(self) -> str:
        return "Remotive"

    @staticmethod
    def _strip_html(text: str) -> str:
        if not text:
            return ""
        clean = re.sub(r"<[^>]+>", " ", text)
        return re.sub(r"\s+", " ", clean).strip()

    def search(
        self,
        keywords: List[str],
        location: str,
        job_type: str = "all",
        seniority: str = "all",
        workplace_type: str = "all",
        date_posted: str = "all",
        limit_per_query: int = 25,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> List[UnifiedJob]:
        """Fetch and extract jobs from Remotive public API."""
        extracted_jobs: List[UnifiedJob] = []
        seen_job_ids: Set[str] = set()

        for kw in keywords:
            clean_kw = kw.strip()
            if not clean_kw:
                continue

            params = {
                "search": clean_kw,
                "limit": str(limit_per_query),
            }

            try:
                resp = self.session.get(self.BASE_URL, params=params, timeout=10)
                if resp.status_code != 200:
                    logger.warning(f"Remotive returned status {resp.status_code} for '{clean_kw}'")
                    continue

                data = resp.json()
                raw_job_list = data.get("jobs", [])
                if not raw_job_list:
                    continue

                for item in raw_job_list:
                    try:
                        job_id = str(item.get("id", "")).strip()
                        if not job_id or job_id in seen_job_ids:
                            continue

                        title = str(item.get("title", "")).strip()
                        company = str(item.get("company_name", "")).strip() or "غير محدد"
                        if not title:
                            continue

                        # Candidate location (often 'Worldwide', 'USA', etc.)
                        req_loc = str(item.get("candidate_required_location", "")).strip()
                        loc_display = f"{req_loc} (عن بُعد / Remote)" if req_loc else "عن بُعد (Worldwide)"

                        raw_url = str(item.get("url", "")).strip()
                        pub_date = str(item.get("publication_date", "غير محدد")).split("T")[0]
                        desc_snippet = self._strip_html(str(item.get("description", "")))[:500]

                        # Raw job type hint if available
                        raw_job_type = str(item.get("job_type", "")).strip()

                        seen_job_ids.add(job_id)
                        extracted_jobs.append(
                            UnifiedJob(
                                job_id=f"remotive_{job_id}",
                                title=title,
                                company=company,
                                location=loc_display,
                                url=raw_url,
                                primary_application_url=raw_url,
                                sources=["Remotive"],
                                posted_date=pub_date,
                                description=desc_snippet,
                                raw_source_data={
                                    "source": "Remotive",
                                    "raw_job_type": raw_job_type,
                                    "candidate_location": req_loc,
                                    "keyword": clean_kw,
                                },
                            )
                        )
                    except Exception as item_err:
                        logger.debug(f"Error parsing Remotive item: {item_err}")
                        continue

            except requests.RequestException as req_err:
                logger.warning(f"Remotive network error for '{clean_kw}': {req_err}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error querying Remotive: {e}")
                continue

        return extracted_jobs
