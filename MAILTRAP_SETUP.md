# Mailtrap Email Verification Setup

Use Mailtrap Email Sandbox for local verification emails.

## 1. Copy SMTP Credentials

In Mailtrap:

1. Open **Email Testing**.
2. Open **Sandboxes**.
3. Select your sandbox.
4. Open **Integration** -> **SMTP**.
5. Copy `Host`, `Port`, `Username`, and `Password`.

## 2. Configure `.env`

The project is already set to use Mailtrap Sandbox defaults:

```env
EMAIL_PROVIDER=smtp
EMAIL_FROM=Research Matcher <noreply@example.local>
FRONTEND_BASE_URL=http://127.0.0.1:3000
EMAIL_VERIFICATION_REQUIRED=true
EMAIL_VERIFICATION_EXPIRE_HOURS=24

SMTP_HOST=sandbox.smtp.mailtrap.io
SMTP_PORT=2525
SMTP_USERNAME=your_mailtrap_username
SMTP_PASSWORD=your_mailtrap_password
SMTP_USE_TLS=false
```

Paste only your real `SMTP_USERNAME` and `SMTP_PASSWORD` into `.env`.

## 3. Restart Backend

After changing `.env`, restart the backend process.

## 4. Test

Register a new account. The verification email should appear in your Mailtrap sandbox inbox.

Open the verification link from the email. The app will call `/auth/verify-email`, mark the account as verified, and allow sign-in.

## Notes

- Mailtrap Sandbox is for testing and does not deliver to real recipients.
- For real production email sending, use Mailtrap Email Sending with a verified sending domain and its SMTP credentials.
