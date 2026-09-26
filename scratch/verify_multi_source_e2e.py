import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from unittest.mock import MagicMock
from sources.base import BaseJobSource, UnifiedJob
from dedup import JobDeduplicator
from scraper import JobClassifier, JobDiscoveryEngine


def test_1_cross_source_duplicate():
    print("\n--- Test 1: Cross-Source Duplicate ---")
    j1 = UnifiedJob(
        job_id="li_1",
        title="Frontend Developer Intern",
        company="ABC Technologies",
        location="Cairo, Egypt",
        sources=["LinkedIn"],
        url="https://linkedin.com/jobs/view/123?tracking=abc",
        primary_application_url="https://linkedin.com/jobs/view/123",
    )
    j2 = UnifiedJob(
        job_id="rem_1",
        title="Frontend Developer Intern",
        company="ABC Technologies",
        location="Cairo, Egypt",
        sources=["Remotive"],
        url="https://remotive.com/job/456?ref=test",
        primary_application_url="https://remotive.com/job/456",
    )
    unique, count = JobDeduplicator.deduplicate_jobs([j1, j2])
    assert len(unique) == 1, f"Expected 1 unique job, got {len(unique)}"
    assert count == 1, f"Expected 1 duplicate merged, got {count}"
    assert set(unique[0].sources) == {"LinkedIn", "Remotive"}, f"Sources mismatch: {unique[0].sources}"
    print("PASS: Cross-source duplicate correctly merged into 1 job with both sources.")


def test_2_distinct_roles():
    print("\n--- Test 2: Distinct Roles in Same Company ---")
    j1 = UnifiedJob(
        job_id="li_1",
        title="Frontend Developer Intern",
        company="ABC Technologies",
        location="Cairo, Egypt",
        sources=["LinkedIn"],
    )
    j2 = UnifiedJob(
        job_id="rem_2",
        title="Backend Developer Intern",
        company="ABC Technologies",
        location="Cairo, Egypt",
        sources=["Remotive"],
    )
    unique, count = JobDeduplicator.deduplicate_jobs([j1, j2])
    assert len(unique) == 2, f"Expected 2 unique jobs, got {len(unique)}"
    assert count == 0, f"Expected 0 duplicates merged, got {count}"
    print("PASS: Distinct roles in same company remain 2 separate jobs.")


def test_3_conservative_company():
    print("\n--- Test 3: Conservative Company Normalization ---")
    j1 = UnifiedJob(
        job_id="1",
        title="AI Engineer",
        company="Smart Eye",
        location="Cairo, Egypt",
        sources=["LinkedIn"],
    )
    j2 = UnifiedJob(
        job_id="2",
        title="AI Engineer",
        company="Smart Eye Technologies",
        location="Cairo, Egypt",
        sources=["Remotive"],
    )
    unique, count = JobDeduplicator.deduplicate_jobs([j1, j2])
    assert len(unique) == 2, f"Expected 2 separate jobs, got {len(unique)}"
    print("PASS: Smart Eye and Smart Eye Technologies are NOT merged.")


def test_4_legal_suffix():
    print("\n--- Test 4: Legal Suffix Merging ---")
    j1 = UnifiedJob(
        job_id="1",
        title="Flutter Developer",
        company="Vortex Corp",
        location="Cairo, Egypt",
        sources=["LinkedIn"],
    )
    j2 = UnifiedJob(
        job_id="2",
        title="Flutter Developer",
        company="Vortex LLC",
        location="Cairo, Egypt",
        sources=["Remotive"],
    )
    unique, count = JobDeduplicator.deduplicate_jobs([j1, j2])
    assert len(unique) == 1, f"Expected 1 merged job, got {len(unique)}"
    assert set(unique[0].sources) == {"LinkedIn", "Remotive"}
    print("PASS: Vortex Corp and Vortex LLC merged successfully.")


def test_5_pipeline_order_hard_filtering_before_dedup():
    print("\n--- Test 5: Pipeline Order (Hard Filter Before Dedup) ---")
    # Simulate a Senior Backend job and a Frontend Intern job
    mock_src = MagicMock(spec=BaseJobSource)
    mock_src.source_name = "MockSource"
    mock_src.search.return_value = [
        UnifiedJob(
            job_id="m1",
            title="Senior Backend Team Lead",
            company="MegaCorp",
            location="Cairo, Egypt",
            sources=["MockSource"],
            raw_source_data={"keyword": "frontend"},
        ),
        UnifiedJob(
            job_id="m2",
            title="Frontend Developer Intern",
            company="Startup",
            location="Cairo, Egypt",
            sources=["MockSource"],
            raw_source_data={"keyword": "frontend"},
        ),
    ]

    engine = JobDiscoveryEngine(sources=[mock_src])
    results = engine.discover(
        keywords=["frontend intern"],
        location="Cairo, Egypt",
        job_type="internship",
        seniority="internship",
    )

    # Only Frontend Developer Intern should remain
    assert len(results) == 1, f"Expected 1 job after hard filtering, got {len(results)}"
    assert "Frontend Developer Intern" in results[0]["المسمى الوظيفي"]
    assert engine.last_metrics["passed_filters"] == 1
    print("PASS: Hard filtering cleanly rejected non-matching roles before deduplication.")


def test_6_same_company_title_different_locations():
    print("\n--- Test 6: Same Company + Title in Different Locations ---")
    j1 = UnifiedJob(
        job_id="1",
        title="Frontend Developer",
        company="Vodafone",
        location="Cairo, Egypt",
        sources=["LinkedIn"],
    )
    j2 = UnifiedJob(
        job_id="2",
        title="Frontend Developer",
        company="Vodafone",
        location="Alexandria, Egypt",
        sources=["Remotive"],
    )
    unique, count = JobDeduplicator.deduplicate_jobs([j1, j2])
    assert len(unique) == 2, f"Expected 2 separate jobs, got {len(unique)}"
    print("PASS: Cairo vs Alexandria for same company/title remain 2 separate jobs.")


def test_7_fault_isolation():
    print("\n--- Test 7: Fault Isolation ---")
    failing_src = MagicMock(spec=BaseJobSource)
    failing_src.source_name = "BrokenSource"
    failing_src.search.side_effect = RuntimeError("Simulated connection timeout / 500")

    working_src = MagicMock(spec=BaseJobSource)
    working_src.source_name = "HealthySource"
    working_src.search.return_value = [
        UnifiedJob(
            job_id="h1",
            title="Flutter Developer",
            company="HealthyCo",
            location="Cairo, Egypt",
            sources=["HealthySource"],
            raw_source_data={"keyword": "flutter"},
        )
    ]

    engine = JobDiscoveryEngine(sources=[failing_src, working_src])
    results = engine.discover(keywords=["flutter"], location="Cairo, Egypt")
    assert len(results) == 1, f"Expected 1 job from HealthySource, got {len(results)}"
    assert results[0]["المصدر"] == "HealthySource"
    assert engine.last_metrics["source_counts"]["BrokenSource"] == 0
    assert engine.last_metrics["source_counts"]["HealthySource"] == 1
    print("PASS: Failure in BrokenSource did not interrupt discovery; HealthySource succeeded.")


if __name__ == "__main__":
    test_1_cross_source_duplicate()
    test_2_distinct_roles()
    test_3_conservative_company()
    test_4_legal_suffix()
    test_5_pipeline_order_hard_filtering_before_dedup()
    test_6_same_company_title_different_locations()
    test_7_fault_isolation()
    print("\n==========================================")
    print("ALL 7 CORE VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("==========================================")
