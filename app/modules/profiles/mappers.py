from app.db.models import ResearcherProfile, ResearcherProfileDetails
from app.schemas.profile_details import ResearcherProfileDetailsRead
from app.schemas.profiles import ResearcherProfileRead
from app.services.serialization import unpack_list


def to_profile_read(profile: ResearcherProfile) -> ResearcherProfileRead:
    return ResearcherProfileRead(
        id=profile.id,
        user_id=profile.user_id,
        full_name=profile.full_name,
        email=profile.email,
        career_stage=profile.career_stage,
        country=profile.country,
        disciplines=unpack_list(profile.disciplines),
        keywords=unpack_list(profile.keywords),
        preferred_countries=unpack_list(profile.preferred_countries),
        orcid_id=profile.orcid_id,
        google_scholar_url=profile.google_scholar_url,
        linkedin_url=profile.linkedin_url,
    )


def to_profile_details_read(details: ResearcherProfileDetails) -> ResearcherProfileDetailsRead:
    return ResearcherProfileDetailsRead(
        id=details.id,
        profile_id=details.profile_id,
        research_summary=details.research_summary,
        publications=unpack_list(details.publications),
        degrees=unpack_list(details.degrees),
        languages=unpack_list(details.languages),
        funding_interests=unpack_list(details.funding_interests),
        unavailable_countries=unpack_list(details.unavailable_countries),
        preferred_opportunity_types=unpack_list(details.preferred_opportunity_types),
        min_duration_months=details.min_duration_months,
        max_duration_months=details.max_duration_months,
    )
