from pydantic import BaseModel, Field

from app.schemas.auth import UserPublicResponse


class UserUpdateRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)


class UserProfileResponse(UserPublicResponse):
    pass
