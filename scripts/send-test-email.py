from app.services.email_delivery import get_email_provider


def main() -> None:
    recipient = input("Recipient email shown in Mailtrap: ").strip() or "test@example.local"
    result = get_email_provider().send(
        recipient,
        "Research Matcher SMTP test",
        "This is a test email from Research Opportunity Matcher.",
    )
    print(f"provider={result.provider} status={result.status} message_id={result.message_id}")
    if result.error:
        print(f"error={result.error}")


if __name__ == "__main__":
    main()
