class TinyError(Exception):
    """Erro base da linguagem. Guarda a linha para mostrar mensagens melhores."""

    def __init__(self, message, line=None):
        self.message = message
        self.line = line
        prefix = f"[linha {line}] " if line is not None else ""
        super().__init__(prefix + message)


class LexError(TinyError):
    pass


class ParseError(TinyError):
    pass


class RuntimeErr(TinyError):
    pass
