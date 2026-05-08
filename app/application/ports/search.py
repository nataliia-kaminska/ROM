from typing import Protocol


class OpportunitySearchPort(Protocol):
    def search_opportunity_ids(
        self,
        keyword: str,
        limit: int,
        offset: int = 0,
        filters: dict[str, str] | None = None,
    ) -> list[int]:
        ...

    def index_opportunity(self, opportunity) -> None:
        ...
