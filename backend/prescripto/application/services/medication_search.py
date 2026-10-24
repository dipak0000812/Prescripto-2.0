"""
Medication Master Search and Candidate Generation Service.
Implements exact and fuzzy matching against the medications table.
"""
import uuid
import difflib
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from prescripto.db.models.medication import Medication as DBMedication
from prescripto.domain.medication.models import (
    CanonicalMedication,
    CandidateMatch,
    MatchingStrategy,
    MedicationResolutionResult,
    resolve_candidate_matches,
)


def _to_domain_medication(db_med: DBMedication) -> CanonicalMedication:
    return CanonicalMedication(
        id=db_med.id,
        brand_name=db_med.brand_name,
        generic_name=db_med.generic_name,
        active_ingredients=list(db_med.active_ingredients or []),
        strength=db_med.strength,
        dosage_form=db_med.dosage_form,
        route=db_med.route,
        rxnorm_cui=db_med.rxnorm_cui,
        source_class=db_med.source_class,
        source_version=db_med.source_version,
        verification_status=db_med.verification_status,
        provenance_metadata=dict(db_med.provenance_metadata or {}),
    )


class MedicationSearchService:
    """Generates candidate matches from the Medication Master for an extracted text line."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def search_candidates(
        self,
        extracted_text: str,
        limit: int = 5,
    ) -> MedicationResolutionResult:
        if not extracted_text or not extracted_text.strip():
            return MedicationResolutionResult(
                extracted_text=extracted_text,
                resolution_status=resolve_candidate_matches("", []).resolution_status,
                resolved_medication=None,
                candidates=[],
            )

        query_text = extracted_text.strip().lower()
        all_meds = self.db.query(DBMedication).all()

        scored_candidates: List[CandidateMatch] = []

        for med in all_meds:
            brand_lower = med.brand_name.lower()
            generic_lower = med.generic_name.lower()
            ingredients = [i.lower() for i in (med.active_ingredients or [])]

            # 1. Exact match
            if query_text == brand_lower or query_text == generic_lower or any(query_text == i for i in ingredients):
                scored_candidates.append(
                    CandidateMatch(
                        medication=_to_domain_medication(med),
                        candidate_score=1.0,
                        matching_strategy=MatchingStrategy.EXACT.value,
                        source_vocabulary="CDSCO",
                    )
                )
                continue

            # 2. Substring match (e.g. "Augmentin 625" in "Augmentin 625 Duo" or "Dolo 650" in "Dolo 650")
            if query_text in brand_lower or brand_lower in query_text:
                score = 0.90
                scored_candidates.append(
                    CandidateMatch(
                        medication=_to_domain_medication(med),
                        candidate_score=score,
                        matching_strategy=MatchingStrategy.FUZZY_SIMILARITY.value,
                        source_vocabulary="CDSCO",
                    )
                )
                continue

            if query_text in generic_lower or generic_lower in query_text:
                score = 0.88
                scored_candidates.append(
                    CandidateMatch(
                        medication=_to_domain_medication(med),
                        candidate_score=score,
                        matching_strategy=MatchingStrategy.FUZZY_SIMILARITY.value,
                        source_vocabulary="CDSCO",
                    )
                )
                continue

            # 3. Fuzzy similarity via sequence matcher
            sim_brand = difflib.SequenceMatcher(None, query_text, brand_lower).ratio()
            sim_generic = difflib.SequenceMatcher(None, query_text, generic_lower).ratio()
            best_sim = max(sim_brand, sim_generic)

            if best_sim >= 0.65:
                scored_candidates.append(
                    CandidateMatch(
                        medication=_to_domain_medication(med),
                        candidate_score=round(best_sim, 3),
                        matching_strategy=MatchingStrategy.FUZZY_SIMILARITY.value,
                        source_vocabulary="CDSCO",
                    )
                )

        # Sort and limit candidates
        sorted_matches = sorted(scored_candidates, key=lambda c: c.candidate_score, reverse=True)[:limit]

        return resolve_candidate_matches(extracted_text=extracted_text, candidates=sorted_matches)
