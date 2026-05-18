import type { View } from "../constants";

export function AboutView({ isSignedIn, onViewChange }: { isSignedIn: boolean; onViewChange: (view: View) => void }) {
  return (
    <section className="panel about-page">
      <div className="about-hero">
        <div>
          <p className="eyebrow">Research Opportunity Matcher</p>
          <h2>Find relevant academic opportunities without turning search into a second job.</h2>
          <p>
            The system collects grants, fellowships, exchanges, research positions, and training opportunities, then helps you browse,
            filter, rank, save, and plan applications from one workspace.
          </p>
        </div>
        <div className="about-hero-actions">
          <button className="primary" type="button" onClick={() => onViewChange("feed")}>
            Browse matches
          </button>
          {isSignedIn && (
            <button className="secondary" type="button" onClick={() => onViewChange("profile")}>
              Improve profile
            </button>
          )}
        </div>
      </div>

      <div className="about-grid">
        <article>
          <span>1</span>
          <h3>Opportunities are collected</h3>
          <p>
            Sources can include curated data, Grants.gov, Horizon Europe, Erasmus+, NAWA, EURAXESS, DAAD, Fulbright, MSCA-related feeds,
            Ukrainian sources, RSS, JSON, and HTML pages. Admin tools import and normalize these records into one catalog.
          </p>
        </article>
        <article>
          <span>2</span>
          <h3>Your profile adds context</h3>
          <p>
            Disciplines, keywords, country, career stage, research summary, publications, languages, and funding interests help the
            system understand what is actually relevant for you.
          </p>
        </article>
        <article>
          <span>3</span>
          <h3>Matching ranks the catalog</h3>
          <p>
            Recommendations combine semantic similarity, eligibility requirements, deadline timing, profile readiness, and previous
            saved or ignored opportunities.
          </p>
        </article>
        <article>
          <span>4</span>
          <h3>Search stays fast</h3>
          <p>
            Keyword search can use Elasticsearch for full-text ranking across titles, summaries, eligibility text, disciplines, and
            keywords. When Elasticsearch is disabled, the app falls back to database search.
          </p>
        </article>
        <article>
          <span>5</span>
          <h3>The board keeps intent clear</h3>
          <p>
            Save, plan, apply, accept, reject, or ignore opportunities. These statuses organize your workflow and also improve future
            recommendation signals.
          </p>
        </article>
        <article>
          <span>6</span>
          <h3>The assistant works on a specific opportunity</h3>
          <p>
            The Apply Assistant retrieves profile and opportunity evidence, then creates grounded checklists, fit notes, warnings, and
            exportable application notes for the selected saved or planned item.
          </p>
        </article>
      </div>

      <div className="about-flow">
        <h3>Typical workflow</h3>
        <div>
          <strong>Browse</strong>
          <span>Filter the catalog or review ranked matches.</span>
        </div>
        <div>
          <strong>Save</strong>
          <span>Keep promising opportunities and ignore poor fits.</span>
        </div>
        <div>
          <strong>Plan</strong>
          <span>Move serious applications to the board and reminders.</span>
        </div>
        <div>
          <strong>Prepare</strong>
          <span>Use the assistant for a checklist, fit statement, and gaps.</span>
        </div>
      </div>
    </section>
  );
}
