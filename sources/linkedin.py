import logging
import random
import re
import time
from typing import Callable, Dict, List, Optional, Set
import requests
from bs4 import BeautifulSoup

from .base import BaseJobSource, UnifiedJob

logger = logging.getLogger(__name__)


class LinkedInSource(BaseJobSource):
    """LinkedIn guest job discovery source."""

    BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="128", "Google Chrome";v="128"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }

    JOB_TYPE_MAP = {
        "full_time": "F",
        "internship": "I",
        "part_time": "P",
        "contract": "C",
        "temporary": "T",
        "volunteer": "V",
    }

    SENIORITY_MAP = {
        "internship": "1",
        "entry": "2",
        "associate": "3",
        "mid": "4",
        "senior": "4",
        "director": "5",
        "executive": "6",
    }

    WORKPLACE_MAP = {
        "onsite": "1",
        "remote": "2",
        "hybrid": "3",
    }

    DATE_POSTED_MAP = {
        "past_24h": "r86400",
        "past_week": "r604800",
        "past_month": "r2592000",
    }

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)

    @property
    def source_name(self) -> str:
        return "LinkedIn"

    def _generate_targeted_queries(
        self,
        keyword: str,
        job_type: str = "all",
        seniority: str = "all",
        workplace_type: str = "all",
    ) -> List[str]:
        """Generate targeted search queries for LinkedIn search guest endpoint."""
        clean_kw = keyword.strip()
        kw_lower = clean_kw.lower()

        queries = []
        if seniority == "internship" or job_type == "internship":
            if "intern" in kw_lower or "تدريب" in kw_lower:
                queries.append(clean_kw)
            else:
                queries.append(f'"{clean_kw}" intern')
                queries.append(f'"{clean_kw}" internship')
                queries.append(f'"{clean_kw}" trainee')
        elif seniority == "entry":
            if any(k in kw_lower for k in ["junior", "entry", "fresh"]):
                queries.append(clean_kw)
            else:
                queries.append(f'"{clean_kw}" junior')
                queries.append(f'"{clean_kw}" "entry level"')
                queries.append(f'"{clean_kw}" fresh')
        elif seniority == "senior":
            if any(k in kw_lower for k in ["senior", "lead", "sr"]):
                queries.append(clean_kw)
            else:
                queries.append(f'"{clean_kw}" senior')
                queries.append(f'"{clean_kw}" lead')
        elif seniority == "mid":
            if "mid" in kw_lower:
                queries.append(clean_kw)
            else:
                queries.append(f'"{clean_kw}" "mid level"')
                queries.append(clean_kw)
        elif seniority == "director":
            if any(k in kw_lower for k in ["manager", "director", "head"]):
                queries.append(clean_kw)
            else:
                queries.append(f'"{clean_kw}" manager')
                queries.append(f'"{clean_kw}" director')
                queries.append(f'"{clean_kw}" head')
        elif job_type == "contract":
            if any(k in kw_lower for k in ["contract", "freelance", "عقد", "حر", "مستقل"]):
                queries.append(clean_kw)
            else:
                queries.append(f'"{clean_kw}" contract')
                queries.append(f'"{clean_kw}" freelance')
        elif job_type == "part_time":
            if "part" in kw_lower:
                queries.append(clean_kw)
            else:
                queries.append(f'"{clean_kw}" part time')
        else:
            queries.append(clean_kw)

        if workplace_type == "remote" and "remote" not in kw_lower:
            queries = [f"{q} remote" for q in queries]

        return queries

    @staticmethod
    def _normalize_string(text: str) -> str:
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip()

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
        """Fetch and extract raw LinkedIn jobs."""
        extracted_jobs: List[UnifiedJob] = []
        seen_job_ids: Set[str] = set()

        for kw in keywords:
            targeted_queries = self._generate_targeted_queries(
                kw, job_type=job_type, seniority=seniority, workplace_type=workplace_type
            )
            # Fetch up to 2 pages (50 jobs) per targeted query
            for tq in targeted_queries:
                for page in range(2):
                    start = page * 25
                    params = {
                        "keywords": tq,
                        "location": location,
                        "start": str(start),
                    }
                    if job_type in self.JOB_TYPE_MAP:
                        params["f_JT"] = self.JOB_TYPE_MAP[job_type]
                    if seniority in self.SENIORITY_MAP:
                        params["f_E"] = self.SENIORITY_MAP[seniority]
                    if workplace_type in self.WORKPLACE_MAP:
                        params["f_WT"] = self.WORKPLACE_MAP[workplace_type]
                    if date_posted in self.DATE_POSTED_MAP:
                        params["f_TPR"] = self.DATE_POSTED_MAP[date_posted]

                    try:
                        resp = self.session.get(self.BASE_URL, params=params, timeout=12)
                        if resp.status_code == 429:
                            logger.warning("LinkedIn rate limited (429).")
                            break
                        if resp.status_code != 200:
                            break

                        soup = BeautifulSoup(resp.content, "html.parser")
                        cards = soup.find_all("li")
                        if not cards:
                            break

                        for card in cards:
                            try:
                                link_elem = card.find("a", class_="base-card__full-link") or card.find("a")
                                if not link_elem or not link_elem.has_attr("href"):
                                    continue

                                raw_link = link_elem["href"].strip()
                                job_link = raw_link.split("?")[0].strip()

                                parts = job_link.rstrip("/").split("-")
                                job_id = parts[-1] if parts else job_link.rstrip("/").split("/")[-1]

                                if not job_id or job_id in seen_job_ids:
                                    continue

                                title_elem = card.find("h3", class_="base-search-card__title")
                                raw_title = self._normalize_string(title_elem.text if title_elem else "")
                                if not raw_title:
                                    continue

                                company_elem = card.find("h4", class_="base-search-card__subtitle")
                                company = self._normalize_string(company_elem.text if company_elem else "غير محدد")

                                location_elem = card.find("span", class_="job-search-card__location")
                                loc = self._normalize_string(location_elem.text if location_elem else location)

                                date_elem = card.find("time")
                                post_date = "غير محدد"
                                if date_elem:
                                    post_date = (
                                        date_elem["datetime"]
                                        if date_elem.has_attr("datetime")
                                        else self._normalize_string(date_elem.text)
                                    )

                                seen_job_ids.add(job_id)
                                extracted_jobs.append(
                                    UnifiedJob(
                                        job_id=f"linkedin_{job_id}",
                                        title=raw_title,
                                        company=company,
                                        location=loc,
                                        url=job_link,
                                        primary_application_url=job_link,
                                        sources=["LinkedIn"],
                                        posted_date=post_date,
                                        raw_source_data={"query": tq, "keyword": kw},
                                    )
                                )
                            except Exception as card_err:
                                logger.debug(f"Error parsing LinkedIn card: {card_err}")
                                continue

                        time.sleep(random.uniform(0.6, 1.2))

                    except requests.RequestException as req_err:
                        logger.warning(f"LinkedIn request error: {req_err}")
                        break
                    except Exception as e:
                        logger.error(f"Unexpected LinkedIn scraping error: {e}")
                        continue

        return extracted_jobs
