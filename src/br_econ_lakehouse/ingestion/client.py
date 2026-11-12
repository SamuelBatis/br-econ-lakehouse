"""Cliente HTTP para a API SGS do Banco Central."""

import logging
from datetime import date
from types import TracebackType
from typing import Self

import httpx

from br_econ_lakehouse.ingestion.exceptions import (
    SeriesNotFoundError,
    SGSRequestError,
    TransientSGSError,
)

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.bcb.gov.br/dados/serie"
SGS_DATE_FORMAT = "%d/%m/%Y"
NO_DATA_MARKER = "Value(s) not found"
SERIES_NOT_FOUND_MARKER = "A serie nao existe"
TRANSIENT_STATUS = {429}


class SGSClient:
    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = 30.0) -> None:
        self._client = httpx.Client(base_url=base_url, timeout=timeout)

    def fetch(self, series_code: int, start: date, end: date) -> list[dict[str, str]]:
        """Busca uma única janela. Retorna os registros brutos da API."""
        params = {
            "formato": "json",
            "dataInicial": start.strftime(SGS_DATE_FORMAT),
            "dataFinal": end.strftime(SGS_DATE_FORMAT),
        }
        try:
            response = self._client.get(f"/bcdata.sgs.{series_code}/dados", params=params)
        except httpx.TimeoutException as exc:
            raise TransientSGSError(
                f"Timeout ao buscar série {series_code} ({start} a {end})"
            ) from exc

        if _is_no_data(response):
            logger.info("Série %s sem dados entre %s e %s", series_code, start, end)
            return []

        _raise_for_status(response, series_code)
        return response.json()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()


def _is_no_data(response: httpx.Response) -> bool:
    """404 com 'Value(s) not found' = período sem dados (não é erro)."""
    return response.status_code == 404 and NO_DATA_MARKER in response.text


def _raise_for_status(response: httpx.Response, series_code: int) -> None:
    """Traduz status HTTP de erro para a exceção SGS correspondente."""
    status = response.status_code
    if status < 400:
        return

    detail = f"HTTP {status} ao buscar série {series_code}: {response.text[:200]!r}"
    if status == 404 and SERIES_NOT_FOUND_MARKER in response.text:
        raise SeriesNotFoundError(f"Série {series_code} não existe na API SGS")
    if status >= 500 or status in TRANSIENT_STATUS:
        raise TransientSGSError(detail)
    raise SGSRequestError(detail)
