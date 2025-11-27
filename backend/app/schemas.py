from pydantic import BaseModel, Field


class WorldCreateRequest(BaseModel):
    description: str = Field(min_length=3, max_length=1200)
    player_name: str | None = Field(default=None, max_length=80)


class WorldRandomRequest(BaseModel):
    player_name: str | None = Field(default=None, max_length=80)


class WorldResponse(BaseModel):
    world_description: str
    scenario_text: str
    hints_for_image: str | None = None
    player_name: str | None = None


class ErrorResponse(BaseModel):
    detail: str
