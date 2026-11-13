"""Erros do cliente SGS, classificados pelo que o chamador deve fazer com eles."""


class SGSError(Exception):
    """Base de todos os erros do cliente SGS."""


class SeriesNotFoundError(SGSError):
    """Série não existe (erro de configuração, não adianta tentar de novo)."""


class SGSRequestError(SGSError):
    """Requisição inválida, ex.: 406 por janela grande demais (não adianta tentar de novo)."""


class TransientSGSError(SGSError):
    """Erro temporário: timeout, 5xx, 429 (vale tentar de novo)."""


class InvalidRecordError(ValueError):
    """Registro da API com formato inválido (problema do dado, não da comunicação)."""
