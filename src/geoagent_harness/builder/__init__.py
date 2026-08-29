"""Proposal-only Builder Agent contracts."""

from geoagent_harness.builder.policy import (
    validate_builder_proposal,
)
from geoagent_harness.builder.schemas import (
    BuilderArtifactKind,
    BuilderArtifactRequest,
    BuilderFileProposal,
    BuilderProposal,
    BuilderRequest,
    BuilderCandidateInspectionResult,
    BuilderCandidateManifest,
    BuilderCandidateManifestFile,
    BuilderCandidateTestRecord,
    BuilderGenerationResult,
    BuilderMaterializationResult,
    BuilderCandidateTestAssessment,
    BuilderReviewPackage,
    BuilderReviewStorageResult,
)
from geoagent_harness.builder.agent import (
    BuilderAgentError,
    BuilderModelClientProtocol,
    generate_builder_proposal,
)
from geoagent_harness.builder.prompt import (
    build_builder_request,
)
from geoagent_harness.builder.review import (
    BuilderReviewError,
    assemble_builder_review_package,
)
from geoagent_harness.builder.service import (
    propose_builder_candidate,
)
from geoagent_harness.builder.request_loader import (
    BuilderRequestLoadError,
    load_builder_request,
)
from geoagent_harness.builder.storage import (
    BuilderGenerationStorageError,
    builder_generation_sha256,
    canonical_builder_generation_json,
    load_builder_generation,
)
from geoagent_harness.builder.materialization import (
    BuilderMaterializationError,
    materialize_builder_proposal,
)
from geoagent_harness.builder.inspection import (
    BuilderCandidateInspectionError,
    inspect_builder_candidate,
    load_builder_candidate_manifest,
)
from geoagent_harness.builder.test_evidence import (
    BuilderCandidateTestEvidenceError,
    load_builder_candidate_test_record,
)
from geoagent_harness.builder.testing import (
    BuilderCandidateTestingError,
    assess_builder_candidate_tests,
)
from geoagent_harness.builder.review_storage import (
    BuilderReviewStorageError,
    builder_review_sha256,
    canonical_builder_review_json,
    persist_builder_review_package,
)

__all__ = [
    "BuilderArtifactKind",
    "BuilderArtifactRequest",
    "BuilderFileProposal",
    "BuilderProposal",
    "BuilderRequest",
    "validate_builder_proposal",
    "BuilderAgentError",
    "BuilderGenerationResult",
    "BuilderModelClientProtocol",
    "build_builder_request",
    "generate_builder_proposal",
    "propose_builder_candidate",
    "BuilderRequestLoadError",
    "load_builder_request",
    "BuilderGenerationStorageError",
    "builder_generation_sha256",
    "canonical_builder_generation_json",
    "load_builder_generation",
    "BuilderMaterializationError",
    "BuilderMaterializationResult",
    "materialize_builder_proposal",
    "BuilderCandidateInspectionError",
    "BuilderCandidateInspectionResult",
    "BuilderCandidateManifest",
    "BuilderCandidateManifestFile",
    "inspect_builder_candidate",
    "BuilderCandidateTestRecord",
    "BuilderCandidateTestAssessment",
    "BuilderCandidateTestEvidenceError",
    "BuilderCandidateTestingError",
    "assess_builder_candidate_tests",
    "load_builder_candidate_test_record",
    "BuilderReviewError",
    "BuilderReviewPackage",
    "assemble_builder_review_package",
    "load_builder_candidate_manifest",
    "BuilderReviewStorageError",
    "BuilderReviewStorageResult",
    "builder_review_sha256",
    "canonical_builder_review_json",
    "persist_builder_review_package",
]
