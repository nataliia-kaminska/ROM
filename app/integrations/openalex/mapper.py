from typing import Any


def extract_openalex_profile(author: dict[str, Any], works: list[dict[str, Any]]) -> dict[str, Any]:
    author_id = author.get("id")
    author_concepts = _concept_records(author.get("x_concepts", []), source="author")
    sorted_works = sorted([work for work in works if isinstance(work, dict)], key=_work_sort_key, reverse=True)
    work_titles = [
        work.get("display_name") or work.get("title")
        for work in sorted_works
        if work.get("display_name") or work.get("title")
    ]
    work_concepts: list[dict[str, Any]] = []
    for work in sorted_works:
        work_concepts.extend(_concept_records(work.get("concepts", []), source="work"))
    concept_records = _deduplicate_concept_records([*author_concepts, *work_concepts])
    concepts = [record["name"] for record in concept_records]
    institutions = _institutions(author)
    return {
        "display_name": author.get("display_name") or "",
        "openalex_author_id": author_id,
        "concepts": concepts,
        "concept_records": concept_records,
        "institutions": institutions,
        "works": work_titles,
        "summary": _summary(author, concepts, work_titles, institutions),
    }


def _concept_records(values: object, source: str) -> list[dict[str, Any]]:
    if not isinstance(values, list):
        return []
    records: list[dict[str, Any]] = []
    for item in values:
        if not isinstance(item, dict) or not item.get("display_name"):
            continue
        records.append(
            {
                "name": str(item["display_name"]),
                "level": item.get("level"),
                "score": item.get("score"),
                "source": source,
            }
        )
    return records


def _work_sort_key(work: dict[str, Any]) -> tuple[int, str]:
    year = work.get("publication_year")
    date = work.get("publication_date")
    year_value = int(year) if isinstance(year, int) else 0
    return year_value, str(date or "")


def _deduplicate_concept_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_name: dict[str, dict[str, Any]] = {}
    for record in records:
        name = str(record.get("name", "")).strip()
        if not name:
            continue
        key = name.casefold()
        existing = by_name.get(key)
        if existing is None or _concept_rank(record) > _concept_rank(existing):
            by_name[key] = {**record, "name": name}
    return sorted(by_name.values(), key=_concept_rank, reverse=True)


def _concept_rank(record: dict[str, Any]) -> float:
    score = record.get("score")
    level = record.get("level")
    score_value = float(score) if isinstance(score, int | float) else 0.0
    level_value = int(level) if isinstance(level, int) else 5
    source_boost = 0.2 if record.get("source") == "author" else 0.0
    return score_value + source_boost - (level_value * 0.03)


def _institutions(author: dict[str, Any]) -> list[str]:
    institutions = []
    for item in author.get("last_known_institutions", []) or []:
        if isinstance(item, dict) and item.get("display_name"):
            institutions.append(str(item["display_name"]))
    return sorted(set(institutions))


def _summary(author: dict[str, Any], concepts: list[str], works: list[str], institutions: list[str]) -> str:
    name = author.get("display_name") or "This researcher"
    count = author.get("works_count")
    parts = []
    if count:
        parts.append(f"{name} has {count} OpenAlex-indexed works")
    else:
        parts.append(f"{name} has OpenAlex-indexed research activity")
    if institutions:
        parts.append(f"with affiliation data for {', '.join(institutions[:2])}")
    if concepts:
        parts.append(f"main research areas include {', '.join(concepts[:6])}")
    if works:
        parts.append(f"recent indexed publications include {', '.join(works[:3])}")
    return "; ".join(parts) + "."
