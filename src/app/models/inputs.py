from typing import Literal

from pydantic import BaseModel, Field


class SimulationRequest(BaseModel):
    search_type: Literal["stock", "country", "index"]
    name: str
    apport_initial: float = Field(gt=0)
    versement_mensuel: float = Field(ge=0)
    horizon_years: int = Field(ge=1, le=50)
    account_type: Literal["CTO", "PEA", "AV", "ALL"]
    courtage_pct: float = Field(ge=0.0, le=5.0, default=0.1)
    frais_garde_pct: float = Field(ge=0.0, le=2.0, default=0.1)
    frais_gestion_av_pct: float = Field(ge=0.0, le=2.0, default=0.75)
    is_couple: bool = False
    avg_len: int = Field(ge=1, le=20, default=10)
