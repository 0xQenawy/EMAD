import html
import logging
import random
import re
import time
from typing import Callable, Dict, List, Optional, Set
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup

from .base import BaseJobSource, UnifiedJob

logger = logging.getLogger(__name__)


class TanqeebSource(BaseJobSource):
    """
    Tanqeeb (تنقيب) regional job board source adapter for Egypt, Saudi Arabia, UAE, and MENA.
    """

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
        "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="128", "Google Chrome";v="128"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
    }

    # Mapping of country/city keywords to Tanqeeb subdomain
    COUNTRY_SUBDOMAINS = {
        "saudi": "https://saudi.tanqeeb.com",
        "سعودية": "https://saudi.tanqeeb.com",
        "رياض": "https://saudi.tanqeeb.com",
        "riyadh": "https://saudi.tanqeeb.com",
        "جدة": "https://saudi.tanqeeb.com",
        "jeddah": "https://saudi.tanqeeb.com",
        "dammam": "https://saudi.tanqeeb.com",
        "دمام": "https://saudi.tanqeeb.com",
        "mecca": "https://saudi.tanqeeb.com",
        "مكة": "https://saudi.tanqeeb.com",
        "medina": "https://saudi.tanqeeb.com",
        "المدينة": "https://saudi.tanqeeb.com",

        "uae": "https://uae.tanqeeb.com",
        "إمارات": "https://uae.tanqeeb.com",
        "امارات": "https://uae.tanqeeb.com",
        "dubai": "https://uae.tanqeeb.com",
        "دبي": "https://uae.tanqeeb.com",
        "abu dhabi": "https://uae.tanqeeb.com",
        "أبوظبي": "https://uae.tanqeeb.com",
        "ابوظبي": "https://uae.tanqeeb.com",
        "sharjah": "https://uae.tanqeeb.com",
        "الشارقة": "https://uae.tanqeeb.com",

        "qatar": "https://qatar.tanqeeb.com",
        "قطر": "https://qatar.tanqeeb.com",
        "kuwait": "https://kuwait.tanqeeb.com",
        "كويت": "https://kuwait.tanqeeb.com",
        "bahrain": "https://bahrain.tanqeeb.com",
        "بحرين": "https://bahrain.tanqeeb.com",
        "oman": "https://oman.tanqeeb.com",
        "عمان": "https://oman.tanqeeb.com",
        "jordan": "https://jordan.tanqeeb.com",
        "أردن": "https://jordan.tanqeeb.com",
    }

    DEFAULT_BASE_URL = "https://egypt.tanqeeb.com"

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)

    @property
    def source_name(self) -> str:
        return "Tanqeeb"

    def resolve_base_url(self, location: str) -> str:
        """Resolve the appropriate Tanqeeb country subdomain based on location."""
        loc_lower = location.lower().strip()
        for key, base_url in self.COUNTRY_SUBDOMAINS.items():
            if key in loc_lower:
                return base_url
        return self.DEFAULT_BASE_URL

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
        limit_per_query: int = 40,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> List[UnifiedJob]:
        """Fetch and extract jobs from Tanqeeb for Egypt, Saudi Arabia, UAE, etc."""
        base_url = self.resolve_base_url(location)
        extracted_jobs: List[UnifiedJob] = []
        seen_job_ids: Set[str] = set()

        # Calculate pages needed based on limit (Tanqeeb provides ~40 jobs per page)
        max_pages = max(1, min(limit_per_query // 30, 2))

        for kw in keywords:
            clean_kw = kw.strip()
            if not clean_kw:
                continue

            for page in range(1, max_pages + 1):
                search_url = f"{base_url}/ar/jobs/search"
                params = {
                    "keywords": clean_kw,
                    "page": str(page),
                }

                try:
                    resp = self.session.get(search_url, params=params, timeout=12)
                    if resp.status_code != 200:
                        logger.warning(f"Tanqeeb ({base_url}) returned {resp.status_code} for query '{clean_kw}'")
                        break

                    soup = BeautifulSoup(resp.content, "html.parser")
                    # Select only top-level job cards (avoiding nested child containers)
                    cards = soup.find_all("div", class_=lambda c: c and "search-job-card" in c and "card-body" in c)
                    if not cards:
                        cards = soup.find_all("div", class_=lambda c: c and "search-job-card" in c)
                    if not cards:
                        break

                    for card in cards:
                        try:
                            # 1. Job Title & Link
                            title_elem = card.find(["h2", "h3"], class_=lambda c: c and "search-job-title" in c)
                            if not title_elem:
                                title_elem = card.find(["h2", "h3"])
                            if not title_elem:
                                continue

                            link_elem = title_elem.find("a", href=True) or card.find("a", class_=lambda c: c and "title" in c)
                            if not link_elem:
                                continue

                            raw_title = self._normalize_string(title_elem.get_text())
                            if not raw_title:
                                continue

                            raw_href = link_elem["href"].strip()
                            full_url = raw_href if raw_href.startswith("http") else f"{base_url}{raw_href}"

                            # Extract unique job ID from URL (e.g. /021073318.html -> 021073318)
                            job_id_match = re.search(r"(\d{6,12})\.html", raw_href)
                            if job_id_match:
                                job_id = f"tanqeeb_{job_id_match.group(1)}"
                            else:
                                job_id = f"tanqeeb_{re.sub(r'[^a-zA-Z0-9]', '', raw_href)[-12:]}"

                            if not job_id or job_id in seen_job_ids:
                                continue

                            # 2. Company Name
                            company = "غير محدد"
                            company_elem = card.find("div", class_=lambda c: c and "search-job-company-name" in c)
                            if company_elem:
                                company = self._normalize_string(company_elem.get_text())
                            else:
                                company_link = card.find("a", href=lambda h: h and "/c/" in h)
                                if company_link:
                                    company = self._normalize_string(company_link.get_text())

                            # 3. Location
                            loc = location
                            loc_elem = card.find("div", class_=lambda c: c and "search-job-company-city" in c)
                            if loc_elem:
                                loc = self._normalize_string(loc_elem.get_text())
                            else:
                                meta_loc = card.find("span", class_=lambda c: c and "search-job-workplace-location" in c)
                                if meta_loc:
                                    loc = self._normalize_string(meta_loc.get_text())

                            # 4. Date Posted (Strictly match search-job-date and exclude separator dots)
                            arabic_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
                            date_elem = card.find("span", class_=lambda c: c and "search-job-date" in c and "sep" not in c)
                            if not date_elem:
                                date_elem = card.find("span", class_="search-job-date")

                            posted_date = "غير محدد"
                            if date_elem:
                                raw_date = self._normalize_string(date_elem.get_text())
                                clean_date = raw_date.replace("·", "").replace("•", "").strip()
                                if clean_date:
                                    posted_date = clean_date.translate(arabic_digits)

                            # 5. Description Snippet (useful for matching & classification)
                            desc_snippet = ""
                            desc_elem = card.find("div", attrs={"data-jb-field": "description"}) or card.find("div", class_=lambda c: c and "description" in c)
                            if desc_elem:
                                desc_snippet = self._normalize_string(desc_elem.get_text())[:400]

                            seen_job_ids.add(job_id)
                            extracted_jobs.append(
                                UnifiedJob(
                                    job_id=job_id,
                                    title=raw_title,
                                    company=company,
                                    location=loc,
                                    url=full_url,
                                    primary_application_url=full_url,
                                    sources=["Tanqeeb"],
                                    posted_date=posted_date,
                                    description=desc_snippet,
                                    raw_source_data={
                                        "source": "Tanqeeb",
                                        "base_url": base_url,
                                        "keyword": clean_kw,
                                    },
                                )
                            )
                        except Exception as parse_err:
                            logger.debug(f"Error parsing Tanqeeb job card: {parse_err}")
                            continue

                    time.sleep(random.uniform(0.5, 1.0))

                except requests.RequestException as req_err:
                    logger.warning(f"Tanqeeb network error for '{clean_kw}': {req_err}")
                    break
                except Exception as e:
                    logger.error(f"Unexpected error in Tanqeeb scraping: {e}")
                    break

        return extracted_jobs
