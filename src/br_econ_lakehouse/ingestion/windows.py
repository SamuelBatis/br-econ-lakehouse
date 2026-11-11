"""Divisão de períodos em janelas para respeitar o limite da API SGS do BCB."""

from datetime import date, timedelta

ONE_DAY = timedelta(days=1)


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
    """Divide [start, end] em janelas contíguas de no máximo `max_years` anos.

    Ambas as pontas são inclusivas; cada janela começa no dia seguinte ao fim
    da anterior.
    """
    if start > end:
        raise ValueError(f"start ({start}) deve ser <= end ({end})")
    if max_years < 1:
        raise ValueError(f"max_years deve ser >= 1, recebido {max_years}")

    windows: list[tuple[date, date]] = []
    current = start
    while current <= end:
        window_end = min(add_years(current, max_years) - ONE_DAY, end)
        windows.append((current, window_end))
        current = window_end + ONE_DAY
    return windows
