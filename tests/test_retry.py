"""Testes do call_with_retry. Sem HTTP: uma função falsa falha N vezes antes de dar certo."""

import pytest

from br_econ_lakehouse.ingestion.exceptions import SeriesNotFoundError, TransientSGSError
from br_econ_lakehouse.ingestion.retry import call_with_retry


class FlakyFunc:
    """Levanta `error` nas primeiras `failures` chamadas; depois retorna "ok"."""

    def __init__(self, failures: int, error: Exception | None = None) -> None:
        self.failures = failures
        self.error = error or TransientSGSError("instável")
        self.calls = 0

    def __call__(self) -> str:
        self.calls += 1
        if self.calls <= self.failures:
            raise self.error
        return "ok"


def always_fails() -> FlakyFunc:
    return FlakyFunc(failures=10**6)


def test_falha_duas_vezes_e_depois_retorna_ok():
    func = FlakyFunc(failures=2)
    esperas: list[float] = []

    assert call_with_retry(func, sleep=esperas.append) == "ok"
    assert func.calls == 3


def test_falha_sempre_levanta_apos_max_attempts():
    func = always_fails()

    with pytest.raises(TransientSGSError):
        call_with_retry(func, max_attempts=4, sleep=lambda _: None)
    assert func.calls == 4


def test_erro_nao_transitorio_nao_tenta_de_novo():
    func = FlakyFunc(failures=1, error=SeriesNotFoundError("série 999999 não existe"))
    esperas: list[float] = []

    with pytest.raises(SeriesNotFoundError):
        call_with_retry(func, sleep=esperas.append)
    assert func.calls == 1
    assert esperas == []


def test_esperas_crescem_exponencialmente_sem_esperar_apos_a_ultima():
    esperas: list[float] = []

    with pytest.raises(TransientSGSError):
        call_with_retry(always_fails(), max_attempts=4, base_delay=1, sleep=esperas.append)
    assert esperas == [1, 2, 4]


def test_max_attempts_zero_levanta_value_error():
    func = FlakyFunc(failures=0)

    with pytest.raises(ValueError):
        call_with_retry(func, max_attempts=0, sleep=lambda _: None)
    assert func.calls == 0
