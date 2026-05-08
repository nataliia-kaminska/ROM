from app.integrations.grants_gov.client import GrantsGovClient
from app.integrations.grants_gov.service import ingest_grants_gov as _ingest_grants_gov


def ingest_grants_gov(
    keyword: str,
    limit: int = 10,
    import_results: bool = True,
    db=None,
):
    return _ingest_grants_gov(
        keyword=keyword,
        limit=limit,
        import_results=import_results,
        db=db,
        client=GrantsGovClient(),
    )


__all__ = ["GrantsGovClient", "ingest_grants_gov"]
