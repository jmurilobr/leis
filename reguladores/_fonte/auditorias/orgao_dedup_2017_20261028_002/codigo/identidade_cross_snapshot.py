import re
types = {'lei': 'lei', 'lei ordinaria': 'lei', 'lei complementar': 'lc', 'medida provisoria': 'mp', 'decreto': 'dec', 'decreto numerado': 'dec', 'decreto-lei': 'del', 'decreto lei': 'del', 'decreto legislativo': 'dlg', 'decreto do poder legislativo': 'dlg', 'emenda constitucional': 'ec', 'emenda constitucional de revisao': 'ecr', 'lei delegada': 'ldl', 'lei constitucional': 'lct'}
dirs = {'leis-ordinarias': ('lei', 'lei'), 'leis-complementares': ('lc', 'lcp'), 'medidas-provisorias': ('mp', 'mpv'), 'decretos': ('dec', 'dec'), 'decretos-lei': ('del', 'del'), 'decretos-legislativos': ('dlg', None), 'emendas-constitucionais': ('ec', None), 'leis-delegadas': ('ldl', 'ldl'), 'leis-constitucionais': ('lct', 'lct')}

def number(s):
    s = str(s).strip()
    m = re.fullmatch('(\\d+(?:\\.\\d{3})*)(-[a-zA-Z0-9]+)?', s)
    return m[1].replace('.', '') + (m[2] or '').upper() if m else None
ambiguous = [('ministerio da cultura', 'comando da aeronautica'), ('ministerio da cultura', 'fundo nacional de desenvolvimento da educacao'), ('ministerio do desenvolvimento social', 'instituto chico mendes de conservacao da biodiversidade'), ('ministerio de minas e energia', 'instituto nacional do seguro social'), ('ministerio da integracao nacional', 'secretaria de fomento e incentivo a cultura')]
