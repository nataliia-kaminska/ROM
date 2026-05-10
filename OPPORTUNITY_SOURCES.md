# Opportunity Sources

This document describes the expanded opportunity ingestion sources added beyond Grants.gov.

## What Changed

The external source importer now supports three source formats:

- `rss`: RSS or Atom feeds.
- `json`: JSON APIs or exported source payloads.
- `html`: ordinary source pages with links to calls, grants, fellowships, programmes, and competitions.

HTML support is useful for Ukrainian and Europe-focused sources that publish opportunity catalogues as regular web pages rather than stable APIs.

## Supported Source Names

Use these `source_name` values in the Admin external import form:

- `nrfu`: National Research Foundation of Ukraine calls.
- `nauka_gov_ua`: Ukrainian science/government research opportunity pages.
- `house_of_europe`: House of Europe opportunity catalogue.
- `science_for_ukraine`: Science for Ukraine researcher support and opportunity pages.
- `msca4ukraine`: MSCA4Ukraine fellowship and displaced-researcher support calls.
- `daad_ukraine`: DAAD Ukraine, including Future Ukraine research grants.
- `fulbright_ukraine`: Fulbright Ukraine academic exchange opportunities.
- `euraxess`: EURAXESS research positions and mobility opportunities.
- `daad`: Generic DAAD opportunities.
- `fulbright`: Generic Fulbright opportunities.
- `msca`: Generic Marie Sklodowska-Curie Actions opportunities.

## Suggested Ukrainian And Ukraine-Focused URLs

These URLs are good starting points for Admin -> External Source Import:

- `nrfu`, `html`: `https://nrfu.org.ua/en/contests/current-calls/`
- `nrfu`, `html`: `https://nrfu.org.ua/en/contests-posts-en/`
- `nauka_gov_ua`, `html`: `https://nauka.gov.ua/`
- `house_of_europe`, `html`: `https://houseofeurope.org.ua/en/opportunities`
- `science_for_ukraine`, `html`: `https://scienceforukraine.eu/`
- `msca4ukraine`, `html`: `https://www.eua.eu/our-work/projects/eu-funded-projects/msca4ukraine-fellowship-scheme.html`
- `daad_ukraine`, `html`: `https://www.daad-ukraine.org/en/`
- `fulbright_ukraine`, `html`: `https://fulbright.org.ua/en/`

## How Normalization Works

Each source connector maps source-specific fields into the shared opportunity model:

- title;
- URL;
- summary;
- eligibility;
- opportunity type;
- disciplines;
- keywords;
- countries;
- career stages;
- deadline.

The Ukrainian connectors add sensible defaults where source pages are sparse. For example:

- `nrfu` defaults to `grant`, `Ukraine`, and research-oriented keywords.
- `house_of_europe` defaults to `grant`, `Ukraine`, `European Union`, and EU/Ukraine keywords.
- `daad_ukraine` defaults to Germany/Ukraine mobility and fellowship keywords.
- `msca4ukraine` defaults to fellowship, Ukraine/EU, and Horizon Europe/MSCA keywords.

The importer still deduplicates opportunities by URL and updates existing records instead of blindly creating duplicates.

## Admin Import Example

For House of Europe:

```text
Source name: house_of_europe
Feed or page URL: https://houseofeurope.org.ua/en/opportunities
Kind: html
Default type: grant
Limit: 25
Import results: enabled
```

For NRFU:

```text
Source name: nrfu
Feed or page URL: https://nrfu.org.ua/en/contests/current-calls/
Kind: html
Default type: grant
Default country: Ukraine
Limit: 25
Import results: enabled
```

## Notes And Limitations

The HTML importer is intentionally conservative. It extracts links that look like calls, grants, fellowships, scholarships, programmes, research opportunities, competitions, or Ukrainian equivalents such as `грант`, `конкурс`, `стипенд`, and `можлив`.

For high-quality production ingestion, the next enhancement would be source-specific HTML detail crawlers. Those crawlers would open each extracted opportunity page and extract richer fields such as deadline, funding amount, eligibility, disciplines, and application instructions.
