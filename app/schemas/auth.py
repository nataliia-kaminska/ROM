from pydantic import BaseModel, EmailStr, Field, field_validator

from app.domain.enums import UserRole


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=3, max_length=120)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        normalized = " ".join(value.strip().split())
        if " " not in normalized:
            raise ValueError("Full name must include at least first and last name")
        if not all(character.isalpha() or character in {" ", "-", "'"} for character in normalized):
            raise ValueError("Full name can contain only letters, spaces, hyphens, and apostrophes")
        return normalized


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserVerifyEmail(BaseModel):
    token: str = Field(..., min_length=20)


class AuthProviderConfigRead(BaseModel):
    orcid_oauth_enabled: bool


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    email_verified: bool
    auth_provider: str = "local"
    orcid_id: str | None = None
    password_login_enabled: bool = True

    model_config = {"from_attributes": True}


class UserRegisterRead(BaseModel):
    message: str
    email: EmailStr
    access_token: str | None = None
    token_type: str = "bearer"
    user: UserRead | None = None


class TokenRead(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
