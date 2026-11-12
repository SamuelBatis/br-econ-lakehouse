"""Testes do fetch_range. Sem HTTP: um cliente falso registra chamadas e devolve o configurado."""

from datetime import date

import pytest

from br_econ_lakehouse.ingestion.exceptions import SeriesNotFoundError, TransientSGSError
from br_econ_lakehouse.ingestion.extract import fetch_range

Window = tuple[date, date]

START, END = date(2018, 1, 1), date(2024, 12, 31)
W1 = (date(2018, 1, 1), date(2020, 12, 31))
W2 = (date(2021, 1, 1), date(2023, 12, 31))
W3 = (date(2024, 1, 1), date(2024, 12, 31))


def record(d: date, valor: str) -> dict[str, str]:
    return {"data": d.strftime("%d/%m/%Y"), "valor": valor}


R1 = [record(date(2018, 1, 2), "3.30"), record(date(2020, 12, 30), "5.19")]
R2 = [record(date(2021, 1, 4), "5.26")]
R3 = [record(date(2024, 1, 2), "4.89"), record(date(2024, 12, 30), "6.19")]


class FakeClient:
    """Devolve `records[janela]`; antes disso, levanta os erros de `failures[janela]` em ordem."""

    def __init__(
        self,
        records: dict[Window, list[dict[str, str]]],
        failures: dict[Window, list[Exception]] | None = None,
    ) -> None:
        self.records = records
        self.failures = failures or {}
        self.calls: list[tuple[int, date, date]] = []

    def fetch(self, series_code: int, start: date, end: date) -> list[dict[str, str]]:
        self.calls.append((series_code, start, end))
        pending = self.failures.get((start, end))
        if pending:
            raise pending.pop(0)
        return self.records[(start, end)]


def test_sete_anos_busca_cada_janela_e_junta_em_ordem():
    client = FakeClient({W1: R1, W2: R2, W3: R3})

    result = fetch_range(client, 1, START, END, max_years=3, sleep=lambda _: None)

    assert client.calls == [(1, *W1), (1, *W2), (1, *W3)]
    assert result == R1 + R2 + R3


def test_janela_sem_dados_nao_afeta_as_outras():
    client = FakeClient({W1: R1, W2: [], W3: R3})

    result = fetch_range(client, 1, START, END, max_years=3, sleep=lambda _: None)

    assert result == R1 + R3


def test_falha_transitoria_numa_janela_e_recuperada_com_retry():
    client = FakeClient(
        {W1: R1, W2: R2, W3: R3},
        failures={W2: [TransientSGSError("503")]},
    )
    esperas: list[float] = []

    result = fetch_range(client, 1, START, END, max_years=3, sleep=esperas.append)

    assert result == R1 + R2 + R3
    assert len(esperas) == 1
    assert client.calls == [(1, *W1), (1, *W2), (1, *W2), (1, *W3)]


def test_serie_inexistente_para_na_primeira_janela():
    client = FakeClient(
        {W1: R1, W2: R2, W3: R3},
        failures={W1: [SeriesNotFoundError("série 1 não existe")]},
    )
    esperas: list[float] = []

    with pytest.raises(SeriesNotFoundError):
        fetch_range(client, 1, START, END, max_years=3, sleep=esperas.append)

    assert client.calls == [(1, *W1)]
    assert esperas == []
