from __future__ import annotations

from app.domain.vision_models import (
    AggregatedVisionResult,
    ConditionFlags,
    ImageInput,
    PerImageVisionResult,
    Ternary,
)

_REQUIRED_VIEWS = {"front", "side", "roof_oblique"}
_ROOF_VIEWS = {"roof_oblique", "rear"}
_KEY_CONFIDENCE_THRESHOLD = 0.65


def aggregate_results(
    results: list[PerImageVisionResult],
    images: list[ImageInput],
) -> AggregatedVisionResult:
    """Merge per-image analysis results into a single building-level assessment.

    Selection strategy:
    - Enum fields: majority-vote weighted by confidence; "unknown" is only
      chosen when no better value exists across any image.
    - Ternary fields: "yes" wins over "no" which wins over "uncertain".
    - Conflicts between non-unknown values are surfaced as quality warnings.
    - needs_more_images is set when coverage, quality, or confidence is lacking.
    """
    if not results:
        raise ValueError("Cannot aggregate an empty results list")

    image_by_id = {img.image_id: img for img in images}
    present_view_types = {img.view_type for img in images}
    missing_views = sorted(_REQUIRED_VIEWS - present_view_types)

    usable = _usable_results(results)
    quality_warnings = _collect_quality_warnings(results, usable)

    wall_finish, wall_finish_conflict = _best_enum(
        [(r.wall_finish_material, r.confidence) for r in usable]
    )
    wall_structure, wall_structure_conflict = _best_enum(
        [(r.wall_structure_guess, r.confidence) for r in usable]
    )
    roof_covering, roof_covering_conflict = _best_enum(
        [(r.roof_covering_material, r.confidence) for r in usable]
    )
    roof_type_val, roof_type_conflict = _best_enum(
        [(r.roof_type, r.confidence) for r in usable]
    )
    window_type, window_type_conflict = _best_enum(
        [(r.window_type_guess, r.confidence) for r in usable]
    )

    for field_name, has_conflict, values in [
        ("wall_finish_material", wall_finish_conflict, [r.wall_finish_material for r in usable]),
        ("wall_structure_guess", wall_structure_conflict, [r.wall_structure_guess for r in usable]),
        ("roof_covering_material", roof_covering_conflict, [r.roof_covering_material for r in usable]),
        ("roof_type", roof_type_conflict, [r.roof_type for r in usable]),
        ("window_type_guess", window_type_conflict, [r.window_type_guess for r in usable]),
    ]:
        if has_conflict:
            unique = sorted({v for v in values if v != "unknown"})
            quality_warnings.append(
                f"Conflicting observations for {field_name}: {', '.join(unique)}"
            )

    insulation = _aggregate_ternary([r.visible_insulation_signs for r in usable])

    condition_flags = ConditionFlags(
        cracks_visible=_aggregate_ternary(
            [r.condition_flags.cracks_visible for r in usable]
        ),
        moisture_stains_visible=_aggregate_ternary(
            [r.condition_flags.moisture_stains_visible for r in usable]
        ),
        facade_degradation_visible=_aggregate_ternary(
            [r.condition_flags.facade_degradation_visible for r in usable]
        ),
        roof_damage_visible=_aggregate_ternary(
            [r.condition_flags.roof_damage_visible for r in usable]
        ),
        thermal_bridge_risk_visible=_aggregate_ternary(
            [r.condition_flags.thermal_bridge_risk_visible for r in usable]
        ),
    )

    overall_confidence = round(
        sum(r.confidence for r in usable) / len(usable), 4
    )

    evidence = _deduplicated_evidence(usable)

    has_roof_view = bool(present_view_types & _ROOF_VIEWS) or any(
        not r.image_quality_flags.roof_not_visible for r in results
    )
    majority_poor_quality = len(usable) < len(results)

    assumption_notes: list[str] = []
    if wall_finish == "unknown":
        assumption_notes.append(
            "Wall finish material could not be determined from available images"
        )
    if roof_type_val == "unknown":
        assumption_notes.append(
            "Roof type could not be determined from available images"
        )

    needs_more_images = (
        not has_roof_view
        or majority_poor_quality
        or overall_confidence < _KEY_CONFIDENCE_THRESHOLD
        or bool(missing_views)
    )

    return AggregatedVisionResult(
        wall_finish_material=wall_finish,  # type: ignore[arg-type]
        wall_structure_guess=wall_structure,  # type: ignore[arg-type]
        roof_covering_material=roof_covering,  # type: ignore[arg-type]
        roof_type=roof_type_val,  # type: ignore[arg-type]
        window_type_guess=window_type,  # type: ignore[arg-type]
        visible_insulation_signs=insulation,
        condition_flags=condition_flags,
        overall_confidence=overall_confidence,
        evidence=evidence,
        needs_more_images=needs_more_images,
        missing_views=missing_views,
        quality_warnings=quality_warnings,
        assumption_notes=assumption_notes,
    )


def _usable_results(results: list[PerImageVisionResult]) -> list[PerImageVisionResult]:
    """Return results from images that are not poor quality.

    Falls back to all results if every image is poor quality, so the
    aggregation always has something to work with.
    """
    good = [
        r
        for r in results
        if not (
            r.image_quality_flags.blurry
            or r.image_quality_flags.low_light
            or r.image_quality_flags.insufficient_detail
        )
    ]
    return good if good else results


def _collect_quality_warnings(
    all_results: list[PerImageVisionResult],
    usable: list[PerImageVisionResult],
) -> list[str]:
    warnings: list[str] = []
    if len(usable) < len(all_results):
        warnings.append(
            f"{len(all_results) - len(usable)} of {len(all_results)} images "
            "excluded due to poor quality (blurry / low-light / insufficient detail)"
        )
    for r in all_results:
        if r.image_quality_flags.occluded:
            warnings.append(f"Image {r.image_id!r} is partially occluded")
    return warnings


def _best_enum(
    values_with_confidence: list[tuple[str, float]],
    fallback: str = "unknown",
) -> tuple[str, bool]:
    """Return (winner, has_conflict).

    winner    — the value with the highest confidence-weighted vote count,
                preferring non-unknown values when available.
    has_conflict — True when at least two distinct non-unknown values appear.
    """
    non_unknown = [
        (v, c) for v, c in values_with_confidence if v != fallback
    ]
    pool = non_unknown if non_unknown else values_with_confidence

    if not pool:
        return fallback, False

    scores: dict[str, float] = {}
    for v, c in pool:
        scores[v] = scores.get(v, 0.0) + c

    winner = max(scores, key=lambda k: scores[k])
    has_conflict = len({v for v, _ in non_unknown}) > 1
    return winner, has_conflict


def _aggregate_ternary(values: list[Ternary]) -> Ternary:
    if "yes" in values:
        return "yes"
    definite = [v for v in values if v != "uncertain"]
    if definite and all(v == "no" for v in definite):
        return "no"
    return "uncertain"


def _deduplicated_evidence(results: list[PerImageVisionResult]) -> list[str]:
    seen: set[str] = set()
    evidence: list[str] = []
    for r in results:
        for item in r.evidence:
            if item not in seen:
                evidence.append(item)
                seen.add(item)
    return evidence
