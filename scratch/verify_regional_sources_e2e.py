import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraper import JobDiscoveryEngine
from sources.tanqeeb import TanqeebSource


def test_tanqeeb_routing():
    print("\n--- Test Tanqeeb Subdomain Routing ---")
    src = TanqeebSource()
    assert src.resolve_base_url("Cairo, Egypt") == "https://egypt.tanqeeb.com"
    assert src.resolve_base_url("Alexandria, Egypt") == "https://egypt.tanqeeb.com"
    assert src.resolve_base_url("Riyadh, Saudi Arabia") == "https://saudi.tanqeeb.com"
    assert src.resolve_base_url("Jeddah, Saudi Arabia") == "https://saudi.tanqeeb.com"
    assert src.resolve_base_url("Dubai, UAE") == "https://uae.tanqeeb.com"
    assert src.resolve_base_url("Abu Dhabi, UAE") == "https://uae.tanqeeb.com"
    assert src.resolve_base_url("Doha, Qatar") == "https://qatar.tanqeeb.com"
    print("PASS: Subdomain routing maps accurately to Egypt, Saudi Arabia, UAE, and Gulf.")


def test_live_egypt_discovery():
    print("\n--- Test Live Egypt Discovery (LinkedIn + Tanqeeb) ---")
    engine = JobDiscoveryEngine()
    results = engine.discover(
        keywords=["flutter"],
        location="Cairo, Egypt",
        pages_per_keyword=1,
    )
    print(f"Total Unique Jobs: {len(results)}")
    print(f"Metrics: {engine.last_metrics}")
    assert len(results) > 0, "Expected at least 1 job for Egypt"
    sources_found = set()
    for r in results:
        for s in r.get("sources", []):
            sources_found.add(s)
    print(f"Sources represented: {sources_found}")
    print("PASS: Live discovery succeeded for Egypt.")


def test_live_saudi_discovery():
    print("\n--- Test Live Saudi Discovery (LinkedIn + Tanqeeb) ---")
    engine = JobDiscoveryEngine()
    results = engine.discover(
        keywords=["backend"],
        location="Riyadh, Saudi Arabia",
        pages_per_keyword=1,
    )
    print(f"Total Unique Jobs: {len(results)}")
    print(f"Metrics: {engine.last_metrics}")
    assert len(results) > 0, "Expected at least 1 job for Saudi Arabia"
    print("PASS: Live discovery succeeded for Saudi Arabia.")


def test_live_uae_discovery():
    print("\n--- Test Live UAE Discovery (LinkedIn + Tanqeeb) ---")
    engine = JobDiscoveryEngine()
    results = engine.discover(
        keywords=["frontend"],
        location="Dubai, UAE",
        pages_per_keyword=1,
    )
    print(f"Total Unique Jobs: {len(results)}")
    print(f"Metrics: {engine.last_metrics}")
    assert len(results) > 0, "Expected at least 1 job for UAE"
    print("PASS: Live discovery succeeded for UAE.")


if __name__ == "__main__":
    test_tanqeeb_routing()
    test_live_egypt_discovery()
    test_live_saudi_discovery()
    test_live_uae_discovery()
    print("\n=======================================================")
    print("ALL REGIONAL E2E DISCOVERY TESTS PASSED FOR EGYPT, SAUDI, UAE!")
    print("=======================================================")
