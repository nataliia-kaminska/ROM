from typing import Any


def extract_openalex_profile(author: dict[str, Any], works: list[dict[str, Any]]) -> dict[str, Any]:
    author_id = author.get("id")
    concepts = [
        item.get("display_name")
        for item in author.get("x_concepts", [])
        if isinstance(item, dict) and item.get("display_name")
    ]
    work_titles = [
        work.get("display_name") or work.get("title")
        for work in works
        if isinstance(work, dict) and (work.get("display_name") or work.get("title"))
    ]
    work_concepts = []
    for work in works:
        for concept in work.get("concepts", []) if isinstance(work, dict) else []:
            name = concept.get("display_name") if isinstance(concept, dict) else None
            if name:
                work_concepts.append(name)
    return {
        "display_name": author.get("display_name") or "",
        "openalex_author_id": author_id,
        "concepts": sorted(set(concepts + work_concepts)),
        "works": work_titles,
        "summary": _summary(author, concepts, work_titles),
    }


def _summary(author: dict[str, Any], concepts: list[str], works: list[str]) -> str:
    name = author.get("display_name") or "This researcher"
    concept_text = ", ".join(concepts[:5])
    count = author.get("works_count")
    if concept_text and count:
        return f"{name} has {count} OpenAlex-indexed works with activity in {concept_text}."
    if concept_text:
        return f"{name} has OpenAlex-indexed activity in {concept_text}."
    if works:
        return f"{name} has OpenAlex-indexed publications including {works[0]}."
    return ""
