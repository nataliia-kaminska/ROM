# Security Hardening Notes

This document tracks security-focused improvements that make the Research Opportunity Matcher stronger for a thesis and closer to production practice.

## Completed

- Restricted opportunity write endpoints to administrators.
- Restricted ingestion endpoints to administrators.
- Added SSRF protection for external source imports:
  - blocks localhost, loopback, private, link-local, multicast, and unspecified hosts;
  - blocks URLs with embedded username/password credentials;
  - supports optional host allowlist through `EXTERNAL_SOURCE_ALLOWED_HOSTS`;
  - validates response content type before parsing;
  - limits downloaded source payload size through `EXTERNAL_SOURCE_MAX_BYTES`.
- Added tests for protected ingestion/write endpoints and SSRF URL blocking.
- Added token/auth hardening:
  - access tokens now include `iat`, `jti`, and `typ=access` claims;
  - refresh tokens are stored only as hashes in the database;
  - refresh tokens are delivered through an HttpOnly cookie;
  - `/auth/refresh` rotates refresh tokens and issues a new access token;
  - `/auth/logout` revokes the stored refresh token and clears the cookie;
  - frontend migrated access-token storage from `localStorage` to `sessionStorage`.
- Added rate limiting for sensitive auth endpoints:
  - registration;
  - login;
  - email verification;
  - refresh token rotation;
  - ORCID OAuth start and callback.
- Added tests for refresh token rotation, logout revocation, and auth rate limiting.

## Recommended Next

- Extend rate limiting to admin import/job endpoints with stricter buckets.
- Add refresh-token reuse detection and account/session audit events.
- Replace custom PBKDF2 password hashing with Argon2id.
- Add production startup checks for unsafe defaults such as weak JWT secret, default DB passwords, and disabled Elasticsearch security.
- Add outbox events for reliable Elasticsearch indexing, embedding refresh, and notification dispatch.
- Add metrics/tracing for ingestion quality, recommendation latency, and failed external provider calls.
