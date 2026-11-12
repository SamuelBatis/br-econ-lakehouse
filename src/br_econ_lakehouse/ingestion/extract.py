"""Extração de um período completo: fatia em janelas e busca cada uma com retry."""

import logging
import time
from collections.abc import Callable
from datetime import date

from br_econ_lakehouse.ingestion.client import SGSClient
from br_econ_lakehouse.ingestion.retry import call_with_retry
from br_econ_lakehouse.ingestion.windows import split_date_range

logger = logging.getLogger(__name__)


def fetch_range(
    client: SGSClient,
    series_code: int,
    start: date,
    end: date,
    *,
    max_years: int = 3,
    sleep: Callable[[float], None] = time.sleep,
) -> list[dict[str, str]]:
    """Busca [start, end] janela por janela, com retry, e junta os registros em ordem."""
    records: list[dict[str, str]] = []
    for w_start, w_end in split_date_range(start, end, max_years=max_years):
        window_records = call_with_retry(
            lambda s=w_start, e=w_end: client.fetch(series_code, s, e),
            sleep=sleep,
        )
        logger.info(
            "Série %s: %d registros entre %s e %s",
            series_code,
            len(window_records),
            w_start,
            w_end,
        )
        records.extend(window_records)
    return records
