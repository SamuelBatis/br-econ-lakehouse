"""Testes do parse_record: conversão explícita de texto da API para tipos Python."""

import re
from datetime import date
from decimal import Decimal

import pytest

from br_econ_lakehouse.ingestion.exceptions import InvalidRecordError
from br_econ_lakehouse.ingestion.models import Observation, parse_record


def test_registro_valido_vira_observation():
    raw = {"data": "02/01/2024", "valor": "4.8526"}

    assert parse_record(raw, 1) == Observation(1, date(2024, 1, 2), Decimal("4.8526"))


def test_valor_e_decimal_exato():
    # Com float: 0.1 * 3 == 0.30000000000000004
    obs = parse_record({"data": "02/01/2024", "valor": "0.1"}, 1)

    assert obs.value * 3 == Decimal("0.3")


INVALID_RECORDS = [
    pytest.param({"data": "2024-01-02", "valor": "4.85"}, id="data-iso"),
    pytest.param({"data": "31/02/2024", "valor": "4.85"}, id="data-impossivel"),
    pytest.param({"data": "02/01/2024", "valor": ""}, id="valor-vazio"),
    pytest.param({"data": "02/01/2024", "valor": "4,85"}, id="valor-com-virgula"),
    pytest.param({"data": "02/01/2024", "valor": "abc"}, id="valor-nao-numerico"),
    pytest.param({"data": "02/01/2024", "valor": "NaN"}, id="valor-nan"),
    pytest.param({"data": "02/01/2024", "valor": "Infinity"}, id="valor-infinito"),
    pytest.param({"data": "02/01/2024", "valor": None}, id="valor-null"),
    pytest.param({"data": "02/01/2024"}, id="sem-valor"),
    pytest.param({"valor": "4.85"}, id="sem-data"),
]


@pytest.mark.parametrize("raw", INVALID_RECORDS)
def test_registro_invalido_levanta_invalid_record_error(raw):
    with pytest.raises(InvalidRecordError):
        parse_record(raw, 1)


@pytest.mark.parametrize("raw", INVALID_RECORDS)
def test_mensagem_de_erro_contem_o_registro(raw):
    with pytest.raises(InvalidRecordError, match=re.escape(repr(raw))):
        parse_record(raw, 1)


def test_invalid_record_error_e_value_error():
    assert issubclass(InvalidRecordError, ValueError)
