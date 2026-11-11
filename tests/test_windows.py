"""Testes de split_date_range (TDD: escritos antes da implementação).

A API SGS do Banco Central limita o intervalo por requisição, então séries
longas (ex.: dólar PTAX diário, IPCA mensal) precisam ser baixadas em janelas.
"""

from datetime import date, timedelta
from itertools import pairwise

import pytest

from br_econ_lakehouse.ingestion.windows import add_years, split_date_range


def _assert_contiguous(start: date, end: date, windows: list[tuple[date, date]]) -> None:
    """Janelas cobrem [start, end] sem buracos nem sobreposição."""
    assert windows[0][0] == start
    assert windows[-1][1] == end
    for w_start, w_end in windows:
        assert w_start <= w_end
    for (_, prev_end), (next_start, _) in pairwise(windows):
        assert next_start == prev_end + timedelta(days=1)


def test_periodo_menor_que_uma_janela_retorna_a_propria_entrada():
    # Amostra curta do dólar: alguns meses de PTAX
    start, end = date(2024, 1, 1), date(2024, 6, 30)

    assert split_date_range(start, end, max_years=3) == [(start, end)]


def test_sete_anos_com_max_tres_gera_tres_janelas():
    # IPCA de 2018 a 2024
    start, end = date(2018, 1, 1), date(2024, 12, 31)

    windows = split_date_range(start, end, max_years=3)

    assert windows == [
        (date(2018, 1, 1), date(2020, 12, 31)),
        (date(2021, 1, 1), date(2023, 12, 31)),
        (date(2024, 1, 1), date(2024, 12, 31)),
    ]


@pytest.mark.parametrize(
    ("start", "end", "max_years"),
    [
        (date(2018, 1, 1), date(2024, 12, 31), 3),
        (date(1999, 7, 15), date(2024, 3, 3), 3),   # datas "quebradas"
        (date(2015, 2, 28), date(2025, 2, 28), 2),  # atravessa anos bissextos
        (date(2000, 1, 1), date(2029, 12, 31), 10),  # limite real da SGS
    ],
)
def test_janelas_sao_contiguas_sem_buracos_nem_sobreposicao(start, end, max_years):
    windows = split_date_range(start, end, max_years=max_years)

    _assert_contiguous(start, end, windows)

    # Nenhuma data repetida e nenhuma faltando
    covered = [
        w_start + timedelta(days=i)
        for w_start, w_end in windows
        for i in range((w_end - w_start).days + 1)
    ]
    assert len(covered) == len(set(covered))
    assert len(covered) == (end - start).days + 1


def test_nenhuma_janela_excede_max_years():
    start, end = date(1999, 7, 15), date(2024, 3, 3)

    for w_start, w_end in split_date_range(start, end, max_years=3):
        limite = add_years(w_start, 3)
        assert w_end < limite


def test_start_maior_que_end_levanta_value_error():
    with pytest.raises(ValueError):
        split_date_range(date(2024, 1, 2), date(2024, 1, 1))


def test_start_igual_end_retorna_janela_de_um_dia():
    dia = date(2024, 3, 15)

    assert split_date_range(dia, dia) == [(dia, dia)]


def test_add_years_data_comum():
    assert add_years(date(2020, 7, 15), 3) == date(2023, 7, 15)


def test_add_years_29_fev_para_ano_bissexto_mantem_29():
    assert add_years(date(2020, 2, 29), 4) == date(2024, 2, 29)


def test_add_years_29_fev_para_ano_nao_bissexto_vira_28():
    assert add_years(date(2020, 2, 29), 3) == date(2023, 2, 28)
