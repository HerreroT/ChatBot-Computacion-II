from __future__ import annotations

import logging

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

logger = logging.getLogger(__name__)


def setup_metrics(app: FastAPI, *, enabled: bool = True) -> None:
    if not enabled:
        logger.info("Metrics disabled by configuration.")
        return

    instrumentator = Instrumentator().instrument(app)
    instrumentator.expose(
        app,
        include_in_schema=False,
        should_gzip=True,
    )
