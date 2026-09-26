"""
Integration tests for Medication Master Seeding and Search Service.
"""
from scripts.seed_medications import seed_medications
from prescripto.application.services.medication_search import MedicationSearchService
from prescripto.domain.medication.models import ResolutionStatus


def test_seed_and_search_medications(db_session):
    # 1. Seed medications
    inserted = seed_medications(db_session)
    assert inserted > 0

    # 2. Idempotency: re-seeding inserts 0 new items
    inserted_again = seed_medications(db_session)
    assert inserted_again == 0

    # 3. Test exact match
    service = MedicationSearchService(db=db_session)
    result = service.search_candidates("Augmentin 625 Duo")
    assert result.resolution_status == ResolutionStatus.RESOLVED
    assert result.resolved_medication is not None
    assert "amoxicillin" in result.resolved_medication.generic_name.lower()

    # 4. Test partial / fuzzy match
    result_dolo = service.search_candidates("Dolo 650")
    assert result_dolo.resolution_status == ResolutionStatus.RESOLVED
    assert result_dolo.resolved_medication.brand_name == "Dolo 650"

    # 5. Test unknown medication
    result_unknown = service.search_candidates("NonExistentDrug12345")
    assert result_unknown.resolution_status == ResolutionStatus.UNRESOLVED
    assert result_unknown.resolved_medication is None
