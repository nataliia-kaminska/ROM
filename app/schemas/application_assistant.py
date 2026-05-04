from pydantic import BaseModel


class ApplicationAssistantRequest(BaseModel):
    profile_id: int
    opportunity_id: int


class ApplicationAssistantRead(BaseModel):
    opportunity_id: int
    profile_id: int
    application_checklist: list[str]
    motivation_letter_outline: list[str]
    research_fit_statement: str
    missing_profile_fields: list[str]
    eligibility_warnings: list[str]
    readiness_score: int = 0
    gap_analysis: list[str] = []
    strengths: list[str] = []
    exported_notes: str
