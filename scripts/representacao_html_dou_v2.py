"""Representação explícita v2: evita linhas vazias CommonMark sem alterar o DOM textual.

Preserva o modo v1 por delegação byte a byte. A única transformação
v2 adicional é LF -> &#10; em linhas vazias comprovadamente textuais. O parser
HTML recompõe o mesmo LF; tags, atributos e demais caracteres ficam intactos.
"""
from html.parser import HTMLParser
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import representacao_html_dou as v1

MODO_HTML_NATIVO_V2 = "html-nativo-texto-dou-v2-lf-entidade"
SENSIVEIS = {"pre", "textarea", "xmp", "plaintext", "listing"}


class _SemNewlinesSensiveis(v1._Campo):
    def handle_starttag(self, tag, attrs):
        super().handle_starttag(tag, attrs)
        if tag in SENSIVEIS:
            raise ValueError("elemento sensível a newline exige revisão")
        for chave, valor in attrs:
            if chave == "style":
                for nome, conteudo in re.findall(r"([\w-]+)\s*:\s*([^;]*)", valor or ""):
                    if nome.lower() in {"white-space", "white-space-collapse", "text-space-collapse"}:
                        if nome.lower() != "white-space" or not re.fullmatch(
                            r"\s*(?:normal|nowrap)\s*(?:!important\s*)?", conteudo, re.I
                        ):
                            raise ValueError("CSS sensível a newline exige revisão")


class _DOM(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.eventos = []

    def handle_starttag(self, tag, attrs):
        self.eventos.append(("abertura", self.get_starttag_text()))

    def handle_startendtag(self, tag, attrs):
        self.eventos.append(("autocontida", self.get_starttag_text()))

    def handle_endtag(self, tag):
        self.eventos.append(("fechamento", tag))

    def handle_data(self, data):
        if self.eventos and self.eventos[-1][0] == "texto":
            self.eventos[-1] = ("texto", self.eventos[-1][1] + data)
        else:
            self.eventos.append(("texto", data))


def assinatura_dom(texto):
    parser = _DOM()
    parser.feed(texto)
    parser.close()
    return parser.eventos


def representar_fragmento(fragmento, *, modo):
    if modo == v1.MODO_HTML_NATIVO:
        return v1.representar_fragmento(fragmento, modo=modo)
    if modo != MODO_HTML_NATIVO_V2:
        raise ValueError("modo de representação HTML desconhecido")
    # Todos os gates de ativos, ocultos, tachados, visuais e CSS do v1 continuam.
    texto = v1.representar_fragmento(fragmento, modo=v1.MODO_HTML_NATIVO)
    parser = _SemNewlinesSensiveis(texto)
    parser.feed(texto)
    parser.close()
    trocas = []
    for match in re.finditer(r"(?m)^[ \t]*\n", texto):
        inicio = match.end() - 1
        if not any(a <= inicio < b for a, b in parser.textos):
            raise ValueError("linha vazia em tag/atributo exige revisão")
        trocas.append(inicio)
    saida = texto
    for inicio in reversed(trocas):
        saida = saida[:inicio] + "&#10;" + saida[inicio + 1:]
    if assinatura_dom(saida) != assinatura_dom(texto):
        raise ValueError("DOM/texto/atributos divergiram")
    return saida
