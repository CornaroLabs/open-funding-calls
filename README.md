# Open Funding Calls

An open, vendor-neutral data standard for describing **funding opportunities**: grant calls, rounds and programme windows from EU and national programmes, foundations, and open source or crypto-native funders.

Existing open standards (360Giving, IATI, OCDS, schema.org `Grant`) describe money that has already been awarded or spent. Open Funding Calls describes the call **before** people apply: who funds, how much, for whom, by when, under which conditions, and how fresh the information is.

> Status: **prototype v0.1.0**. Expect breaking changes until v1.0. Feedback is very welcome in the issue tracker.

## What is here

| Path | What it is |
|---|---|
| `schema/funding-call.schema.json` | JSON Schema (2020-12) for one funding call record |
| `schema/context.jsonld` | JSON-LD context mapping core fields to schema.org |
| `examples/` | Valid example records; `examples/invalid/` shows common mistakes |
| `python/` | Validator library and CLI (`ofc-validate`) |

## The record at a glance

```json
{
  "specVersion": "0.1.0",
  "id": "web3grants.co:nlnet-restack-2",
  "title": "NLnet Restack Fund, second call",
  "funder": { "name": "Stichting NLnet", "url": "https://nlnet.nl" },
  "status": "open",
  "amount": { "currency": "EUR", "minPerProject": 5000, "maxPerProject": 50000 },
  "dates": { "deadlines": [{ "dateTime": "2027-01-03T12:00:00+01:00" }] },
  "eligibility": { "countries": ["HE-ASSOCIATED"], "openSourceRequired": true },
  "sourceUrl": "https://nlnet.nl/restack/",
  "provenance": { "publisher": "web3grants.co", "lastVerified": "2026-11-22T11:00:00Z", "license": "CC-BY-4.0" }
}
```

Design choices:

- **Status lifecycle**: `upcoming`, `open`, `rolling`, `paused`, `closed`, `cancelled`.
- **Time zones are mandatory** on every date-time, and a call can have several deadlines.
- **Amounts stay in the funder's unit**: ISO 4217 for fiat (`EUR`), `crypto:` prefix for crypto assets (`crypto:ARB`). No conversion is implied.
- **Identifiers are reused, not invented**: ROR, Wikidata, CAIP-10 chain addresses.
- **Provenance is required**: who published the record and when it was last checked against the source.
- **Multilingual text**: any text field can be a plain string or `{"en": "...", "el": "..."}`.

## Validate records

```bash
cd python
pip install -e .
ofc-validate ../examples            # or: python -m open_funding_calls FILE...
ofc-validate data.jsonl --json      # machine-readable report
ofc-validate data/ --strict         # warnings fail too
```

The validator runs two layers:

1. **Structural**: JSON Schema, including formats.
2. **Semantic**, with stable rule ids: `date-timezone`, `date-order`, `status-expired`, `status-upcoming-past`, `rolling-with-deadline`, `no-deadline`, `amount-range`, `amount-total`, `stale`, `verified-in-future`.

Run the tests with `cd python && python -m pytest`.

## Roadmap

- v0.9 specification with public review, code lists and an extension mechanism
- JavaScript/TypeScript validator sharing the same test fixtures
- Open source reference API and bulk data publication (JSON Lines, CSV), seeded with web3grants.co listings
- Crosswalks to schema.org, EU Funding & Tenders Portal, Grants.gov and DAOIP-5

## Licence

Code: Apache-2.0 (see `LICENSE`). Specification, schema and documentation: CC BY 4.0.

Maintained by [Cornaro Labs](https://cornarolabs.xyz), the team behind [web3grants.co](https://web3grants.co).
