# ORCID OAuth Sign-In Setup

The app supports ORCID OAuth 2.0 sign-in as an alternative to local password accounts.
ORCID users are stored with `auth_provider=orcid`, `orcid_id`, `email_verified=true`, and `password_login_enabled=false`.

## Local Callback URLs

Use these URLs when creating the ORCID client:

- Backend redirect URI: `http://127.0.0.1:8000/auth/orcid/callback`
- Frontend callback page: `http://127.0.0.1:3000/orcid-callback`

## Environment

Set these values in `.env`:

```env
ORCID_OAUTH_ENABLED=true
ORCID_CLIENT_ID=your-orcid-client-id
ORCID_CLIENT_SECRET=your-orcid-client-secret
ORCID_REDIRECT_URI=http://127.0.0.1:8000/auth/orcid/callback
ORCID_AUTHORIZE_URL=https://orcid.org/oauth/authorize
ORCID_TOKEN_URL=https://orcid.org/oauth/token
ORCID_OAUTH_SCOPE=/authenticate
```

For ORCID sandbox testing, use the sandbox URLs instead:

```env
ORCID_AUTHORIZE_URL=https://sandbox.orcid.org/oauth/authorize
ORCID_TOKEN_URL=https://sandbox.orcid.org/oauth/token
```

Restart the backend after changing `.env`.

## Flow

1. The user clicks `Sign in with ORCID`.
2. Backend creates a short-lived signed OAuth `state`.
3. ORCID authenticates the user and redirects to `/auth/orcid/callback`.
4. Backend exchanges the authorization code for an authenticated ORCID iD.
5. Backend finds or creates a passwordless local user and redirects to `/orcid-callback?token=...`.
6. Frontend stores the app JWT and opens the workspace.
