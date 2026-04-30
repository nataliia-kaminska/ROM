def pack_list(values: list[str]) -> str:
    return "\n".join(sorted({value.strip() for value in values if value.strip()}))


def unpack_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item for item in value.splitlines() if item]


def normalize_terms(values: list[str]) -> set[str]:
    return {value.strip().lower() for value in values if value.strip()}

