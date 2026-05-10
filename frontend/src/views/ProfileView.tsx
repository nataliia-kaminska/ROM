import { type FormEvent, useEffect, useState } from "react";
import type { ProfileDetailsPayload, ProfilePayload } from "../api";
import type { CareerStage, OpportunityType } from "../types";
import { careerStages, opportunityTypes } from "../constants";
import { ActionButton, Field, HelpTip, MultiValueField, SelectField, TextArea } from "../components/ui";

type ProfileSection = "basics" | "research" | "imports";

export function ProfileView({
  userEmail,
  userFullName,
  activeProfileExists,
  loading,
  profileForm,
  detailsForm,
  disciplineOptions,
  keywordOptions,
  countryOptions,
  orcidForm,
  openAlexForm,
  highlightFields,
  onProfileChange,
  onDetailsChange,
  onLoadDetails,
  onSaveProfile,
  onSaveDetails,
  onOrcidChange,
  onOpenAlexChange,
  onImportOrcid,
  onImportOpenAlex,
}: {
  userEmail: string;
  userFullName: string;
  activeProfileExists: boolean;
  loading: boolean;
  profileForm: ProfilePayload;
  detailsForm: ProfileDetailsPayload;
  disciplineOptions: string[];
  keywordOptions: string[];
  countryOptions: string[];
  orcidForm: { orcid_id: string; email: string; career_stage: CareerStage; disciplines: string; preferred_countries: string };
  openAlexForm: { openalex_author_id: string; orcid_id: string; max_works: number };
  highlightFields: string[];
  onProfileChange: (form: ProfilePayload) => void;
  onDetailsChange: (form: ProfileDetailsPayload) => void;
  onLoadDetails: () => void;
  onSaveProfile: (event: FormEvent) => void;
  onSaveDetails: (event: FormEvent) => void;
  onOrcidChange: (form: { orcid_id: string; email: string; career_stage: CareerStage; disciplines: string; preferred_countries: string }) => void;
  onOpenAlexChange: (form: { openalex_author_id: string; orcid_id: string; max_works: number }) => void;
  onImportOrcid: (event: FormEvent) => void;
  onImportOpenAlex: (event: FormEvent) => void;
}) {
  const [section, setSection] = useState<ProfileSection>("basics");
  const accountName = userFullName || profileForm.full_name;
  const highlights = new Set(highlightFields);

  useEffect(() => {
    if (highlightFields.some((field) => ["research_summary", "publications"].includes(field))) {
      setSection("research");
      return;
    }
    if (highlightFields.length > 0) {
      setSection("basics");
    }
  }, [highlightFields.join("|")]);

  return (
    <section className="panel">
      <div className="section-title">
        <div>
          <h2>Profile Wizard and Editor</h2>
          <p>Complete the required identity fields first, then add research evidence or import public metadata.</p>
        </div>
      </div>

      <nav className="profile-subnav" aria-label="Profile sections">
        <button type="button" className={section === "basics" ? "active" : ""} onClick={() => setSection("basics")}>
          Wizard and Editor
        </button>
        <button type="button" className={section === "research" ? "active" : ""} onClick={() => setSection("research")}>
          Research Evidence
        </button>
        <button type="button" className={section === "imports" ? "active" : ""} onClick={() => setSection("imports")}>
          Imports
        </button>
      </nav>

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
          <Field labelText="ORCID" value={profileForm.orcid_id ?? ""} onChange={(orcid_id) => onProfileChange({ ...profileForm, orcid_id })} />
          <Field labelText="Google Scholar URL" value={profileForm.google_scholar_url ?? ""} onChange={(google_scholar_url) => onProfileChange({ ...profileForm, google_scholar_url })} />
          <Field labelText="LinkedIn URL" value={profileForm.linkedin_url ?? ""} onChange={(linkedin_url) => onProfileChange({ ...profileForm, linkedin_url })} />
          <ActionButton busy={loading} className="span-2">{activeProfileExists ? "Update profile" : "Create profile"}</ActionButton>
        </form>
      )}

      {section === "research" && (
        <form className="grid-form separated" onSubmit={onSaveDetails}>
          <div className="span-2 focus-strip">
            <strong>Most important</strong>
            <span>Research summary, publications, and funding interests have the biggest effect on match explanations and advisor notes.</span>
          </div>
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
          onOrcidChange={onOrcidChange}
          onOpenAlexChange={onOpenAlexChange}
          onImportOrcid={onImportOrcid}
          onImportOpenAlex={onImportOpenAlex}
        />
      )}

      <datalist id="profile-country-options">{countryOptions.map((item) => <option value={item} key={item} />)}</datalist>
    </section>
  );
}

function fieldHighlight(highlights: Set<string>, field: string): string {
  return highlights.has(field) ? "field-highlight" : "";
}

export function ProfileImportsView({
  orcidForm,
  openAlexForm,
  onOrcidChange,
  onOpenAlexChange,
  onImportOrcid,
  onImportOpenAlex,
}: {
  orcidForm: { orcid_id: string; email: string; career_stage: CareerStage; disciplines: string; preferred_countries: string };
  openAlexForm: { openalex_author_id: string; orcid_id: string; max_works: number };
  onOrcidChange: (form: { orcid_id: string; email: string; career_stage: CareerStage; disciplines: string; preferred_countries: string }) => void;
  onOpenAlexChange: (form: { openalex_author_id: string; orcid_id: string; max_works: number }) => void;
  onImportOrcid: (event: FormEvent) => void;
  onImportOpenAlex: (event: FormEvent) => void;
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
        <Field labelText="ORCID iD" value={orcidForm.orcid_id} onChange={(orcid_id) => onOrcidChange({ ...orcidForm, orcid_id })} placeholder="0000-0000-0000-0000" />
        <Field labelText="Email" value={orcidForm.email} onChange={(email) => onOrcidChange({ ...orcidForm, email })} />
        <SelectField labelText="Career stage" value={orcidForm.career_stage} options={careerStages} onChange={(career_stage) => onOrcidChange({ ...orcidForm, career_stage })} />
        <Field labelText="Disciplines" value={orcidForm.disciplines} onChange={(disciplines) => onOrcidChange({ ...orcidForm, disciplines })} />
        <Field labelText="Preferred countries" value={orcidForm.preferred_countries} onChange={(preferred_countries) => onOrcidChange({ ...orcidForm, preferred_countries })} />
        <button className="primary span-2">Import public profile</button>
      </form>
      <form className="grid-form separated" onSubmit={onImportOpenAlex}>
        <div className="span-2">
          <div className="title-with-help">
            <h2>OpenAlex Enrichment</h2>
            <HelpTip text="OpenAlex is an open scholarly graph. Enrichment adds public publication titles and concepts to improve profile completeness and recommendation explanations." />
          </div>
          <p className="muted">Merge public concepts and publication titles into the active profile.</p>
        </div>
        <Field labelText="OpenAlex author id" value={openAlexForm.openalex_author_id} onChange={(openalex_author_id) => onOpenAlexChange({ ...openAlexForm, openalex_author_id })} placeholder="A1234567890" />
        <Field labelText="ORCID override" value={openAlexForm.orcid_id} onChange={(orcid_id) => onOpenAlexChange({ ...openAlexForm, orcid_id })} />
        <Field labelText="Max works" type="number" value={String(openAlexForm.max_works)} onChange={(max_works) => onOpenAlexChange({ ...openAlexForm, max_works: Number(max_works) })} />
        <button className="primary">Import OpenAlex</button>
      </form>
    </div>
  );
}
