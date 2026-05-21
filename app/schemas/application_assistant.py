from pydantic import BaseModel, Field


class ApplicationAssistantRequest(BaseModel):
    profile_id: int
    opportunity_id: int


class ApplicationAssistantRead(BaseModel):
    opportunity_id: int
    profile_id: int
    profile_name: str = ""
    opportunity_title: str = ""
    retrieved_context: list[str] = Field(default_factory=list)
    web_research: list[str] = Field(default_factory=list)
    application_checklist: list[str]
    motivation_letter_outline: list[str]
    research_fit_statement: str
    missing_profile_fields: list[str]
    eligibility_warnings: list[str]
    readiness_score: int = 0
    gap_analysis: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    advisor_provider: str = "deterministic"
    advisor_memo: str = ""
    exported_notes: str
