import html
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, urlunparse


@dataclass
class UnifiedJob:
    """Unified job listing data model across all sources."""
    job_id: str
    title: str
    company: str
    location: str
    job_type: str = "غير محدد"
    seniority: str = "غير محدد"
    workplace_type: str = "غير محدد"
    url: str = "#"
    primary_application_url: str = "#"
    sources: List[str] = field(default_factory=list)
    posted_date: str = "غير محدد"
    description: str = ""
    relevance_score: int = 0
    raw_source_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert UnifiedJob to dict matching Emad's UI and export formats."""
        source_label = " + ".join(self.sources) if self.sources else "غير محدد"
        return {
            "Job ID": self.job_id,
            "المسمى الوظيفي": self.title,
            "الشركة": self.company,
            "المكان": self.location,
            "نوع الوظيفة": self.job_type,
            "مستوى الخبرة": self.seniority,
            "بيئة العمل": self.workplace_type,
            "تاريخ النشر": self.posted_date,
            "رابط التقديم": self.primary_application_url or self.url,
            "المصدر": source_label,
            "sources": list(self.sources),
            "relevance_score": self.relevance_score,
            "description": self.description,
        }


class BaseJobSource(ABC):
    """Abstract Base Class for all job discovery sources."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of the job source (e.g. 'LinkedIn', 'Tanqeeb')."""
        pass

    @abstractmethod
    def search(
        self,
        keywords: List[str],
        location: str,
        job_type: str = "all",
        seniority: str = "all",
        workplace_type: str = "all",
        date_posted: str = "all",
        limit_per_query: int = 25,
    ) -> List[UnifiedJob]:
        """Search and extract job listings from this source."""
        pass
