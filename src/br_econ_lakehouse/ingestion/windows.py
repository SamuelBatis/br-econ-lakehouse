"""Divisão de períodos em janelas para respeitar o limite da API SGS do BCB."""

from datetime import date


def add_years(d: date, years: int) -> date:
    """Soma `years` anos a `d`.

    Se o resultado cair em 29/02 de um ano não bissexto, retorna 28/02.
    """
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        # Só acontece com 29/02 indo para um ano não bissexto
        return d.replace(year=d.year + years, day=28)


def split_date_range(start: date, end: date, max_years: int = 3) -> list[tuple[date, date]]:
    raise NotImplementedError
