import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
import ulid

from research_tool.domain import Evidence, EvidenceType, EvidenceTheme
from research_tool.core.evidence_manager import EvidenceManager

@pytest.fixture
def evidence_repo():
    repo = AsyncMock()
    # Ensure create returns what is passed
    repo.create.side_effect = lambda ev: ev
    return repo

@pytest.fixture
def entity_repo():
    return AsyncMock()

@pytest.fixture
def file_storage():
    storage = AsyncMock()
    storage.save_screenshot.return_value = "mock_screenshot_path.png"
    return storage

@pytest.fixture
def yield_tracker():
    return MagicMock()

@pytest.fixture
def evidence_manager(evidence_repo, entity_repo, file_storage, yield_tracker):
    return EvidenceManager(
        run_id="run-123",
        evidence_repo=evidence_repo,
        entity_repo=entity_repo,
        file_storage=file_storage,
        yield_tracker=yield_tracker,
    )

@pytest.mark.asyncio
async def test_add_evidence_success(evidence_manager, evidence_repo, file_storage, yield_tracker):
    with patch("research_tool.core.evidence_manager.build_evidence_provenance") as mock_build_prov:
        mock_build_prov.return_value = {
            "run_id": "run-123",
            "source_entity_id": "entity-1",
            "root_seed_id": "seed-1"
        }
        
        evidence = await evidence_manager.add_evidence(
            entity_id="entity-1",
            evidence_type=EvidenceType.PRODUCT_CLAIM,
            raw_text="Some text",
            source_platform="reddit",
            source_url="http://reddit.com",
            root_seed_id="seed-1"
        )
        
        assert evidence.entity_id == "entity-1"
        assert evidence.evidence_type == EvidenceType.PRODUCT_CLAIM
        assert evidence.raw_text == "Some text"
        assert evidence.run_id == "run-123"
        
        evidence_repo.create.assert_awaited_once()
        yield_tracker.record_evidence.assert_called_once()
        file_storage.save_evidence_json.assert_awaited_once()

@pytest.mark.asyncio
async def test_add_evidence_with_screenshot(evidence_manager, file_storage):
    with patch("research_tool.core.evidence_manager.build_evidence_provenance") as mock_build_prov:
        mock_build_prov.return_value = {
            "run_id": "run-123",
            "source_entity_id": "entity-1",
            "root_seed_id": "seed-1"
        }
        
        screenshot_bytes = b"fake-image-bytes"
        evidence = await evidence_manager.add_evidence(
            entity_id="entity-1",
            evidence_type=EvidenceType.PRODUCT_CLAIM,
            raw_text="Some text",
            source_platform="reddit",
            source_url="http://reddit.com",
            root_seed_id="seed-1",
            screenshot_bytes=screenshot_bytes
        )
        
        file_storage.save_screenshot.assert_awaited_once_with(screenshot_bytes, f"evidence_{evidence.evidence_id}")
        assert evidence.screenshot_path == "mock_screenshot_path.png"

@pytest.mark.asyncio
async def test_add_theme(evidence_manager, evidence_repo):
    expected_theme = EvidenceTheme(
        theme_id="theme-1",
        entity_id="ent-1",
        theme_label="Theme Label",
        frequency=1,
        sample_evidence_ids=["ev-1"],
        updated_at=datetime.now(timezone.utc)
    )
    evidence_repo.upsert_theme.return_value = expected_theme
    
    theme = await evidence_manager.add_theme(
        entity_id="ent-1",
        theme_label="Theme Label",
        sample_ids=["ev-1"]
    )
    
    evidence_repo.upsert_theme.assert_awaited_once()
    args, _ = evidence_repo.upsert_theme.call_args
    assert args[0].entity_id == "ent-1"
    assert args[0].theme_label == "Theme Label"
    assert args[0].sample_evidence_ids == ["ev-1"]
    assert theme == expected_theme

@pytest.mark.asyncio
async def test_list_for_entity(evidence_manager, evidence_repo):
    expected_evidence = [MagicMock(), MagicMock()]
    evidence_repo.list_by_entity.return_value = expected_evidence
    
    result = await evidence_manager.list_for_entity("ent-1")
    
    evidence_repo.list_by_entity.assert_awaited_once_with("ent-1")
    assert result == expected_evidence
