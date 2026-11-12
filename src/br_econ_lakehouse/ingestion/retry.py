"""Retry com backoff exponencial para erros transitórios."""

import logging
import time
from collections.abc import Callable

from br_econ_lakehouse.ingestion.exceptions import TransientSGSError

logger = logging.getLogger(__name__)


def call_with_retry[T](
    func: Callable[[], T],
    *,
    max_attempts: int = 4,
    base_delay: float = 1.0,
    retry_on: tuple[type[Exception], ...] = (TransientSGSError,),
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Chama `func`, tentando de novo nos erros de `retry_on`.

    A espera antes da tentativa N+1 é `base_delay * 2**(N-1)`: 1s, 2s, 4s...
    Não espera depois da última tentativa; o último erro sobe para o chamador.
    Erros fora de `retry_on` sobem na hora, sem nova tentativa.
    """
    if max_attempts < 1:
        raise ValueError(f"max_attempts deve ser >= 1, recebido {max_attempts}")

    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except retry_on as exc:
            if attempt == max_attempts:
                logger.error("Desistindo após %d tentativas: %s", attempt, exc)
                raise
            delay = base_delay * 2 ** (attempt - 1)
            logger.warning(
                "Tentativa %d/%d falhou (%s). Nova tentativa em %.1fs",
                attempt,
                max_attempts,
                exc,
                delay,
            )
            sleep(delay)

    raise AssertionError("inalcançável")  # pragma: no cover
