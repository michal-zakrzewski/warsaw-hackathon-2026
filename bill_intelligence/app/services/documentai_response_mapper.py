"""Maps a raw google.cloud.documentai Document to BillExtractionResult."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    pass

from app.domain.bill_intelligence_models import BillEntity, BillExtractionResult


def map_document_ai_response(
    doc_result,  # google.cloud.documentai.Document
    document_id: str,
    processor_id: str,
    processor_type: Literal["utility", "form", "custom", "unknown"],
    include_raw: bool = False,
) -> BillExtractionResult:
    """Convert a Document AI Document proto to a BillExtractionResult.

    Handles both typed entities (Utility Parser) and form key-value pairs
    (Form Parser).  Form fields from pages[].form_fields are always merged
    in — they act as a catch-all for fields the entity extractor missed.
    """
    entities = _map_entities(doc_result)
    entities += _map_form_fields(doc_result)  # Form Parser key-value pairs
    tables = _map_tables(doc_result)
    confidence = _overall_confidence(entities, doc_result)

    raw_document: dict | None = None
    if include_raw:
        raw_document = _proto_to_dict(doc_result)

    warnings: list[str] = []
    if not entities:
        warnings.append("No entities extracted — document may be unstructured or unsupported")
    if confidence < 0.5:
        warnings.append(f"Low overall extraction confidence: {confidence:.2f}")

    return BillExtractionResult(
        document_id=document_id,
        processor_used=processor_id,
        processor_type=processor_type,
        success=True,
        entities=entities,
        text=getattr(doc_result, "text", None),
        tables=tables,
        confidence=confidence,
        warnings=warnings,
        raw_document=raw_document,
    )


def _map_entities(doc_result) -> list[BillEntity]:
    entities: list[BillEntity] = []
    for entity in getattr(doc_result, "entities", []):
        normalized_text = _extract_normalized_value(entity)
        page_refs = _extract_page_refs(entity)
        entities.append(
            BillEntity(
                type=entity.type_,
                mention_text=entity.mention_text or None,
                normalized_value=normalized_text,
                confidence=entity.confidence if entity.confidence else None,
                page_refs=page_refs,
                raw={"type": entity.type_, "mention_text": entity.mention_text},
            )
        )
        # Recurse into nested properties (e.g. line_item sub-entities)
        for prop in getattr(entity, "properties", []):
            prop_normalized = _extract_normalized_value(prop)
            entities.append(
                BillEntity(
                    type=prop.type_,
                    mention_text=prop.mention_text or None,
                    normalized_value=prop_normalized,
                    confidence=prop.confidence if prop.confidence else None,
                    page_refs=_extract_page_refs(prop),
                    raw={"type": prop.type_, "mention_text": prop.mention_text},
                )
            )
    return entities


def _extract_normalized_value(entity) -> str | None:
    nv = getattr(entity, "normalized_value", None)
    if nv is None:
        return None
    # Try text first
    if getattr(nv, "text", None):
        return nv.text
    # Date value
    dv = getattr(nv, "date_value", None)
    if dv and getattr(dv, "year", None):
        return f"{dv.year:04d}-{dv.month:02d}-{dv.day:02d}"
    # Float value
    fv = getattr(nv, "float_value", None)
    if fv is not None:
        return str(fv)
    # Money value
    mv = getattr(nv, "money_value", None)
    if mv is not None:
        units = getattr(mv, "units", 0)
        nanos = getattr(mv, "nanos", 0)
        amount = units + nanos / 1_000_000_000
        return str(round(amount, 4))
    return None


def _extract_page_refs(entity) -> list[int]:
    try:
        anchor = entity.page_anchor
        return [int(ref.page) for ref in anchor.page_refs]
    except Exception:
        return []


def _map_form_fields(doc_result) -> list[BillEntity]:
    """Extract Form Parser key-value pairs from pages[].form_fields.

    Each form field key becomes the entity type; the value becomes
    mention_text / normalized_value.  This is the primary extraction path
    for the Form Parser processor.
    """
    entities: list[BillEntity] = []
    full_text: str = getattr(doc_result, "text", "") or ""
    for page in getattr(doc_result, "pages", []):
        for field in getattr(page, "form_fields", []):
            key_text = _layout_text(getattr(field, "field_name", None), full_text).strip(" :")
            val_text = _layout_text(getattr(field, "field_value", None), full_text).strip()
            if not key_text or not val_text:
                continue
            confidence = None
            fv = getattr(field, "field_value", None)
            if fv is not None:
                raw_conf = getattr(fv, "confidence", None)
                if raw_conf is not None:
                    confidence = float(raw_conf)
            entities.append(
                BillEntity(
                    type=key_text.lower(),
                    mention_text=val_text,
                    normalized_value=val_text,
                    confidence=confidence,
                    raw={"key": key_text, "value": val_text},
                )
            )
    return entities


def _map_tables(doc_result) -> list[dict]:
    tables: list[dict] = []
    for page in getattr(doc_result, "pages", []):
        for table in getattr(page, "tables", []):
            header_rows = _extract_table_rows(table.header_rows, doc_result.text)
            body_rows = _extract_table_rows(table.body_rows, doc_result.text)
            tables.append({"header_rows": header_rows, "body_rows": body_rows})
    return tables


def _extract_table_rows(rows, full_text: str) -> list[list[str]]:
    result: list[list[str]] = []
    for row in rows:
        cells: list[str] = []
        for cell in row.cells:
            text = _layout_text(cell.layout, full_text)
            cells.append(text)
        result.append(cells)
    return result


def _layout_text(layout, full_text: str) -> str:
    try:
        segments: list[str] = []
        for seg in layout.text_anchor.text_segments:
            start = int(seg.start_index)
            end = int(seg.end_index)
            segments.append(full_text[start:end])
        return "".join(segments).strip()
    except Exception:
        return ""


def _overall_confidence(entities: list[BillEntity], doc_result) -> float:
    if not entities:
        return 0.0
    confidences = [e.confidence for e in entities if e.confidence is not None]
    if not confidences:
        return 0.5
    return round(sum(confidences) / len(confidences), 4)


def _proto_to_dict(doc_result) -> dict:
    try:
        from google.protobuf.json_format import MessageToDict  # type: ignore[import]
        return MessageToDict(doc_result._pb)
    except Exception:
        return {}
