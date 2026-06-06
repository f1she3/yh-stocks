from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from app.charts import kpi_comparison, projection
from app.models.inputs import SimulationRequest
from app.services import simulation_service, stock_service
from app.services.simulation_service import SimulationParams, portfolio_avg_apy, portfolio_cagr

router = APIRouter()


def _form_to_request(
    search_type: str,
    name: str,
    apport_initial: float,
    versement_mensuel: float,
    horizon_years: int,
    account_type: str,
    courtage_pct: float,
    frais_garde_pct: float,
    frais_gestion_av_pct: float,
    is_couple: bool,
    avg_len: int,
) -> SimulationRequest:
    return SimulationRequest(
        search_type=search_type,
        name=name,
        apport_initial=apport_initial,
        versement_mensuel=versement_mensuel,
        horizon_years=horizon_years,
        account_type=account_type,
        courtage_pct=courtage_pct / 100,
        frais_garde_pct=frais_garde_pct / 100,
        frais_gestion_av_pct=frais_gestion_av_pct / 100,
        is_couple=is_couple,
        avg_len=avg_len,
    )


@router.post("/simulate", response_class=HTMLResponse)
async def simulate(
    request: Request,
    search_type: Annotated[str, Form()],
    name: Annotated[str, Form()],
    apport_initial: Annotated[float, Form()],
    versement_mensuel: Annotated[float, Form()],
    horizon_years: Annotated[int, Form()],
    account_type: Annotated[str, Form()],
    courtage_pct: Annotated[float, Form()] = 0.1,
    frais_garde_pct: Annotated[float, Form()] = 0.1,
    frais_gestion_av_pct: Annotated[float, Form()] = 0.75,
    is_couple: Annotated[bool, Form()] = False,
    avg_len: Annotated[int, Form()] = 10,
) -> HTMLResponse:
    templates = request.app.state.templates
    cfg = request.app.state.config
    cache = request.app.state.cache

    try:
        sim_req = _form_to_request(
            search_type, name, apport_initial, versement_mensuel,
            horizon_years, account_type, courtage_pct, frais_garde_pct,
            frais_gestion_av_pct, is_couple, avg_len,
        )

        kpi_rows, roi_series, apy_series = stock_service.get_kpis(
            name=sim_req.name,
            search_type=sim_req.search_type,
            avg_len=sim_req.avg_len,
            cache=cache,
            cache_ttl=cfg.cache_ttl,
            yf_timeout=cfg.yf_timeout,
        )

        cagr = portfolio_cagr(roi_series)
        avg_apy = portfolio_avg_apy(apy_series)

        params = SimulationParams(
            apport_initial=sim_req.apport_initial,
            versement_mensuel=sim_req.versement_mensuel,
            horizon_years=sim_req.horizon_years,
            r_annual=cagr,
            avg_apy=avg_apy,
            courtage_pct=sim_req.courtage_pct,
            frais_garde_pct=sim_req.frais_garde_pct,
            frais_gestion_av_pct=sim_req.frais_gestion_av_pct,
            is_couple=sim_req.is_couple,
        )
        sim_result = simulation_service.run_simulation(params)

        chart_kpi = kpi_comparison.build(kpi_rows)
        chart_proj = projection.build(sim_result)

        symbols = [r.symbol for r in kpi_rows]

        return templates.TemplateResponse(
            request,
            "partials/results.html",
            {
                "kpi_rows": kpi_rows,
                "sim": sim_result,
                "chart_kpi": chart_kpi,
                "chart_proj": chart_proj,
                "symbols": symbols,
                "horizon_years": sim_req.horizon_years,
            },
        )

    except Exception as exc:
        return templates.TemplateResponse(
            request,
            "partials/error.html",
            {"error": str(exc)},
            status_code=500,
        )
