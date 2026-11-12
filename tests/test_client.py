"""Testes do SGSClient. Todo HTTP é mockado com respx: nenhuma chamada real de rede."""

from datetime import date

import httpx
import pytest
import respx

from br_econ_lakehouse.ingestion.client import SGSClient

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
def test_serie_inexistente_404_texto_levanta_erro(client):
    url = f"{BASE_URL}/bcdata.sgs.999999/dados"
    respx.get(url).mock(return_value=httpx.Response(404, text="A serie nao existe!"))

    with pytest.raises(httpx.HTTPStatusError):
        client.fetch(999999, *FEV_2024)
