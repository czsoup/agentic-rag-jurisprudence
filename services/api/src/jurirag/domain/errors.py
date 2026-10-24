"""Erreurs métier. LLM, index et outils."""


class JuriragError(Exception):
    """Racine des erreurs du projet."""


class LLMError(JuriragError):
    """Erreur renvoyée par le serveur LLM."""


class LLMUnavailableError(LLMError):
    """Serveur injoignable ou modèle absent."""


class LLMTimeoutError(LLMError):
    """Le serveur n'a pas répondu à temps."""


class LLMGenerationError(LLMError):
    """Génération interrompue ou réponse inexploitable."""


class IndexNotReadyError(JuriragError):
    """L'index n'a pas été construit (lancer `jurirag-build`)."""


class CaseNotFoundError(JuriragError):
    """Identifiant de décision inconnu de l'index."""
