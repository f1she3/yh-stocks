from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pytickersymbols import PyTickerSymbols

router = APIRouter()
_stock_data = PyTickerSymbols()

_COUNTRIES: list[str] = sorted(_stock_data.get_all_countries())
_INDICES: list[str] = sorted(_stock_data.get_all_indices())


def _get_templates(request: Request) -> Jinja2Templates:
    return request.app.state.templates


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    templates = _get_templates(request)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "countries": _COUNTRIES,
            "indices": _INDICES,
        },
    )


@router.get("/healthz")
async def health() -> dict:
    return {"status": "ok"}
