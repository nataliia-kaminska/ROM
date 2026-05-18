from app.services.opportunity_page_preview import _html_to_readable_text


def test_page_preview_prioritizes_title_and_meta_description():
    text = _html_to_readable_text(
        """
        <html>
          <head>
            <title>MSCA Doctoral Networks 2026</title>
            <meta name="description" content="Funding for international doctoral training networks.">
          </head>
          <body>
            <nav>Search Home Login</nav>
            <main><h1>Call details</h1><p>Applicants build a consortium and train doctoral candidates.</p></main>
          </body>
        </html>
        """
    )

    assert text.startswith("MSCA Doctoral Networks 2026 Funding for international doctoral training networks.")
    assert "Search Home Login" not in text
