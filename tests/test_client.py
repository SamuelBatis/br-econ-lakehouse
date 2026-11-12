"""Testes do SGSClient. Todo HTTP é mockado com respx: nenhuma chamada real de rede."""

from datetime import date

import httpx
import pytest
import respx

from br_econ_lakehouse.ingestion.client import SGSClient
from br_econ_lakehouse.ingestion.exceptions import (
    SeriesNotFoundError,
    SGSRequestError,
    TransientSGSError,
)

BASE_URL = "https://api.bcb.gov.br/dados/serie"
DOLAR_URL = f"{BASE_URL}/bcdata.sgs.1/dados"
FEV_2024 = (date(2024, 2, 1), date(2024, 2, 29))


@pytest.fixture
def client():
    with SGSClient(base_url=BASE_URL) as c:
        yield c


@respx.mock
def test_monta_url_com_codigo_da_serie_e_datas_dd_mm_aaaa(client):
    route = respx.get(DOLAR_URL).mock(return_value=httpx.Response(200, json=[]))

    client.fetch(1, *FEV_2024)

    request = route.calls.last.request
    assert request.url.path == "/dados/serie/bcdata.sgs.1/dados"
    assert dict(request.url.params) == {
        "formato": "json",
        "dataInicial": "01/02/2024",
        "dataFinal": "29/02/2024",
    }


@respx.mock
def test_retorna_registros_como_vieram_da_api(client):
    registros = [
        {"data": "01/02/2024", "valor": "4.9535"},
        {"data": "02/02/2024", "valor": "4.9259"},
    ]
    respx.get(DOLAR_URL).mock(return_value=httpx.Response(200, json=registros))

    assert client.fetch(1, *FEV_2024) == registros


@respx.mock
def test_resposta_lista_vazia_retorna_lista_vazia(client):
    respx.get(DOLAR_URL).mock(return_value=httpx.Response(200, json=[]))

    assert client.fetch(1, *FEV_2024) == []


@respx.mock
def test_periodo_sem_dados_404_value_not_found_retorna_lista_vazia(client):
    corpo = {
        "erro": {
            "statusCode": 404,
            "detail": "br.gov.bcb.pec.sgs.comum.excecoes.SGSNegocioException: Value(s) not found",
        }
    }
    respx.get(DOLAR_URL).mock(return_value=httpx.Response(404, json=corpo))

    assert client.fetch(1, *FEV_2024) == []


@respx.mock
def test_serie_inexistente_levanta_series_not_found_com_codigo_na_mensagem(client):
    url = f"{BASE_URL}/bcdata.sgs.999999/dados"
    respx.get(url).mock(return_value=httpx.Response(404, text="A serie nao existe!"))

    with pytest.raises(SeriesNotFoundError, match="999999"):
        client.fetch(999999, *FEV_2024)


@respx.mock
def test_http_406_levanta_sgs_request_error(client):
    respx.get(DOLAR_URL).mock(return_value=httpx.Response(406))

    with pytest.raises(SGSRequestError):
        client.fetch(1, *FEV_2024)


@respx.mock
def test_404_sem_mensagem_conhecida_levanta_sgs_request_error(client):
    # Ex.: base_url errada. Não é "série inexistente" nem "sem dados".
    respx.get(DOLAR_URL).mock(return_value=httpx.Response(404, text="Not Found"))

    with pytest.raises(SGSRequestError):
        client.fetch(1, *FEV_2024)


@respx.mock
@pytest.mark.parametrize("status", [500, 503])
def test_http_5xx_levanta_transient_error(client, status):
    respx.get(DOLAR_URL).mock(return_value=httpx.Response(status))

    with pytest.raises(TransientSGSError):
        client.fetch(1, *FEV_2024)


@respx.mock
def test_http_429_levanta_transient_error(client):
    respx.get(DOLAR_URL).mock(return_value=httpx.Response(429))

    with pytest.raises(TransientSGSError):
        client.fetch(1, *FEV_2024)


@respx.mock
def test_timeout_levanta_transient_error(client):
    respx.get(DOLAR_URL).mock(side_effect=httpx.ReadTimeout("timeout"))

    with pytest.raises(TransientSGSError):
        client.fetch(1, *FEV_2024)
