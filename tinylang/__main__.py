"""Uso:
    python -m tinylang              abre o REPL
    python -m tinylang arquivo.tl   executa um arquivo
"""

import sys

from .errors import TinyError
from .interpreter import Interpreter, stringify


def run_file(path):
    try:
        with open(path, encoding="utf-8") as f:
            source = f.read()
    except OSError as e:
        print(f"não consegui abrir '{path}': {e.strerror}", file=sys.stderr)
        return 66
    try:
        Interpreter().run(source)
    except TinyError as e:
        print(f"erro: {e}", file=sys.stderr)
        return 1
    return 0


def repl():
    print("TinyLang REPL - digite 'sair' para fechar")
    interp = Interpreter()
    buffer = ""
    while True:
        try:
            line = input("... " if buffer else ">>> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not buffer and line.strip() == "sair":
            break

        buffer += line + "\n"
        # enquanto tiver chave aberta, continua lendo as próximas linhas
        if buffer.count("{") > buffer.count("}"):
            continue

        source = buffer.strip()
        buffer = ""
        if not source:
            continue
        # no REPL o ';' final é opcional
        if not source.endswith((";", "}")):
            source += ";"
        try:
            result = interp.run(source)
            if result is not None:
                print(stringify(result))
        except TinyError as e:
            print(f"erro: {e}")


def main():
    # no Windows o console às vezes não usa UTF-8 e os acentos saem quebrados
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    if len(sys.argv) > 2:
        print("uso: python -m tinylang [arquivo.tl]")
        return 64
    if len(sys.argv) == 2:
        return run_file(sys.argv[1])
    repl()
    return 0


if __name__ == "__main__":
    sys.exit(main())
