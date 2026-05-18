from urllib.parse import urlparse


EUROPEAN_GENERIC_SOURCE_NAMES = ("erasmus", "nawa", "horizon")

GENERIC_PROVIDER_URL_FRAGMENTS = (
    "applying-by-yourself",
    "opportunities-for-individuals",
    "calls-for-proposals",
    "topic-search",
    "screen/opportunities",
    "erasmus-mundus-catalogue",
    "mobility-and-learning-agreements",
    "nawa-programmes",
)

GENERIC_PROVIDER_TITLES = {
    "applying by yourself",
    "calls for proposals",
    "funding opportunities",
    "mobility and learning agreements",
    "nawa programmes",
    "ongoing calls for proposals",
    "opportunities for individuals",
    "read what you can apply to by yourself",
    "search the erasmus mundus catalogue",
}


def is_generic_provider_reference(source_name: str, title: str, url: str) -> bool:
    normalized_source = source_name.strip().lower().replace("-", "_")
    if not any(source in normalized_source for source in EUROPEAN_GENERIC_SOURCE_NAMES):
        return False
    normalized_title = " ".join(title.casefold().split()).strip(" .:-")
    if normalized_title in GENERIC_PROVIDER_TITLES:
        return True
    normalized_url = url.casefold()
    path = urlparse(normalized_url).path
    return any(fragment in normalized_url or fragment in path for fragment in GENERIC_PROVIDER_URL_FRAGMENTS)
