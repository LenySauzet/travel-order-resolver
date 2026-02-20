"""Station model."""

from pydantic import BaseModel


class Station(BaseModel):
    """A train station."""

    id: int
    name: str
    lat: float | None = None
    lon: float | None = None
