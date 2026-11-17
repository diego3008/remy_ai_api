from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Response models built directly from SQLAlchemy instances."""

    model_config = ConfigDict(from_attributes=True)
