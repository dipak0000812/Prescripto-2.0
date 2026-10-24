"""
Knowledge Provider Base Specification.
Provides contract for external or internal clinical safety sources.
Enforces NOT_EVALUATED guarantee and capability-gated evaluation.
"""
from abc import ABC, abstractmethod
from typing import List, Set, Optional
import uuid

from prescripto.domain.safety.models import (
    SafetyCheckType,
    DomainRiskFinding,
    FindingStatus,
    NotEvaluatedReason,
)
from prescripto.domain.medication.models import CanonicalMedication


class KnowledgeProvider(ABC):
    """Abstract base class for all knowledge providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'OPENFDA', 'CDSCO')."""
        pass

    @property
    @abstractmethod
    def provider_version(self) -> str:
        """Version of the provider dataset."""
        pass

    @property
    @abstractmethod
    def supported_checks(self) -> Set[SafetyCheckType]:
        """Set of SafetyCheckType checks this provider supports."""
        pass

    def supports_check(self, check_type: SafetyCheckType) -> bool:
        return check_type in self.supported_checks

    @abstractmethod
    def evaluate(
        self,
        analysis_id: uuid.UUID,
        check_type: SafetyCheckType,
        medication_id: uuid.UUID,
        medication: Optional[CanonicalMedication] = None,
    ) -> List[DomainRiskFinding]:
        """
        Evaluates a medication against this provider.
        Must return DomainRiskFinding instances.
        If provider lacks capability or cannot evaluate, MUST return a NOT_EVALUATED finding with a non-null reason.
        """
        pass
