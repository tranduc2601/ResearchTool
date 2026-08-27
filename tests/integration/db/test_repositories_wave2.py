"""Integration tests for Wave 2 repositories: Evidence, Entity, Checkpoint, Event."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
import ulid

from research_tool.domain import (
    ActionEvent,
    AgentStatus,
    CheckpointData,
    CheckpointTrigger,
    Confidence,
    Entity,
    EntityListing,
    EntityRelation,
    EntityType,
    EventActor,
    EventType,
    Evidence,
    EvidenceTheme,
    EvidenceType,
    IdentityConfidence,
    PageType,
    RunSession,
    RunStatus,
    StopCondition,
    WorldState,
)
from research_tool.infrastructure.db.connection import apply_schema
from research_tool.infrastructure.db.repositories import (
    CheckpointRepo,
    EntityRepo,
    EventRepo,
    EvidenceRepo,
    RunRepo,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def db(tmp_path: Path) -> Path:
    """Create a fresh SQLite DB with schema applied."""
    db_path = tmp_path / "test.sqlite3"
    await apply_schema(db_path)
    return db_path


def make_run(**kwargs) -> RunSession:
    defaults = dict(
        run_id=ulid.new().str,
        goal_text="Test run",
        status=RunStatus.RUNNING,
        stop_conditions=[StopCondition.FRONTIER_EXHAUSTED],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return RunSession(**defaults)


def make_entity(run_id: str, name: str = "Test Product", **kwargs) -> Entity:
    defaults = dict(
        entity_id=ulid.new().str,
        run_id=run_id,
        entity_type=EntityType.PRODUCT,
        canonical_name=name,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return Entity(**defaults)


def make_evidence(run_id: str, entity_id: str | None = None, **kwargs) -> Evidence:
    defaults = dict(
        evidence_id=ulid.new().str,
        run_id=run_id,
        entity_id=entity_id,
        evidence_type=EvidenceType.REVIEW,
        source_platform="web",
        captured_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return Evidence(**defaults)


def make_theme(entity_id: str, label: str = "durability", **kwargs) -> EvidenceTheme:
    defaults = dict(
        theme_id=ulid.new().str,
        entity_id=entity_id,
        theme_label=label,
        frequency=1,
        sample_evidence_ids=[],
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return EvidenceTheme(**defaults)


def make_world_state(run_id: str, **kwargs) -> WorldState:
    defaults = dict(
        run_id=run_id,
        platform="web",
        app="browser",
        page_type=PageType.PRODUCT_PAGE,
        confidence=Confidence.KNOWN,
        agent_status=AgentStatus.NORMAL,
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return WorldState(**defaults)


def make_checkpoint(run_id: str, world_state: WorldState, **kwargs) -> CheckpointData:
    defaults = dict(
        checkpoint_id=ulid.new().str,
        run_id=run_id,
        world_state=world_state,
        trigger=CheckpointTrigger.EVIDENCE_SAVED,
        created_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return CheckpointData(**defaults)


def make_event(run_id: str, **kwargs) -> ActionEvent:
    defaults = dict(
        event_id=ulid.new().str,
        run_id=run_id,
        event_type=EventType.NAVIGATE,
        actor=EventActor.AGENT,
        occurred_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return ActionEvent(**defaults)


# ---------------------------------------------------------------------------
# EvidenceRepo tests
# ---------------------------------------------------------------------------


async def test_evidence_create_and_list_by_entity(db: Path) -> None:
    """EvidenceRepo.create then list_by_entity returns the evidence."""
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    entity_repo = EntityRepo(db)
    entity = make_entity(run.run_id)
    await entity_repo.create(entity)

    repo = EvidenceRepo(db)
    ev = make_evidence(run.run_id, entity_id=entity.entity_id)
    await repo.create(ev)

    results = await repo.list_by_entity(entity.entity_id)
    assert len(results) == 1
    assert results[0].evidence_id == ev.evidence_id
    assert results[0].evidence_type == EvidenceType.REVIEW


async def test_evidence_count_by_run_increments(db: Path) -> None:
    """EvidenceRepo.count_by_run increments correctly."""
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = EvidenceRepo(db)
    assert await repo.count_by_run(run.run_id) == 0

    await repo.create(make_evidence(run.run_id))
    assert await repo.count_by_run(run.run_id) == 1

    await repo.create(make_evidence(run.run_id))
    assert await repo.count_by_run(run.run_id) == 2


async def test_evidence_list_by_entity_filtered_by_type(db: Path) -> None:
    """EvidenceRepo.list_by_entity filters by evidence_type."""
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    entity_repo = EntityRepo(db)
    entity = make_entity(run.run_id)
    await entity_repo.create(entity)

    repo = EvidenceRepo(db)
    ev_review = make_evidence(run.run_id, entity_id=entity.entity_id, evidence_type=EvidenceType.REVIEW)
    ev_pain = make_evidence(run.run_id, entity_id=entity.entity_id, evidence_type=EvidenceType.PAIN_POINT)
    await repo.create(ev_review)
    await repo.create(ev_pain)

    reviews = await repo.list_by_entity(entity.entity_id, evidence_type=EvidenceType.REVIEW)
    assert len(reviews) == 1
    assert reviews[0].evidence_id == ev_review.evidence_id

    pain_points = await repo.list_by_entity(entity.entity_id, evidence_type=EvidenceType.PAIN_POINT)
    assert len(pain_points) == 1
    assert pain_points[0].evidence_id == ev_pain.evidence_id


async def test_evidence_upsert_theme_creates_new(db: Path) -> None:
    """EvidenceRepo.upsert_theme creates a new theme when none exists."""
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    entity_repo = EntityRepo(db)
    entity = make_entity(run.run_id)
    await entity_repo.create(entity)

    repo = EvidenceRepo(db)
    theme = make_theme(entity.entity_id, label="battery life")
    result = await repo.upsert_theme(theme)

    themes = await repo.list_themes_by_entity(entity.entity_id)
    assert len(themes) == 1
    assert themes[0].theme_label == "battery life"
    assert themes[0].frequency == 1


async def test_evidence_upsert_theme_increments_frequency(db: Path) -> None:
    """EvidenceRepo.upsert_theme increments frequency when entity+label already exists."""
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    entity_repo = EntityRepo(db)
    entity = make_entity(run.run_id)
    await entity_repo.create(entity)

    repo = EvidenceRepo(db)
    # First upsert
    t1 = make_theme(entity.entity_id, label="durability", sample_evidence_ids=["ev1"])
    await repo.upsert_theme(t1)

    # Second upsert with same entity+label
    t2 = make_theme(entity.entity_id, label="durability", sample_evidence_ids=["ev2"])
    result = await repo.upsert_theme(t2)

    themes = await repo.list_themes_by_entity(entity.entity_id)
    assert len(themes) == 1
    assert themes[0].frequency == 2


# ---------------------------------------------------------------------------
# EntityRepo tests
# ---------------------------------------------------------------------------


async def test_entity_create_and_get(db: Path) -> None:
    """EntityRepo.create then get returns entity."""
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = EntityRepo(db)
    entity = make_entity(run.run_id, name="Logitech MX Keys")
    await repo.create(entity)

    fetched = await repo.get(entity.entity_id)
    assert fetched is not None
    assert fetched.entity_id == entity.entity_id
    assert fetched.canonical_name == "Logitech MX Keys"
    assert fetched.entity_type == EntityType.PRODUCT


async def test_entity_find_by_name(db: Path) -> None:
    """EntityRepo.find_by_name returns correct entity."""
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = EntityRepo(db)
    entity = make_entity(run.run_id, name="Keychron K2")
    await repo.create(entity)

    found = await repo.find_by_name("Keychron K2", run.run_id)
    assert found is not None
    assert found.entity_id == entity.entity_id

    not_found = await repo.find_by_name("Nonexistent Product", run.run_id)
    assert not_found is None


async def test_entity_add_listing_and_list_listings(db: Path) -> None:
    """EntityRepo.add_listing then list_listings returns the listing."""
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    entity_repo = EntityRepo(db)
    entity = make_entity(run.run_id)
    await entity_repo.create(entity)

    listing = EntityListing(
        listing_id=ulid.new().str,
        entity_id=entity.entity_id,
        platform="shopee",
        url="https://shopee.vn/keyboard",
        title="Mechanical Keyboard",
        price=1500000.0,
        currency="VND",
        captured_at=datetime.now(UTC),
    )
    await entity_repo.add_listing(listing)

    listings = await entity_repo.list_listings(entity.entity_id)
    assert len(listings) == 1
    assert listings[0].listing_id == listing.listing_id
    assert listings[0].platform == "shopee"
    assert listings[0].price == pytest.approx(1500000.0)


async def test_entity_add_relation_and_list_relations(db: Path) -> None:
    """EntityRepo.add_relation then list_relations returns from either side."""
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    entity_repo = EntityRepo(db)
    entity_a = make_entity(run.run_id, name="Product A")
    entity_b = make_entity(run.run_id, name="Product B")
    await entity_repo.create(entity_a)
    await entity_repo.create(entity_b)

    relation = EntityRelation(
        relation_id=ulid.new().str,
        entity_id_a=entity_a.entity_id,
        entity_id_b=entity_b.entity_id,
        relation_type=IdentityConfidence.PROBABLY_SAME,
        confidence=0.85,
        created_at=datetime.now(UTC),
    )
    await entity_repo.add_relation(relation)

    # Query from entity_a's side
    relations_a = await entity_repo.list_relations(entity_a.entity_id)
    assert len(relations_a) == 1
    assert relations_a[0].relation_id == relation.relation_id

    # Query from entity_b's side
    relations_b = await entity_repo.list_relations(entity_b.entity_id)
    assert len(relations_b) == 1
    assert relations_b[0].relation_id == relation.relation_id


# ---------------------------------------------------------------------------
# CheckpointRepo tests
# ---------------------------------------------------------------------------


async def test_checkpoint_save_and_get_latest(db: Path) -> None:
    """CheckpointRepo.save then get_latest returns it for the run."""
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = CheckpointRepo(db)
    ws = make_world_state(run.run_id)
    cp = make_checkpoint(run.run_id, ws)
    await repo.save(cp)

    latest = await repo.get_latest(run.run_id)
    assert latest is not None
    assert latest.checkpoint_id == cp.checkpoint_id
    assert latest.trigger == CheckpointTrigger.EVIDENCE_SAVED


async def test_checkpoint_get_latest_empty_returns_none(db: Path) -> None:
    """CheckpointRepo.get_latest on empty run returns None."""
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = CheckpointRepo(db)
    result = await repo.get_latest(run.run_id)
    assert result is None


async def test_checkpoint_world_state_roundtrip(db: Path) -> None:
    """Checkpoint WorldState round-trips correctly (serialize -> store -> load -> same values)."""
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    ws = WorldState(
        run_id=run.run_id,
        platform="tiktok",
        app="TikTok",
        page_type=PageType.SOCIAL_FEED,
        current_objective="Find trending keyboard reviews",
        navigation_history=["https://tiktok.com", "https://tiktok.com/keyboards"],
        confidence=Confidence.UNCERTAIN,
        agent_status=AgentStatus.LOW_YIELD,
        current_entity_id="entity-abc",
        scroll_position=250.5,
        updated_at=datetime.now(UTC),
    )

    cp = make_checkpoint(run.run_id, ws)
    repo = CheckpointRepo(db)
    await repo.save(cp)

    loaded = await repo.get(cp.checkpoint_id)
    assert loaded is not None
    lws = loaded.world_state

    assert lws.run_id == ws.run_id
    assert lws.platform == ws.platform
    assert lws.app == ws.app
    assert lws.page_type == PageType.SOCIAL_FEED
    assert lws.confidence == Confidence.UNCERTAIN
    assert lws.agent_status == AgentStatus.LOW_YIELD
    assert lws.current_entity_id == "entity-abc"
    assert lws.scroll_position == pytest.approx(250.5)
    assert lws.current_objective == "Find trending keyboard reviews"
    assert lws.navigation_history == ["https://tiktok.com", "https://tiktok.com/keyboards"]


# ---------------------------------------------------------------------------
# EventRepo tests
# ---------------------------------------------------------------------------


async def test_event_append_and_list_by_run(db: Path) -> None:
    """EventRepo.append then list_by_run returns events in order."""
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = EventRepo(db)
    ev1 = make_event(run.run_id, event_type=EventType.SEARCH)
    ev2 = make_event(run.run_id, event_type=EventType.NAVIGATE)
    ev3 = make_event(run.run_id, event_type=EventType.CLICK)

    await repo.append(ev1)
    await repo.append(ev2)
    await repo.append(ev3)

    events = await repo.list_by_run(run.run_id)
    assert len(events) == 3
    # Events should be returned in insertion/occurred_at order
    event_ids = [e.event_id for e in events]
    assert ev1.event_id in event_ids
    assert ev2.event_id in event_ids
    assert ev3.event_id in event_ids


async def test_event_get_recent_returns_n_most_recent(db: Path) -> None:
    """EventRepo.get_recent returns N most recent events."""
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = EventRepo(db)
    events = []
    for i in range(5):
        ev = make_event(run.run_id)
        await repo.append(ev)
        events.append(ev)

    recent = await repo.get_recent(run.run_id, n=3)
    assert len(recent) == 3
    # Most recent first (DESC order)
    recent_ids = [e.event_id for e in recent]
    # Last 3 appended should be among recent
    assert events[-1].event_id in recent_ids
    assert events[-2].event_id in recent_ids
    assert events[-3].event_id in recent_ids
