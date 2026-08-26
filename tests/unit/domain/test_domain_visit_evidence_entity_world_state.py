"""Unit tests for domain models: VisitRecord, Evidence, Entity, WorldState, CheckpointData, ActionEvent, UserProfile, and associated enums."""

from datetime import UTC, datetime

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
    UserProfile,
    VisitRecord,
    WorldState,
)


def test_visit_record_defaults():
    visit = VisitRecord(visit_id="vis-1", run_id="run-1", platform="shopee")

    assert visit.visit_id == "vis-1"
    assert visit.run_id == "run-1"
    assert visit.platform == "shopee"
    assert visit.url is None
    assert visit.entity_id is None
    assert visit.content_fingerprint is None
    assert visit.screen_fingerprint is None
    assert visit.revisit_count == 0
    assert visit.last_revisit_reason is None
    assert visit.last_revisit_sought is None
    assert isinstance(visit.visited_at, datetime)
    assert visit.visited_at.tzinfo == UTC


def test_evidence_type_twelve_members():
    expected = {
        "NEGATIVE_COMMENT",
        "POSITIVE_COMMENT",
        "REVIEW",
        "RECOMMENDATION",
        "PRODUCT_CLAIM",
        "SOCIAL_POST",
        "SPECIFICATION",
        "PRICE_OBSERVATION",
        "DURABILITY_CLAIM",
        "PAIN_POINT",
        "RELATED_PRODUCT",
        "RELATED_CATEGORY",
    }
    actual = {e.value for e in EvidenceType}
    assert actual == expected
    assert len(EvidenceType) == 12


def test_evidence_direct_url_none_valid():
    evidence = Evidence(
        evidence_id="evi-1",
        run_id="run-1",
        evidence_type=EvidenceType.POSITIVE_COMMENT,
        source_platform="youtube",
        raw_text="Great lumbar support for long sessions",
        source_url="https://youtube.com/watch?v=123",
        direct_url=None,
    )

    assert evidence.evidence_id == "evi-1"
    assert evidence.run_id == "run-1"
    assert evidence.evidence_type == EvidenceType.POSITIVE_COMMENT
    assert evidence.source_platform == "youtube"
    assert evidence.raw_text == "Great lumbar support for long sessions"
    assert evidence.source_url == "https://youtube.com/watch?v=123"
    assert evidence.direct_url is None
    assert evidence.parent_url is None
    assert evidence.entity_id is None
    assert evidence.screenshot_path is None
    assert evidence.confidence is None
    assert evidence.provenance is None
    assert isinstance(evidence.captured_at, datetime)
    assert evidence.captured_at.tzinfo == UTC


def test_evidence_theme_defaults():
    theme = EvidenceTheme(
        theme_id="theme-1",
        entity_id="ent-1",
        theme_label="Mesh tearing after 6 months",
    )

    assert theme.theme_id == "theme-1"
    assert theme.entity_id == "ent-1"
    assert theme.theme_label == "Mesh tearing after 6 months"
    assert theme.frequency == 1
    assert theme.sample_evidence_ids == []
    assert isinstance(theme.updated_at, datetime)
    assert theme.updated_at.tzinfo == UTC


def test_entity_type_seven_members():
    expected = {
        "PRODUCT",
        "POST",
        "CATEGORY",
        "KEYWORD",
        "VIDEO",
        "CHANNEL",
        "PAGE",
    }
    actual = {t.value for t in EntityType}
    assert actual == expected
    assert len(EntityType) == 7


def test_entity_defaults_and_identity_confidence():
    entity = Entity(
        entity_id="ent-1",
        run_id="run-1",
        entity_type=EntityType.PRODUCT,
        canonical_name="Sihoo M57 Ergonomic Chair",
    )

    assert entity.entity_id == "ent-1"
    assert entity.run_id == "run-1"
    assert entity.entity_type == EntityType.PRODUCT
    assert entity.canonical_name == "Sihoo M57 Ergonomic Chair"
    assert entity.brand is None
    assert entity.model is None
    assert entity.identity_confidence == IdentityConfidence.UNKNOWN
    assert entity.user_profile_match is None
    assert entity.provenance is None
    assert isinstance(entity.created_at, datetime)
    assert entity.created_at.tzinfo == UTC
    assert isinstance(entity.updated_at, datetime)
    assert entity.updated_at.tzinfo == UTC


def test_entity_listing_and_relation_instantiation():
    listing = EntityListing(
        listing_id="list-1",
        entity_id="ent-1",
        platform="shopee",
        url="https://shopee.vn/product/123",
        title="Ghe cong thai hoc Sihoo M57",
        price=3500000.0,
        currency="VND",
        metadata={"seller": "Official Store"},
    )
    assert listing.listing_id == "list-1"
    assert listing.entity_id == "ent-1"
    assert listing.platform == "shopee"
    assert listing.url == "https://shopee.vn/product/123"
    assert listing.title == "Ghe cong thai hoc Sihoo M57"
    assert listing.price == 3500000.0
    assert listing.currency == "VND"
    assert listing.metadata == {"seller": "Official Store"}
    assert isinstance(listing.captured_at, datetime)
    assert listing.captured_at.tzinfo == UTC

    relation = EntityRelation(
        relation_id="rel-1",
        entity_id_a="ent-1",
        entity_id_b="ent-2",
        relation_type=IdentityConfidence.SAME,
        confidence=0.95,
    )
    assert relation.relation_id == "rel-1"
    assert relation.entity_id_a == "ent-1"
    assert relation.entity_id_b == "ent-2"
    assert relation.relation_type == IdentityConfidence.SAME
    assert relation.confidence == 0.95
    assert isinstance(relation.created_at, datetime)
    assert relation.created_at.tzinfo == UTC


def test_page_type_captcha_and_all_members():
    assert PageType.CAPTCHA == "CAPTCHA"
    assert PageType.CAPTCHA in PageType
    expected = {
        "UNKNOWN",
        "SEARCH_RESULT",
        "PRODUCT_PAGE",
        "REVIEW_SECTION",
        "COMMENT_SECTION",
        "SOCIAL_POST",
        "SOCIAL_FEED",
        "VIDEO_PAGE",
        "CATEGORY_PAGE",
        "LOGIN_PAGE",
        "CAPTCHA",
        "ERROR_PAGE",
        "NAVIGATION",
    }
    actual = {p.value for p in PageType}
    assert actual == expected
    assert len(PageType) == 13


def test_world_state_defaults():
    ws = WorldState(
        run_id="run-1",
        platform="tiktok",
        app="browser",
    )

    assert ws.run_id == "run-1"
    assert ws.platform == "tiktok"
    assert ws.app == "browser"
    assert ws.page_type == PageType.UNKNOWN
    assert ws.current_entity_id is None
    assert ws.current_seed_id is None
    assert ws.root_seed_id is None
    assert ws.current_branch_id is None
    assert ws.scroll_position is None
    assert ws.last_action_event_id is None
    assert ws.current_objective == ""
    assert isinstance(ws.navigation_history, list)
    assert ws.navigation_history == []
    assert ws.confidence == Confidence.UNKNOWN
    assert ws.agent_status == AgentStatus.NORMAL
    assert isinstance(ws.updated_at, datetime)
    assert ws.updated_at.tzinfo == UTC


def test_checkpoint_trigger_eight_members():
    expected = {
        "SEARCH_DONE",
        "PRODUCT_OPENED",
        "REVIEW_SECTION_ENTERED",
        "EVIDENCE_SAVED",
        "SEED_DISCOVERED",
        "FRONTIER_ITEM_SELECTED",
        "NAVIGATION_COMPLETED",
        "HUMAN_HANDOFF",
    }
    actual = {t.value for t in CheckpointTrigger}
    assert actual == expected
    assert len(CheckpointTrigger) == 8


def test_checkpoint_data_instantiation():
    ws = WorldState(run_id="run-1", platform="shopee", app="browser")
    checkpoint = CheckpointData(
        checkpoint_id="chk-1",
        run_id="run-1",
        world_state=ws,
        frontier_snapshot=[{"frontier_id": "f-1", "score": 0.8}],
        yield_snapshot={"window_start": 0, "new_candidates": 3, "new_evidence": 5},
    )

    assert checkpoint.checkpoint_id == "chk-1"
    assert checkpoint.run_id == "run-1"
    assert checkpoint.world_state == ws
    assert checkpoint.frontier_snapshot == [{"frontier_id": "f-1", "score": 0.8}]
    assert checkpoint.yield_snapshot == {"window_start": 0, "new_candidates": 3, "new_evidence": 5}
    assert checkpoint.trigger == CheckpointTrigger.EVIDENCE_SAVED
    assert isinstance(checkpoint.created_at, datetime)
    assert checkpoint.created_at.tzinfo == UTC


def test_action_event_defaults():
    event = ActionEvent(
        event_id="evt-1",
        run_id="run-1",
        event_type=EventType.SEARCH,
    )

    assert event.event_id == "evt-1"
    assert event.run_id == "run-1"
    assert event.event_type == EventType.SEARCH
    assert event.actor == EventActor.AGENT
    assert event.detail is None
    assert event.parent_event_id is None
    assert isinstance(event.occurred_at, datetime)
    assert event.occurred_at.tzinfo == UTC


def test_action_event_all_event_types():
    expected = {
        "SEARCH",
        "NAVIGATE",
        "CLICK",
        "SCROLL",
        "TYPE",
        "BACK",
        "SCREENSHOT",
        "SEED_DISCOVERED",
        "EVIDENCE_SAVED",
        "CHECKPOINT",
        "RECOVERY",
        "HUMAN_REQUIRED",
        "YIELD_LOW",
        "SATURATION",
        "RUN_START",
        "RUN_END",
    }
    actual = {e.value for e in EventType}
    assert actual == expected
    assert len(EventType) == 16


def test_user_profile_defaults():
    profile = UserProfile(profile_id="prof-1")

    assert profile.profile_id == "prof-1"
    assert profile.budget_anchor is None
    assert profile.budget_currency == "VND"
    assert profile.size_constraints is None
    assert profile.height_cm is None
    assert profile.usage_context is None
    assert isinstance(profile.preferences, list)
    assert profile.preferences == []
    assert isinstance(profile.dislikes, list)
    assert profile.dislikes == []
    assert isinstance(profile.pp_priorities, list)
    assert profile.pp_priorities == []


def test_all_enums_are_str_subclasses():
    enums_to_test = [
        EvidenceType,
        EntityType,
        IdentityConfidence,
        PageType,
        Confidence,
        AgentStatus,
        CheckpointTrigger,
        EventType,
        EventActor,
    ]
    for enum_cls in enums_to_test:
        for member in enum_cls:
            assert isinstance(member, str), f"{member} in {enum_cls} is not a str instance"
            assert isinstance(member.value, str), f"{member.value} in {enum_cls} is not str"
