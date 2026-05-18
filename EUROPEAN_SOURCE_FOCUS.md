# European Opportunity Source Focus

The catalog now has explicit support for several European opportunity sources that are important for an academic research-matching thesis.

## Added Connectors

- `horizon_europe` / `horizon`
  - Focus: European Commission research and innovation calls.
  - Default type: grant.
  - Default country scope: European Union.
  - Keywords: Horizon Europe, European Commission, research and innovation, EU funding.
- `erasmus`
  - Focus: Erasmus+ mobility and exchange opportunities.
  - Default type: exchange.
  - Default country scope: European Union.
  - Keywords: Erasmus+, mobility, exchange, Europe.
- `nawa`
  - Focus: Polish National Agency for Academic Exchange scholarships and academic mobility programmes.
  - Default type: fellowship.
  - Default country scope: Poland.
  - Keywords: NAWA, Poland, academic exchange, scholarship.

## Admin Presets

The Admin Console source import page now includes presets for:

- Horizon Europe: European Commission Funding & Tenders calls page.
- Erasmus+: Erasmus+ opportunities for individuals.
- NAWA: Polish academic exchange and scholarship programmes.

These presets are intentionally conservative. Some official portals are JavaScript-heavy and may import only high-level links through the generic HTML importer. When that happens, the best next enhancement is a source-specific API/page crawler for the provider rather than loosening the generic parser too much.

## Why This Strengthens The Project

- Reduces US-centric bias from relying mainly on Grants.gov.
- Adds EU mobility, scholarship, and research funding contexts.
- Improves relevance for Ukrainian and European researchers.
- Gives the thesis a clearer international academic opportunity scope.

## Official Source References

- Horizon Europe calls are published through the European Commission Funding & Tenders Portal.
- Erasmus+ publishes mobility and education opportunities through the official Erasmus+ portal.
- NAWA publishes Polish academic exchange and scholarship programmes through the official NAWA portal.
