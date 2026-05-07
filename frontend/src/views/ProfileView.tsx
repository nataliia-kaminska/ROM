import type { FormEvent } from "react";
import type { ProfileDetailsPayload, ProfilePayload } from "../api";
import type { CareerStage, OpportunityType } from "../types";
import { careerStages, opportunityTypes } from "../constants";
import { ActionButton, Field, HelpTip, MultiValueField, SelectField, TextArea } from "../components/ui";

export function ProfileView({
  userEmail,
  activeProfileExists,
  loading,
  profileForm,
  detailsForm,
  keywordOptions,
  countryOptions,
  onProfileChange,
  onDetailsChange,
  onLoadDetails,
  onSaveProfile,
  onSaveDetails,
}: {
  userEmail: string;
  activeProfileExists: boolean;
  loading: boolean;
  profileForm: ProfilePayload;
  detailsForm: ProfileDetailsPayload;
  keywordOptions: string[];
  countryOptions: string[];
  onProfileChange: (form: ProfilePayload) => void;
  onDetailsChange: (form: ProfileDetailsPayload) => void;
  onLoadDetails: () => void;
  onSaveProfile: (event: FormEvent) => void;
  onSaveDetails: (event: FormEvent) => void;
}) {
  return (
    <>
      <section className="panel">
        <div className="section-title">
          <div>
            <h2>Profile Wizard and Editor</h2>
            <p>Create the profile used by recommendations, then enrich matching preferences.</p>
          </div>
          <button className="secondary" onClick={onLoadDetails}>
            Load details
          </button>
        </div>
        <form className="grid-form" onSubmit={onSaveProfile}>
          <Field labelText="Full name" value={profileForm.full_name} onChange={(full_name) => onProfileChange({ ...profileForm, full_name })} />
          <Field labelText="Account email" value={userEmail} disabled onChange={() => undefined} title="Profile email is linked to the signed-in account." />
          <SelectField labelText="Career stage" value={profileForm.career_stage} options={careerStages} onChange={(career_stage) => onProfileChange({ ...profileForm, career_stage })} />
          <Field labelText="Country" value={profileForm.country ?? ""} list="country-options" placeholder="Use countries visible in the feed" onChange={(country) => onProfileChange({ ...profileForm, country })} />
          <MultiValueField
            labelText="Disciplines"
            values={profileForm.disciplines}
            placeholder="Type a discipline, then Enter"
            help="Used for semantic matching, eligibility scoring, and match explanations."
            suggestions={keywordOptions}
            onChange={(disciplines) => onProfileChange({ ...profileForm, disciplines })}
          />
          <MultiValueField
            labelText="Keywords"
            values={profileForm.keywords}
            placeholder="Type a keyword, then Enter"
            help="Used to find topic overlap with opportunity summaries, keywords, and source metadata."
            suggestions={keywordOptions}
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
        <form className="grid-form separated" onSubmit={onSaveDetails}>
          <TextArea labelText="Research summary" value={detailsForm.research_summary} onChange={(research_summary) => onDetailsChange({ ...detailsForm, research_summary })} />
          <MultiValueField labelText="Publications" values={detailsForm.publications} placeholder="Paste a title or DOI, then Enter" help="Used by readiness scoring and the assistant to identify strengths and publication gaps." onChange={(publications) => onDetailsChange({ ...detailsForm, publications })} />
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
      </section>
    </>
  );
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
    <section className="panel">
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
    </section>
  );
}
