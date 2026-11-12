"""Cliente HTTP para a API SGS do Banco Central."""

import logging
from datetime import date
from types import TracebackType
from typing import Self

import httpx

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.bcb.gov.br/dados/serie"
SGS_DATE_FORMAT = "%d/%m/%Y"
NO_DATA_MARKER = "Value(s) not found"


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
        response = self._client.get(f"/bcdata.sgs.{series_code}/dados", params=params)

        if _is_no_data(response):
            logger.info("Série %s sem dados entre %s e %s", series_code, start, end)
            return []

        response.raise_for_status()
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
