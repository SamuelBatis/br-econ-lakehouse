"""Parse e validação dos registros brutos da API SGS."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from br_econ_lakehouse.ingestion.exceptions import InvalidRecordError

SGS_DATE_FORMAT = "%d/%m/%Y"


@dataclass(frozen=True, slots=True)
class Observation:
    series_code: int
    ref_date: date
    value: Decimal


def parse_record(raw: dict[str, str], series_code: int) -> Observation:
    """Converte um registro bruto da API. Levanta InvalidRecordError se for inválido."""
    try:
        ref_date = _parse_date(raw["data"])
        value = _parse_value(raw["valor"])
    except (KeyError, ValueError, TypeError) as exc:
        raise InvalidRecordError(
            f"Registro inválido da série {series_code}: {raw!r} ({_reason(exc)})"
        ) from exc
    return Observation(series_code=series_code, ref_date=ref_date, value=value)


def _parse_date(text: str) -> date:
    return datetime.strptime(text, SGS_DATE_FORMAT).date()


def _parse_value(text: str) -> Decimal:
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise ValueError(f"valor não numérico: {text!r}") from None
    if not value.is_finite():
        raise ValueError(f"valor não finito: {text!r}")
    return value


def _reason(exc: Exception) -> str:
    if isinstance(exc, KeyError):
        return f"chave ausente: {exc}"
    return str(exc)
