from dataclasses import dataclass


@dataclass
class KpiRow:
    name: str
    symbol: str
    roi_pct: float | None
    avg_roi_pct: float | None
    apy_pct: float | None
    avg_apy_pct: float | None
