import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import diskcache
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Ensure src/ is on path so `import functions` works in services
_SRC_DIR = Path(__file__).parent.parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from app.routes import index, simulate  # noqa: E402 — after sys.path setup
from config import load_config  # noqa: E402
from logger_config import get_logger  # noqa: E402

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = load_config()
    logger = get_logger(level=cfg.log_level)

    os.makedirs(cfg.cache_dir, exist_ok=True)
    cache = diskcache.Cache(cfg.cache_dir, size_limit=500_000_000)

    app.state.config = cfg
    app.state.cache = cache
    app.state.templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))
    app.state.logger = logger

    logger.info("yh-stocks started", extra={"cache_dir": cfg.cache_dir, "port": cfg.port})
    yield

    cache.close()
    logger.info("yh-stocks stopped")


def create_app() -> FastAPI:
    app = FastAPI(title="yh-stocks", docs_url=None, redoc_url=None)
    app.router.lifespan_context = lifespan

    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
    app.include_router(index.router)
    app.include_router(simulate.router)

    return app


app = create_app()
