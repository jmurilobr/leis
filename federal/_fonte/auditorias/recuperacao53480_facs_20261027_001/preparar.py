"""Prepara candidato privado; nenhuma escrita em destinos canônicos."""
import hashlib, json, subprocess
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
def sha(b): return hashlib.sha256(b).hexdigest()
def rel(p): return str(p.relative_to(ROOT))
def info(p): return {"path": rel(p), "sha256": sha(p.read_bytes()), "bytes": p.stat().st_size}
def save(name, obj):
    p = BASE / name
    assert not p.exists(), p
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
    return p

canonical = 'federal/decretos/1964/dec-53480-1964-01-23.md'
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
old = subprocess.check_output(['git', 'show', f'{head}:{canonical}'], cwd=ROOT)
assert sha(old) == '60b9c427d89bf0df452e33e2ca802b71e0021ad695cb4f1dae364455577ddf2a'
assert (ROOT / canonical).read_bytes() == old
pre = BASE / 'preimagem_HEAD.md'
assert not pre.exists()
pre.write_bytes(old)
pdf = ROOT / 'federal/_fonte/auditorias/clbr_modelos_20261021_004/1964.pdf'
assert sha(pdf.read_bytes()) == 'd82ed4da9c496455ddb7694d7e71f829a1b4ba322e8a5fe688c446ccca722a00'
proof = ROOT / 'federal/_provas_modelo53480_clbr_20261021_009'
url = 'https://bd.camara.leg.br/bd/bitstreams/2326a317-d511-4f14-9907-6b041487e7ae/download'
assets = []
def asset(name, target, page, label, crop=None):
    p = BASE / 'render' / name
    assert p.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    assets.append({**info(p), 'destino': 'federal/anexos/decretos/1964/dec-53480-1964-01-23-' + target + '.png', 'pagina_pdf': page, 'rotulo': label, 'dpi': 300, 'recorte_pixels': crop, 'operacoes': 'Render PDF pelo Poppler; somente recorte quando explicitado; sem edição posterior de pixels.'})
asset('p81-esquerda-ato.png', 'p81-coluna-esquerda', 135, 'Página 81, coluna esquerda: da epígrafe ao início do artigo 1º', [200, 1380, 710, 1138])
asset('p81-direita-ato.png', 'p81-coluna-direita', 135, 'Página 81, coluna direita: continuação do artigo 1º', [900, 150, 800, 2300])
for page in range(136, 145):
    asset(f'pagina-{page:04}.png', f'p{page-54}', page, f'Página {page-54}')
for n, page in enumerate(range(145, 154), 1):
    asset(f'pagina-{page:04}.png', f'mapa{n}', page, f'Mapa {n}, folha não numerada com referência impressa à página 90')
assert len(assets) == 20
note = ('Edição fac-símile integral da CLBR de 1964, volume II, páginas 81–90 e nove folhas de mapas. '
        'O cabeçalho da página 81 traz literalmente 53.490. O índice da mesma edição identifica 53.480, de 23/01/1964, com esta ementa e página 81; '
        'o índice também registra 53.490 separadamente na página 100. A identidade 53.480 é corroborada pelo índice e metadados do Senado e pela publicação original da Câmara. '
        'A divergência foi preservada sem atribuição de causa e sem criar alias. O índice informa publicação em 30/01/1964 e retificação em 06/02/1964; '
        'esta reprodução corresponde à edição CLBR, sem certificar o conteúdo daquela retificação. A transcrição anterior do Normas foi arquivada integralmente. '
        'O artigo 7º desta edição contém 1.095 (mil e noventa e cinco), enquanto a transcrição anterior contém 1.095 mil (mil e noventa e cinco); não se mesclaram os corpos.')
header = old.decode().split('---\n', 2)[1]
lines = []
for line in header.rstrip().splitlines():
    if line.startswith('fonte:'): line = 'fonte: ' + json.dumps(url)
    elif line.startswith('baixado_em:'): line = 'baixado_em: 2026-10-21'
    elif line.startswith('versao_texto:'): line = 'versao_texto: "edição CLBR integral em fac-símile"'
    lines.append(line)
lines += ['fonte_texto_anterior: "https://normas.leg.br/?urn=urn:lex:br:federal:decreto:1964-01-23;53480"',
          'sha256_pdf_fonte: ' + json.dumps(sha(pdf.read_bytes())),
          'nota_editorial_fonte: ' + json.dumps(note, ensure_ascii=False)]
body = '\n# Decreto nº 53.480 de 23/01/1964\n\n'
body += 'Edição CLBR de 1964, volume II. Corpo e mapas reproduzidos em fac-símile.\n\n'
for a in assets:
    body += '### ' + a['rotulo'] + '\n\n'
    body += '![' + a['rotulo'] + '](../../anexos/decretos/1964/' + Path(a['destino']).name + ')\n\n'
candidate = BASE / 'dec-53480-1964-01-23-clbr-integral.md'
assert not candidate.exists()
candidate.write_text('---\n' + '\n'.join(lines) + '\n---\n' + body.rstrip() + '\n')
assert candidate.read_text().count('![') == 20
captures = json.loads((pdf.parent / 'capturas.json').read_text())[2:]
receipt = save('recibo_fonte1964.json', {'pdf': info(pdf), 'capturas_preexistentes': captures, 'capturado_em_local': '2026-10-21', 'nova_rede': False})
evidence = [proof / n for n in ['senado-metadados.json.gz', 'recorte-indice-senado.json', 'camara-publicacaooriginal.html.gz', 'camara-captura.headers.txt', 'preimagens-normas.json.gz', 'indice-pIX-180dpi.png', 'indice-pX-180dpi.png', 'cabecalho-p81-600dpi.png']]
evidence += [ROOT / 'federal/_evidencia_identidade_modelos53480_clbr_20261021_009.json', ROOT / 'federal/_provas_modelo53480_clbr_20261021_010/recibo.json', ROOT / 'federal/_provas_modelo53480_clbr_20261021_010/pagina100-180dpi.png', BASE / 'capa-volumeII.png']
manifest = save('candidato53480.json', {
    'status': 'Candidato privado para revisão ROOT; sem promoção, alteração de pendência ou novo alias.',
    'head_preimagem': head, 'path_canonico': canonical, 'preimagem': info(pre), 'candidato': info(candidate),
    'urn': 'urn:lex:br:federal:decreto:1964-01-23;53480', 'fonte_primaria': info(pdf), 'recibo': info(receipt),
    'ativos_em_ordem_de_leitura': assets, 'provas_preexistentes': [info(p) for p in evidence],
    'nota_editorial': note, 'preparado_em': datetime.now(ZoneInfo('America/Recife')).isoformat(),
    'revisao_visual': 'Conferidos os dois recortes da página 81, as páginas completas 82–90 e todos os nove mapas. O corpo contém artigos 1º a 82 e fecho próprio de 23/01/1964, com João Goulart e ministros. O mapa 6 é formulário com área em branco na fonte; preservado. Não foi feita transcrição OCR normativa.',
    'limites': 'Fac-símile, não edição textual pesquisável. ROOT ainda revisará a edição e decidirá promoção. A inspeção não certifica vigência, retificação do DOU ou identidade visual de renderizadores Markdown. A fonte anual e as provas anteriores são preexistentes e permanecem imóveis.',
    'comandos_render': ['pdftoppm -f 135 -l 153 -r 300 -png PDF render/pagina', 'pdftoppm -f 135 -l 135 -r 300 -x 200 -y 1380 -W 710 -H 1138 -png -singlefile PDF render/p81-esquerda-ato', 'pdftoppm -f 135 -l 135 -r 300 -x 900 -y 150 -W 800 -H 2300 -png -singlefile PDF render/p81-direita-ato']})
paths = [Path(__file__).resolve(), pre, candidate, receipt, manifest] + [ROOT / a['path'] for a in assets] + evidence + [pdf]
paths = list(dict.fromkeys(paths))
lst = BASE / 'entrega-paths.txt'
assert not lst.exists()
lst.write_text(''.join(rel(p) + '\n' for p in paths))
save('entrega-hashes.json', [info(p) for p in paths] + [info(lst)])
print(json.dumps({'arquivos': len(paths), 'ativos_normativos': len(assets), 'sha_candidato': sha(candidate.read_bytes()), 'head': head}))
