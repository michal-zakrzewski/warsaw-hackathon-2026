from __future__ import annotations

import pytest

from app.domain.vision_models import (
    AggregatedVisionResult,
    ConditionFlags,
    ImageInput,
    ImageQualityFlags,
    PerImageVisionResult,
)
from app.services.vision_aggregator import aggregate_results


# ---------------------------------------------------------------------------
# Fixtures / builders
# ---------------------------------------------------------------------------


def _good_flags(*, roof_not_visible: bool = False, facade_not_visible: bool = False) -> ImageQualityFlags:
    return ImageQualityFlags(
        blurry=False,
        low_light=False,
        occluded=False,
        roof_not_visible=roof_not_visible,
        facade_not_visible=facade_not_visible,
        insufficient_detail=False,
    )


def _poor_flags() -> ImageQualityFlags:
    return ImageQualityFlags(
        blurry=True,
        low_light=False,
        occluded=False,
        roof_not_visible=True,
        facade_not_visible=True,
        insufficient_detail=False,
    )


def _neutral_conditions() -> ConditionFlags:
    return ConditionFlags(
        cracks_visible="no",
        moisture_stains_visible="no",
        facade_degradation_visible="no",
        roof_damage_visible="no",
        thermal_bridge_risk_visible="uncertain",
    )


def _make_result(
    image_id: str,
    *,
    wall_finish: str = "plaster",
    wall_structure: str = "brick",
    roof_covering: str = "ceramic_tile",
    roof_type: str = "gable",
    window_type: str = "double_glazed",
    confidence: float = 0.80,
    quality_flags: ImageQualityFlags | None = None,
    conditions: ConditionFlags | None = None,
    evidence: list[str] | None = None,
    missing: list[str] | None = None,
) -> PerImageVisionResult:
    return PerImageVisionResult(
        image_id=image_id,
        wall_finish_material=wall_finish,  # type: ignore[arg-type]
        wall_structure_guess=wall_structure,  # type: ignore[arg-type]
        roof_covering_material=roof_covering,  # type: ignore[arg-type]
        roof_type=roof_type,  # type: ignore[arg-type]
        window_type_guess=window_type,  # type: ignore[arg-type]
        visible_insulation_signs="uncertain",
        condition_flags=conditions or _neutral_conditions(),
        image_quality_flags=quality_flags or _good_flags(),
        confidence=confidence,
        evidence=evidence or ["Plaster facade observed", "Brick reveals visible"],
        missing_information=missing or [],
    )


def _make_image(image_id: str, view_type: str = "front") -> ImageInput:
    return ImageInput(
        image_id=image_id,
        source_type="upload",
        storage_path=f"/uploads/{image_id}.jpg",
        view_type=view_type,  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
# Empty input guard
# ---------------------------------------------------------------------------


class TestAggregateGuards:
    def test_empty_results_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            aggregate_results([], [])


# ---------------------------------------------------------------------------
# Consistent results
# ---------------------------------------------------------------------------


class TestConsistentAggregation:
    def test_consistent_results_pick_correct_values(self) -> None:
        results = [
            _make_result("img-1", wall_finish="plaster", roof_type="gable", confidence=0.80),
            _make_result("img-2", wall_finish="plaster", roof_type="gable", confidence=0.85),
        ]
        images = [_make_image("img-1", "front"), _make_image("img-2", "roof_oblique")]
        agg = aggregate_results(results, images)

        assert agg.wall_finish_material == "plaster"
        assert agg.roof_type == "gable"

    def test_no_conflict_warnings_when_consistent(self) -> None:
        results = [
            _make_result("img-1", wall_finish="brick_face", confidence=0.75),
            _make_result("img-2", wall_finish="brick_face", confidence=0.80),
        ]
        images = [_make_image("img-1", "front"), _make_image("img-2", "side")]
        agg = aggregate_results(results, images)

        conflict_warnings = [w for w in agg.quality_warnings if "Conflicting" in w]
        assert conflict_warnings == []

    def test_confidence_is_averaged(self) -> None:
        results = [
            _make_result("img-1", confidence=0.80),
            _make_result("img-2", confidence=0.90),
        ]
        images = [_make_image("img-1", "front"), _make_image("img-2", "roof_oblique")]
        agg = aggregate_results(results, images)

        assert abs(agg.overall_confidence - 0.85) < 0.001

    def test_evidence_is_deduplicated(self) -> None:
        shared_evidence = "Plaster facade observed"
        results = [
            _make_result("img-1", evidence=[shared_evidence, "Detail A"]),
            _make_result("img-2", evidence=[shared_evidence, "Detail B"]),
        ]
        images = [_make_image("img-1", "front"), _make_image("img-2", "side")]
        agg = aggregate_results(results, images)

        assert agg.evidence.count(shared_evidence) == 1
        assert "Detail A" in agg.evidence
        assert "Detail B" in agg.evidence


# ---------------------------------------------------------------------------
# Conflicting results
# ---------------------------------------------------------------------------


class TestConflictingAggregation:
    def test_conflict_produces_warning(self) -> None:
        results = [
            _make_result("img-1", wall_finish="plaster", confidence=0.70),
            _make_result("img-2", wall_finish="brick_face", confidence=0.75),
        ]
        images = [_make_image("img-1", "front"), _make_image("img-2", "side")]
        agg = aggregate_results(results, images)

        conflict_warnings = [w for w in agg.quality_warnings if "wall_finish_material" in w]
        assert conflict_warnings, "Expected a conflict warning for wall_finish_material"

    def test_higher_confidence_wins_on_conflict(self) -> None:
        results = [
            _make_result("img-1", wall_finish="plaster", confidence=0.60),
            _make_result("img-2", wall_finish="concrete", confidence=0.90),
        ]
        images = [_make_image("img-1", "front"), _make_image("img-2", "side")]
        agg = aggregate_results(results, images)

        assert agg.wall_finish_material == "concrete"

    def test_unknown_does_not_count_as_conflict(self) -> None:
        results = [
            _make_result("img-1", roof_type="gable", quality_flags=_good_flags(roof_not_visible=True)),
            _make_result("img-2", roof_type="gable", quality_flags=_good_flags(roof_not_visible=False)),
        ]
        images = [_make_image("img-1", "front"), _make_image("img-2", "roof_oblique")]
        agg = aggregate_results(results, images)

        conflict_warnings = [w for w in agg.quality_warnings if "roof_type" in w]
        assert conflict_warnings == []


# ---------------------------------------------------------------------------
# Missing views
# ---------------------------------------------------------------------------


class TestMissingViews:
    def test_all_required_views_present(self) -> None:
        results = [
            _make_result("img-1"),
            _make_result("img-2"),
            _make_result("img-3"),
        ]
        images = [
            _make_image("img-1", "front"),
            _make_image("img-2", "side"),
            _make_image("img-3", "roof_oblique"),
        ]
        agg = aggregate_results(results, images)
        assert agg.missing_views == []

    def test_missing_roof_oblique_is_detected(self) -> None:
        results = [_make_result("img-1"), _make_result("img-2")]
        images = [_make_image("img-1", "front"), _make_image("img-2", "side")]
        agg = aggregate_results(results, images)
        assert "roof_oblique" in agg.missing_views

    def test_missing_front_is_detected(self) -> None:
        results = [_make_result("img-1"), _make_result("img-2")]
        images = [_make_image("img-1", "side"), _make_image("img-2", "roof_oblique")]
        agg = aggregate_results(results, images)
        assert "front" in agg.missing_views

    def test_missing_side_is_detected(self) -> None:
        results = [_make_result("img-1"), _make_result("img-2")]
        images = [_make_image("img-1", "front"), _make_image("img-2", "roof_oblique")]
        agg = aggregate_results(results, images)
        assert "side" in agg.missing_views

    def test_missing_views_list_is_sorted(self) -> None:
        results = [_make_result("img-1")]
        images = [_make_image("img-1", "detail")]
        agg = aggregate_results(results, images)
        assert agg.missing_views == sorted(agg.missing_views)


# ---------------------------------------------------------------------------
# needs_more_images
# ---------------------------------------------------------------------------


class TestNeedsMoreImages:
    def test_no_roof_view_triggers_flag(self) -> None:
        results = [_make_result("img-1", confidence=0.90)]
        images = [_make_image("img-1", "front")]
        agg = aggregate_results(results, images)
        assert agg.needs_more_images is True

    def test_majority_poor_quality_triggers_flag(self) -> None:
        results = [
            _make_result("img-1", quality_flags=_poor_flags()),
            _make_result("img-2", quality_flags=_poor_flags()),
            _make_result("img-3", quality_flags=_good_flags()),
        ]
        images = [
            _make_image("img-1", "front"),
            _make_image("img-2", "side"),
            _make_image("img-3", "roof_oblique"),
        ]
        agg = aggregate_results(results, images)
        assert agg.needs_more_images is True

    def test_low_overall_confidence_triggers_flag(self) -> None:
        results = [
            _make_result("img-1", confidence=0.50),
            _make_result("img-2", confidence=0.55),
        ]
        images = [_make_image("img-1", "front"), _make_image("img-2", "side")]
        agg = aggregate_results(results, images)
        assert agg.needs_more_images is True

    def test_complete_high_quality_set_clears_flag(self) -> None:
        results = [
            _make_result("img-1", confidence=0.85),
            _make_result("img-2", confidence=0.80),
            _make_result("img-3", confidence=0.90),
        ]
        images = [
            _make_image("img-1", "front"),
            _make_image("img-2", "side"),
            _make_image("img-3", "roof_oblique"),
        ]
        agg = aggregate_results(results, images)
        assert agg.needs_more_images is False

    def test_missing_views_list_triggers_flag(self) -> None:
        results = [_make_result("img-1", confidence=0.90)]
        images = [_make_image("img-1", "detail")]
        agg = aggregate_results(results, images)
        assert agg.needs_more_images is True


# ---------------------------------------------------------------------------
# ConditionFlags aggregation
# ---------------------------------------------------------------------------


class TestConditionFlagsAggregation:
    def test_yes_dominates_no_and_uncertain(self) -> None:
        cond_yes = ConditionFlags(
            cracks_visible="yes",
            moisture_stains_visible="no",
            facade_degradation_visible="uncertain",
            roof_damage_visible="no",
            thermal_bridge_risk_visible="uncertain",
        )
        cond_no = ConditionFlags(
            cracks_visible="no",
            moisture_stains_visible="no",
            facade_degradation_visible="no",
            roof_damage_visible="no",
            thermal_bridge_risk_visible="no",
        )
        results = [
            _make_result("img-1", conditions=cond_yes),
            _make_result("img-2", conditions=cond_no),
        ]
        images = [_make_image("img-1", "front"), _make_image("img-2", "side")]
        agg = aggregate_results(results, images)

        assert agg.condition_flags.cracks_visible == "yes"
        assert agg.condition_flags.moisture_stains_visible == "no"

    def test_all_uncertain_stays_uncertain(self) -> None:
        cond = ConditionFlags(
            cracks_visible="uncertain",
            moisture_stains_visible="uncertain",
            facade_degradation_visible="uncertain",
            roof_damage_visible="uncertain",
            thermal_bridge_risk_visible="uncertain",
        )
        results = [_make_result("img-1", conditions=cond)]
        images = [_make_image("img-1", "front")]
        agg = aggregate_results(results, images)

        assert agg.condition_flags.cracks_visible == "uncertain"
