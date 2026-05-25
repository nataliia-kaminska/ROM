import { type FormEvent, useEffect, useState } from "react";
import type { ProfileDetailsPayload, ProfilePayload } from "../api";
import type { CareerStage, OpenAlexPreview, OpportunityType, ProfileDiscoveryCandidate } from "../types";
import { careerStages, opportunityTypes } from "../constants";
import { ActionButton, Field, HelpTip, MultiValueField, PageHeader, SelectField, TextArea } from "../components/ui";
import { label } from "../utils/format";

type ProfileSection = "preview" | "basics" | "research" | "imports";

export function ProfileView({
  userEmail,
  userFullName,
  userAuthProvider,
  userOrcidId,
  activeProfileExists,
  loading,
  profileForm,
  detailsForm,
  disciplineOptions,
  keywordOptions,
  countryOptions,
  orcidForm,
  openAlexForm,
  openAlexPreview,
  profileDiscoveryCandidates,
  profileDiscoveryConfirmed,
  profileDiscoveryLoading,
  highlightFields,
  onProfileChange,
  onDetailsChange,
  onSaveProfile,
  onSaveDetails,
  onOrcidChange,
  onOpenAlexChange,
  onImportOrcid,
  onImportOpenAlex,
  onPreviewOpenAlex,
  onDiscoverProfileCandidates,
  onApplyProfileCandidate,
  onDismissProfileCandidate,
  onOpenAccountSettings,
}: {
  userEmail: string;
  userFullName: string;
  userAuthProvider: string;
  userOrcidId: string | null;
  activeProfileExists: boolean;
  loading: boolean;
  profileForm: ProfilePayload;
  detailsForm: ProfileDetailsPayload;
  disciplineOptions: string[];
  keywordOptions: string[];
  countryOptions: string[];
  orcidForm: { orcid_id: string; email: string; career_stage: CareerStage; disciplines: string; preferred_countries: string };
  openAlexForm: { openalex_author_id: string; orcid_id: string; max_works: number };
  openAlexPreview: OpenAlexPreview | null;
  profileDiscoveryCandidates: ProfileDiscoveryCandidate[];
  profileDiscoveryConfirmed: ProfileDiscoveryCandidate[];
  profileDiscoveryLoading: boolean;
  highlightFields: string[];
  onProfileChange: (form: ProfilePayload) => void;
  onDetailsChange: (form: ProfileDetailsPayload) => void;
  onSaveProfile: (event: FormEvent) => void;
  onSaveDetails: (event: FormEvent) => void;
  onOrcidChange: (form: { orcid_id: string; email: string; career_stage: CareerStage; disciplines: string; preferred_countries: string }) => void;
  onOpenAlexChange: (form: { openalex_author_id: string; orcid_id: string; max_works: number }) => void;
  onImportOrcid: (event: FormEvent) => void;
  onImportOpenAlex: () => void;
  onPreviewOpenAlex: (event: FormEvent) => void;
  onDiscoverProfileCandidates: () => void;
  onApplyProfileCandidate: (candidate: ProfileDiscoveryCandidate) => void;
  onDismissProfileCandidate: (candidate: ProfileDiscoveryCandidate) => void;
  onOpenAccountSettings: () => void;
}) {
  const [section, setSection] = useState<ProfileSection>(() => sectionFromHash());
  const accountName = userFullName || profileForm.full_name;
  const highlights = new Set(highlightFields);
  const isOrcidAccount = userAuthProvider === "orcid";

  function selectSection(nextSection: ProfileSection) {
    setSection(nextSection);
    if (window.location.hash) {
      window.history.replaceState(null, "", "/profile");
    }
  }

  useEffect(() => {
    const syncHash = () => setSection(sectionFromHash());
    window.addEventListener("hashchange", syncHash);
    return () => window.removeEventListener("hashchange", syncHash);
  }, []);

  useEffect(() => {
    if (highlightFields.some((field) => ["research_summary", "publications"].includes(field))) {
      selectSection("research");
      return;
    }
    if (highlightFields.length > 0) {
      selectSection("basics");
    }
  }, [highlightFields.join("|")]);

  return (
    <section className="profile-page">
      <PageHeader
        title={section === "preview" ? "Research profile" : "Profile editor"}
        description={section === "preview" ? "Review how your profile looks to the matching engine before editing details." : "Update profile basics, research evidence, and imported academic metadata."}
        hint="Country, career stage, disciplines, keywords, publications, and research summary have the strongest effect on personalized matches."
      />

      <div className="panel">
      {section !== "preview" && (
        <nav className="profile-subnav" aria-label="Profile sections">
        <button type="button" onClick={() => selectSection("preview")}>
          Preview
        </button>
        <button type="button" className={section === "basics" ? "active" : ""} onClick={() => selectSection("basics")}>
          Wizard and Editor
        </button>
        <button type="button" className={section === "research" ? "active" : ""} onClick={() => selectSection("research")}>
          Research Evidence
        </button>
        <button type="button" className={section === "imports" ? "active" : ""} onClick={() => selectSection("imports")}>
          Imports
        </button>
      </nav>
      )}

      {section === "preview" && (
        <ProfilePreview
          accountName={accountName}
          userEmail={userEmail}
          profileForm={profileForm}
          detailsForm={detailsForm}
          isOrcidAccount={isOrcidAccount}
          userOrcidId={userOrcidId}
          onEdit={() => selectSection("basics")}
          onAccount={onOpenAccountSettings}
          discoveryCandidates={profileDiscoveryCandidates}
          discoveryConfirmed={profileDiscoveryConfirmed}
          discoveryLoading={profileDiscoveryLoading}
          onDiscover={onDiscoverProfileCandidates}
          onApplyCandidate={onApplyProfileCandidate}
          onDismissCandidate={onDismissProfileCandidate}
        />
      )}

      {section === "basics" && (
        <form className="grid-form" onSubmit={onSaveProfile}>
          <Field
            labelText="Account name"
            value={accountName}
            disabled
            onChange={() => undefined}
            title="This comes from the name saved on your account during registration."
          />
          <Field labelText="Account email" value={userEmail} disabled onChange={() => undefined} title="Profile email is linked to the signed-in account." />
          <SelectField
            labelText="Career stage"
            value={profileForm.career_stage}
            options={careerStages}
            required
            className={fieldHighlight(highlights, "career_stage")}
            onChange={(career_stage) => onProfileChange({ ...profileForm, career_stage })}
          />
          <Field
            labelText="Home country"
            value={profileForm.country ?? ""}
            list="profile-country-options"
            required
            className={fieldHighlight(highlights, "country")}
            placeholder="Where you are based or hold primary eligibility"
            title="Used as your home country for eligibility checks, mobility warnings, and recommendation explanations."
            onChange={(country) => onProfileChange({ ...profileForm, country })}
          />
          <MultiValueField
            labelText="Disciplines"
            values={profileForm.disciplines}
            placeholder="Type a discipline, then Enter"
            help="Used for semantic matching, eligibility scoring, and match explanations."
            suggestions={disciplineOptions}
            className={fieldHighlight(highlights, "disciplines")}
            onChange={(disciplines) => onProfileChange({ ...profileForm, disciplines })}
          />
          <MultiValueField
            labelText="Keywords"
            values={profileForm.keywords}
            placeholder="Type a keyword, then Enter"
            help="Used to find topic overlap with opportunity summaries, keywords, and source metadata."
            suggestions={keywordOptions}
            className={fieldHighlight(highlights, "keywords")}
            onChange={(keywords) => onProfileChange({ ...profileForm, keywords })}
          />
          <MultiValueField
            labelText="Preferred countries"
            values={profileForm.preferred_countries}
            placeholder="Type a country, then Enter"
            help="Used to boost opportunities in countries you prefer."
            suggestions={countryOptions}
            onChange={(preferred_countries) => onProfileChange({ ...profileForm, preferred_countries })}
          />
          <Field labelText="Google Scholar URL" value={profileForm.google_scholar_url ?? ""} onChange={(google_scholar_url) => onProfileChange({ ...profileForm, google_scholar_url })} />
          <ActionButton busy={loading} className="span-2">{activeProfileExists ? "Update profile" : "Create profile"}</ActionButton>
        </form>
      )}

      {section === "research" && (
        <form className="grid-form separated" onSubmit={onSaveDetails}>
          <div className="span-2 focus-strip">
            <strong>Most important</strong>
            <span>Research summary, publications, and funding interests have the biggest effect on match explanations and advisor notes.</span>
          </div>
          <AcademicEvidence detailsForm={detailsForm} />
          <TextArea labelText="Research summary" className={`span-2 ${fieldHighlight(highlights, "research_summary")}`} value={detailsForm.research_summary} onChange={(research_summary) => onDetailsChange({ ...detailsForm, research_summary })} />
          <MultiValueField className={fieldHighlight(highlights, "publications")} labelText="Publications" values={detailsForm.publications} placeholder="Paste a title or DOI, then Enter" help="Used by readiness scoring and the assistant to identify strengths and publication gaps." onChange={(publications) => onDetailsChange({ ...detailsForm, publications })} />
          <MultiValueField labelText="Degrees" values={detailsForm.degrees} placeholder="Example: PhD Computer Science" help="Used for eligibility checks when opportunities require a degree level." suggestions={["Bachelor", "Master", "PhD", "MD", "MBA"]} onChange={(degrees) => onDetailsChange({ ...detailsForm, degrees })} />
          <MultiValueField labelText="Languages" values={detailsForm.languages} placeholder="Example: English" help="Used when requirements mention language ability." suggestions={["English", "German", "French", "Spanish", "Ukrainian"]} onChange={(languages) => onDetailsChange({ ...detailsForm, languages })} />
          <MultiValueField labelText="Funding interests" values={detailsForm.funding_interests} placeholder="Example: mobility funding" help="Used as extra topic preference for recommendations and advisor context." suggestions={keywordOptions} onChange={(funding_interests) => onDetailsChange({ ...detailsForm, funding_interests })} />
          <MultiValueField labelText="Unavailable countries" values={detailsForm.unavailable_countries} placeholder="Type a country, then Enter" help="Used to reduce or warn about opportunities in places you cannot relocate to." suggestions={countryOptions} onChange={(unavailable_countries) => onDetailsChange({ ...detailsForm, unavailable_countries })} />
          <MultiValueField
            labelText="Preferred types"
            values={detailsForm.preferred_opportunity_types}
            placeholder="Example: fellowship"
            help="Used to boost opportunity categories you care about."
            suggestions={opportunityTypes}
            onChange={(preferred_opportunity_types) => onDetailsChange({ ...detailsForm, preferred_opportunity_types: preferred_opportunity_types as OpportunityType[] })}
          />
          <ActionButton busy={loading} className="span-2">Save details</ActionButton>
        </form>
      )}

      {section === "imports" && (
        <ProfileImportsView
          orcidForm={orcidForm}
          openAlexForm={openAlexForm}
          openAlexPreview={openAlexPreview}
          isOrcidAccount={isOrcidAccount}
          userOrcidId={userOrcidId}
          onOrcidChange={onOrcidChange}
          onOpenAlexChange={onOpenAlexChange}
          onImportOrcid={onImportOrcid}
          onImportOpenAlex={onImportOpenAlex}
          onPreviewOpenAlex={onPreviewOpenAlex}
        />
      )}

      <datalist id="profile-country-options">{countryOptions.map((item) => <option value={item} key={item} />)}</datalist>
      </div>
    </section>
  );
}

function ProfilePreview({
  accountName,
  userEmail,
  profileForm,
  detailsForm,
  isOrcidAccount,
  userOrcidId,
  onEdit,
  onAccount,
  discoveryCandidates,
  discoveryConfirmed,
  discoveryLoading,
  onDiscover,
  onApplyCandidate,
  onDismissCandidate,
}: {
  accountName: string;
  userEmail: string;
  profileForm: ProfilePayload;
  detailsForm: ProfileDetailsPayload;
  isOrcidAccount: boolean;
  userOrcidId: string | null;
  onEdit: () => void;
  onAccount: () => void;
  discoveryCandidates: ProfileDiscoveryCandidate[];
  discoveryConfirmed: ProfileDiscoveryCandidate[];
  discoveryLoading: boolean;
  onDiscover: () => void;
  onApplyCandidate: (candidate: ProfileDiscoveryCandidate) => void;
  onDismissCandidate: (candidate: ProfileDiscoveryCandidate) => void;
}) {
  const identity = [
    profileForm.career_stage ? label(profileForm.career_stage) : "",
    profileForm.country,
    isOrcidAccount && userOrcidId ? `ORCID ${userOrcidId}` : "",
  ].filter(Boolean);
  return (
    <div className="profile-preview">
      <article className="profile-preview-hero">
        <div>
          <p className="eyebrow">{isOrcidAccount ? "ORCID-linked researcher" : "Researcher profile"}</p>
          <h3>{accountName || "Unnamed researcher"}</h3>
          <p>{userEmail}</p>
          <div className="chips">
            {identity.map((item) => (
              <span key={item}>{item}</span>
            ))}
          </div>
        </div>
        <div className="actions">
          <button className="primary" type="button" onClick={onEdit}>
            Edit profile
          </button>
          <button className="secondary" type="button" onClick={onAccount}>
            Account settings
          </button>
        </div>
      </article>
      <div className="profile-preview-grid">
        <PreviewCard title="Disciplines" values={profileForm.disciplines} empty="Add disciplines to improve topic matching." />
        <PreviewCard title="Keywords" values={profileForm.keywords} empty="Add keywords to tune search and recommendations." />
        <PreviewCard title="Languages and degrees" values={[...detailsForm.languages, ...detailsForm.degrees]} empty="Add languages and degrees for eligibility checks." />
        <PreviewCard title="Research summary" values={detailsForm.research_summary ? [detailsForm.research_summary] : []} empty="Add a short summary so the assistant can personalize advice." variant="full" />
        <PreviewCard title="Funding preferences" values={detailsForm.funding_interests} empty="Add funding interests to guide recommendations." />
        <PreviewCard title="Publications" values={detailsForm.publications} empty="Import or add publications to strengthen readiness scoring." variant="wide" />
      </div>
      <section className="profile-discovery">
        <div>
          <div>
            <span>Public profile discovery</span>
            <strong>Find public evidence</strong>
            <p>Search for researcher pages that may enrich your summary, disciplines, keywords, publications, degrees, languages, funding interests, and profile embedding after you confirm a result.</p>
          </div>
          <HelpTip text="Nothing is imported automatically. Confirming a source lets the system parse the page, extract useful academic metadata, and refresh the profile embedding used by recommendations." />
          <button className="secondary" type="button" disabled={discoveryLoading} onClick={onDiscover}>
            {discoveryLoading ? "Searching..." : "Find public profile"}
          </button>
        </div>
        {discoveryCandidates.length > 0 ? (
          <div className="profile-discovery-list">
            {discoveryCandidates.map((candidate) => (
              <article key={candidate.url}>
                <div>
                  <a href={candidate.url} target="_blank" rel="noreferrer">
                    <strong>{candidate.title}</strong>
                  </a>
                  <span>{candidate.source} - {candidate.confidence}% confidence</span>
                  <p>{candidate.snippet}</p>
                </div>
                <div className="actions">
                  <button className="primary icon-choice" type="button" title="Yes, enrich my profile from this source" onClick={() => onApplyCandidate(candidate)}>
                    Yes
                  </button>
                  <button className="secondary icon-choice" type="button" title="No, hide this suggestion" onClick={() => onDismissCandidate(candidate)}>
                    No
                  </button>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <p className="muted">Search DuckDuckGo for public researcher pages, then confirm before anything is merged into your profile.</p>
        )}
      </section>
      {discoveryConfirmed.length > 0 && (
        <section className="profile-discovery profile-discovery-confirmed">
          <div>
            <div>
              <span>Confirmed public sources</span>
              <strong>Reviewed links</strong>
              <p>These links were confirmed and will not appear again as suggestions for this profile.</p>
            </div>
          </div>
          <div className="profile-discovery-list">
            {discoveryConfirmed.map((candidate) => (
              <article key={candidate.url}>
                <div>
                  <a href={candidate.url} target="_blank" rel="noreferrer">
                    <strong>{candidate.title}</strong>
                  </a>
                  <span>{candidate.source}</span>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function PreviewCard({ title, values, empty, variant = "normal" }: { title: string; values: string[]; empty: string; variant?: "normal" | "wide" | "full" }) {
  const visible = values.filter(Boolean).slice(0, variant === "full" ? 2 : 6);
  return (
    <article className={`profile-preview-card profile-preview-card-${variant}`}>
      <span>{title}</span>
      {visible.length ? (
        variant === "full" ? (
          <p>{visible.join(" ")}</p>
        ) : (
          <div className="chips">
            {visible.map((value) => (
              <span key={value}>{value}</span>
            ))}
          </div>
        )
      ) : (
        <p className="muted">{empty}</p>
      )}
    </article>
  );
}

function sectionFromHash(): ProfileSection {
  return "preview";
}

function AcademicEvidence({ detailsForm }: { detailsForm: ProfileDetailsPayload }) {
  const topPublications = detailsForm.publications.slice(0, 3);
  const topInterests = detailsForm.funding_interests.slice(0, 6);
  return (
    <article className="academic-evidence span-2">
      <div>
        <span>Academic evidence</span>
        <strong>{detailsForm.publications.length} publications</strong>
      </div>
      <p>
        Imported publications and funding interests are used in match explanations, semantic profile embeddings, and advisor memos.
      </p>
      {topPublications.length > 0 && (
        <ul>
          {topPublications.map((publication) => (
            <li key={publication}>{publication}</li>
          ))}
        </ul>
      )}
      {topInterests.length > 0 && (
        <div className="chips">
          {topInterests.map((interest) => (
            <span key={interest}>{interest}</span>
          ))}
        </div>
      )}
    </article>
  );
}

function fieldHighlight(highlights: Set<string>, field: string): string {
  return highlights.has(field) ? "field-highlight" : "";
}

export function ProfileImportsView({
  orcidForm,
  openAlexForm,
  openAlexPreview,
  isOrcidAccount,
  userOrcidId,
  onOrcidChange,
  onOpenAlexChange,
  onImportOrcid,
  onImportOpenAlex,
  onPreviewOpenAlex,
}: {
  orcidForm: { orcid_id: string; email: string; career_stage: CareerStage; disciplines: string; preferred_countries: string };
  openAlexForm: { openalex_author_id: string; orcid_id: string; max_works: number };
  openAlexPreview: OpenAlexPreview | null;
  isOrcidAccount: boolean;
  userOrcidId: string | null;
  onOrcidChange: (form: { orcid_id: string; email: string; career_stage: CareerStage; disciplines: string; preferred_countries: string }) => void;
  onOpenAlexChange: (form: { openalex_author_id: string; orcid_id: string; max_works: number }) => void;
  onImportOrcid: (event: FormEvent) => void;
  onImportOpenAlex: () => void;
  onPreviewOpenAlex: (event: FormEvent) => void;
}) {
  return (
    <div>
      <div className="section-title">
        <div className="title-with-help">
          <h2>Profile Imports</h2>
          <HelpTip text="ORCID is a public researcher identifier. This app uses it to prefill your profile and improve matching with public academic metadata." />
        </div>
      </div>
      <form className="grid-form" onSubmit={onImportOrcid}>
        <Field labelText="ORCID iD" value={userOrcidId || orcidForm.orcid_id} disabled={isOrcidAccount} onChange={(orcid_id) => onOrcidChange({ ...orcidForm, orcid_id })} placeholder="0000-0000-0000-0000" />
        <Field labelText="Email" value={orcidForm.email} disabled={isOrcidAccount} onChange={(email) => onOrcidChange({ ...orcidForm, email })} />
        <SelectField labelText="Career stage" value={orcidForm.career_stage} options={careerStages} onChange={(career_stage) => onOrcidChange({ ...orcidForm, career_stage })} />
        <Field labelText="Disciplines" value={orcidForm.disciplines} onChange={(disciplines) => onOrcidChange({ ...orcidForm, disciplines })} />
        <Field labelText="Preferred countries" value={orcidForm.preferred_countries} onChange={(preferred_countries) => onOrcidChange({ ...orcidForm, preferred_countries })} />
        <button className="primary span-2">Import public profile</button>
      </form>
      <form className="grid-form separated" onSubmit={onPreviewOpenAlex}>
        <div className="span-2">
          <div className="title-with-help">
            <h2>OpenAlex Enrichment</h2>
            <HelpTip text="OpenAlex is an open scholarly graph. Enrichment adds public publication titles and concepts to improve profile completeness and recommendation explanations." />
          </div>
          <p className="muted">Preview public concepts and publication titles before merging them into the active profile.</p>
        </div>
        <Field labelText="OpenAlex author id" value={openAlexForm.openalex_author_id} onChange={(openalex_author_id) => onOpenAlexChange({ ...openAlexForm, openalex_author_id })} placeholder="A1234567890" />
        <Field labelText="ORCID override" value={openAlexForm.orcid_id} onChange={(orcid_id) => onOpenAlexChange({ ...openAlexForm, orcid_id })} />
        <Field labelText="Max works" type="number" value={String(openAlexForm.max_works)} onChange={(max_works) => onOpenAlexChange({ ...openAlexForm, max_works: Number(max_works) })} />
        <div className="actions">
          <button className="primary">Preview OpenAlex</button>
          <button className="secondary" type="button" disabled={!openAlexPreview} onClick={() => onImportOpenAlex()}>
            Import preview
          </button>
        </div>
        {openAlexPreview && <OpenAlexPreviewPanel preview={openAlexPreview} />}
      </form>
    </div>
  );
}

function OpenAlexPreviewPanel({ preview }: { preview: OpenAlexPreview }) {
  return (
    <article className="openalex-preview span-2">
      <div className="section-title compact-title">
        <div>
          <p className="eyebrow">OpenAlex preview</p>
          <h3>{preview.display_name || "Matched researcher"}</h3>
          {preview.summary && <p>{preview.summary}</p>}
        </div>
        <strong>{preview.works_count} works</strong>
      </div>
      <div className="evidence-grid">
        <EvidenceList title="New publications" values={preview.new_publications} empty="No new publications detected." />
        <EvidenceList title="Suggested disciplines" values={preview.suggested_disciplines} empty="No discipline suggestions." />
        <EvidenceList title="Suggested keywords" values={preview.suggested_keywords} empty="No keyword suggestions." />
        <EvidenceList title="Funding interests" values={preview.suggested_funding_interests} empty="No funding interest suggestions." />
      </div>
    </article>
  );
}

function EvidenceList({ title, values, empty }: { title: string; values: string[]; empty: string }) {
  return (
    <div>
      <strong>{title}</strong>
      {values.length ? (
        <ul>
          {values.slice(0, 6).map((value) => (
            <li key={value}>{value}</li>
          ))}
        </ul>
      ) : (
        <p className="muted">{empty}</p>
      )}
    </div>
  );
}
