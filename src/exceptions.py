"""Hierarquia de exceções do robô (recuperável / negócio / fatal)."""


class BotError(Exception):
    """Base de todos os erros do robô."""


class RecoverableError(BotError):
    """Falha transitória: tentar de novo faz sentido."""


class BusinessError(BotError):
    """Falha de um item: registra e segue para o próximo."""


class InvalidInputError(BusinessError):
    """Linha da planilha que não passa na validação."""


class FatalError(BotError):
    """O robô não consegue continuar."""


class SystemUnavailableError(FatalError):
    """rpachallenge.com fora do ar ou sem responder."""


class ChallengeFailedError(FatalError):
    """O desafio terminou abaixo da taxa de acerto esperada."""
