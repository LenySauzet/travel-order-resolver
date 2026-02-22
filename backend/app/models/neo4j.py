from pydantic import BaseModel


class Neo4jFastestPathResponse(BaseModel):
    duration_minutes: float
    nb_steps: int
    stations: list[str]
    trips: list[str]


class Neo4jFewestStopsRoute(BaseModel):
    nb_steps: int
    nb_transfers: int
    duration_minutes: float
    stations: list[str]
    trips: list[str]


class Neo4jFewestStopsResponse(BaseModel):
    routes: list[Neo4jFewestStopsRoute]
