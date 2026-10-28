"""ROOT: valida 3.848 documentos e 191 promoções; dry-run é o padrão.

Somente --apply escreve, depois de todas as verificações. Não opera Git de
escrita, rede, conversores ou registro de pendências. Promove apenas bytes finais
já congelados, com backups completos antes da primeira troca atômica.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import datetime
import gzip
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3].resolve()
PACK = ROOT / 'federal/_fonte/auditorias/retomada_federal_20261027_004/cumulativo022024_v2'
CM = ROOT / 'federal/_fonte/auditorias/commonmark8886_20261027_001'
SPECIAL = 'federal/decretos/1942/dec-8886-1942-03-02.md'
sha = lambda data: hashlib.sha256(data).hexdigest()

def read_json(path):
    return json.loads(path.read_bytes())

def safe(relative):
    raw = Path(relative)
    assert not raw.is_absolute() and '..' not in raw.parts, relative
    joined = ROOT / raw
    resolved = joined.resolve()
    assert resolved.is_relative_to(ROOT) and resolved == joined, relative
    return resolved

def number_key(value):
    return re.sub(r'[.\s]', '', str(value)).upper().lstrip('0') or '0'

def fields(raw):
    text = raw.decode('utf-8')
    assert text.startswith('---\n')
    cab, body = text[4:].split('\n---\n', 1)
    metadata = {}
    for line in cab.splitlines():
        key, value = line.split(':', 1)
        value = value.strip()
        assert key not in metadata
        metadata[key] = json.loads(value) if value.startswith('"') else value
    return metadata, body

def payload(raw):
    _, body = fields(raw)
    title, separator, content = body.lstrip().partition('\n')
    assert separator and title.startswith('# Decreto ')
    return content

def durable_new(path, data):
    with path.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())

def sync_dir(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
receipt = read_json(BASE / 'recibo_promocao191.json')
assert sha(Path(__file__).read_bytes()) == receipt['sha256_runner']
for record in receipt['insumos']:
    assert sha(safe(record['path']).read_bytes()) == record['sha256'], record['path']
for pair in receipt['listas_congeladas']:
    listing = safe(pair['paths'])
    hashes = read_json(safe(pair['hashes']))
    assert sha(listing.read_bytes()) == hashes['sha256_lista']
    paths = listing.read_text().splitlines()
    assert paths == [record['path'] for record in hashes['arquivos']]
    assert len(paths) == len(set(paths))
    for record in hashes['arquivos']:
        assert sha(safe(record['path']).read_bytes()) == record['sha256'], record['path']

head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
verified = read_json(PACK / 'verificacao3848.json')
vs = {record['path']: record for record in verified['registros']}
assert len(vs) == len(verified['registros']) == 3848
promotions = read_json(PACK / 'promocoes191.json')['substituicoes']
ps = {record['path']: record for record in promotions}
assert len(ps) == len(promotions) == 191 and set(ps).issubset(vs)
assert all(p['sha256_preimagem'] != p['sha256_candidato'] for p in promotions)
assert sum(bool(record['HTML_original']) for record in promotions) == 12
archive = read_json(PACK / 'fontes3848/mapa_fontes3848.json')
assert len(archive['registros']) == 3848
parts = {record['path']: record for record in archive['partes']}
assert len(parts) == len(archive['partes'])
for relative, part in parts.items():
    path = safe(relative)
    assert path.stat().st_size == part['bytes_gzip'] < 95 * 1024 ** 2
    assert sha(path.read_bytes()) == part['sha256_gzip']

seen, urns, identities = set(), set(), set()
positions = {path: 0 for path in parts}
part_counts = {path: 0 for path in parts}
pending, native_payloads = [], {}
for record in archive['registros']:
    path = record['path']
    match = re.fullmatch(r'federal/decretos/(\d{4})/dec-([a-z0-9-]+)-(\d{4}-\d\d-\d\d)\.md', path)
    assert match and path in vs and path not in seen, path
    seen.add(path)
    v = vs[path]
    relative = record['arquivo']
    assert relative in parts and record['offset_gzip'] == positions[relative]
    with safe(relative).open('rb') as stream:
        stream.seek(record['offset_gzip'])
        member = stream.read(record['bytes_gzip_member'])
    assert len(member) == record['bytes_gzip_member'] and sha(member) == record['sha256_member_gzip']
    positions[relative] += len(member)
    part_counts[relative] += 1
    raw_record = gzip.decompress(member)  # Também confere o CRC de cada membro.
    assert sha(raw_record) == record['sha256_registro_jsonl']
    obj = json.loads(raw_record)
    assert obj['path'] == path and obj['urn'] == v['urn']
    assert obj['numero'] == v['numero'] and obj['data'] == v['data']
    assert match[1] == obj['data'][:4] and match[3] == obj['data']
    assert number_key(match[2]) == number_key(obj['numero'])
    identity = (number_key(obj['numero']), obj['data'][:4])
    assert identity not in identities and obj['urn'] not in urns, path
    identities.add(identity)
    urns.add(obj['urn'])
    prefix = 'urn:lex:br:federal:decreto:' + obj['data'] + ';'
    assert obj['urn'].startswith(prefix) and number_key(obj['urn'][len(prefix):]) == identity[0]
    for key, hkey in [('md_final', 'sha256_md_final'), ('html_original', 'sha256_html'), ('metadados_raw', 'sha256_metadados')]:
        assert sha(obj[key].encode()) == obj[hkey] == record[hkey] == v[hkey], path
    metadata = json.loads(obj['metadados_raw'])
    assert metadata['legislationIdentifier'] == obj['urn'] and metadata['legislationDate'] == obj['data']
    assert metadata['legislationType'] in {'Decreto Numerado', 'Decreto'}
    final = obj['md_final'].encode()
    front, _ = fields(final)
    assert front['urn'] == obj['urn'] and front['data'] == obj['data']
    assert number_key(front['numero']) == identity[0] and front['tipo'] in {'Decreto', 'Decreto Numerado'}
    assert sha(safe(v['arquivo_final']).read_bytes()) == obj['sha256_md_final']
    current = safe(path).read_bytes()
    if path in ps:
        p = ps[path]
        assert v['arquivo_final'] == p['candidate']
        assert obj['md_preimagem'] is not None
        before = obj['md_preimagem'].encode()
        assert sha(before) == obj['sha256_preimagem'] == record['sha256_preimagem'] == p['sha256_preimagem'] == v['sha256_preimagem']
        assert sha(final) == p['sha256_candidato']
        current_sha = sha(current)
        assert current_sha in {p['sha256_preimagem'], p['sha256_candidato']}, path
        pending.append({'path': path, 'before': before, 'final': final, 'skip': current_sha == p['sha256_candidato']})
        if p['HTML_original']:
            native_payloads[path] = sha(payload(final).encode())
    else:
        assert obj['md_preimagem'] is None and obj['sha256_preimagem'] is None
        assert sha(current) == obj['sha256_md_final'], path
assert len(seen) == 3848 and len(pending) == 191 and len(native_payloads) == 12
for relative, part in parts.items():
    assert positions[relative] == part['bytes_gzip'] and part_counts[relative] == part['registros']
replay = read_json(PACK / 'resultado.json')
assert replay['resumo'] == {'auditados': 3848, 'aprovados': 3848, 'divergencias': 0}
assert len(replay['registros']) == 3848 and {record['path'] for record in replay['registros']} == seen
assert all(record['aprovado'] and record['sha256_md_final'] == vs[record['path']]['sha256_md_final'] for record in replay['registros'])
assert read_json(PACK / 'validacao_arquivo_publico3848.json')['resumo'] == {'registros': 3848, 'preimagens': 191, 'partes': len(parts), 'divergencias': 0}

# Onze renders oficiais aprovados e uma limitação explícita de tamanho, coberta
# pelo complemento local CommonMark/HTML5, sem afirmar validação GitHub integral.
github = read_json(PACK / 'github12_complemento_resultado.json')
assert github['resumo'] == {'chamadas': 12, 'renders_aprovados': 11, 'recusas_por_limite_400KB': 1, 'outros_erros': 0}
covered = set()
for record in github['aprovados']:
    path = record['path']
    assert path in native_payloads and path not in covered and record['aprovado'] is True
    assert set(record['checks']) == {'texto_pontuacao', 'assinatura_numerica', 'contextos_numericos', 'listas_type_start_value', 'matrizes_tabelas', 'eventos_rowspan_colspan'}
    assert all(value is True for value in record['checks'].values())
    assert record['sha256_candidato'] == vs[path]['sha256_md_final'] and record['sha256_html_fonte'] == vs[path]['sha256_html']
    for key in ['request', 'response']:
        assert sha(safe(record[key]['path']).read_bytes()) == record[key]['sha256']
    request = read_json(safe(record['request']['path']))
    assert request['mode'] == 'gfm' and sha(request['text'].encode()) == native_payloads[path]
    covered.add(path)
refusal = github['recusa']
assert refusal['path'] == SPECIAL and refusal['returncode'] != 0
assert '400 KB' in refusal['erro'] and 'HTTP 403' in refusal['erro']
for key in ['request', 'response']:
    assert sha(safe(refusal[key]['path']).read_bytes()) == refusal[key]['sha256']
assert sha(read_json(safe(refusal['request']['path']))['text'].encode()) == native_payloads[SPECIAL]
local = read_json(CM / 'resultado.json')
assert local['path'] == SPECIAL and local['aprovado'] is True
assert set(local['checks']) == {'texto_pontuacao_mesmo_comparador_anterior', 'assinatura_numerica_anterior', 'contextos_numericos_anteriores', 'texto_pontuacao_HTML5', 'assinatura_numerica_HTML5', 'contextos_numericos_HTML5', 'listas_HTML5_type_start_value_contadores', 'matrizes_HTML5_linha_celula_spans'}
assert all(value is True for value in local['checks'].values())
assert local['sha256_md_final'] == vs[SPECIAL]['sha256_md_final'] and local['sha256_html_original'] == vs[SPECIAL]['sha256_html']
assert local['sha256_payload'] == native_payloads[SPECIAL] and local['resumo']['divergencias'] == 0
assert local['motores']['markdown_it_py'] == '4.0.0' and local['motores']['html5lib'] == '1.1'
assert sha(gzip.decompress((CM / 'md_final.md.gz').read_bytes())) == vs[SPECIAL]['sha256_md_final']
assert sha(gzip.decompress((CM / 'fonte_original.html.gz').read_bytes())) == vs[SPECIAL]['sha256_html']
assert sha((CM / 'render_commonmark.html').read_bytes()) == local['sha256_render_commonmark']
binding = read_json(CM / 'vinculo_payload_api_recusado.json')
assert binding['mesmo_payload_integral'] and binding['sha256_payload_commonmark'] == native_payloads[SPECIAL]
assert binding['sha256_request_github'] == refusal['request']['sha256']
covered.add(SPECIAL)
assert covered == set(native_payloads)

query = subprocess.run(['git', 'cat-file', '--batch-check'], cwd=ROOT,
    input=''.join(head + ':' + path + '\n' for path in sorted(seen)), text=True, capture_output=True, check=True)
assert len(query.stdout.splitlines()) == 3848 and all(line.endswith(' missing') for line in query.stdout.splitlines()), 'Um destino já está em HEAD; revisar a seleção antes de promover.'
years = sorted({record['data'][:4] for record in vs.values()})
tree = subprocess.check_output(['git', 'ls-tree', '-rz', head, '--'] + ['federal/decretos/' + year for year in years], cwd=ROOT)
for entry in tree.split(b'\0'):
    if not entry:
        continue
    path = entry.split(b'\t', 1)[1].decode()
    match = re.fullmatch(r'federal/decretos/(\d{4})/dec-(.+)-\d{4}-\d\d-\d\d\.md', path)
    if match:
        assert (number_key(match[2]), match[1]) not in identities, ('Colisão número/ano em HEAD', path)
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == head
print('Validados: 3.848 documentos/fontes, 191 preimagens, 11 renders GitHub e 8.886 por CommonMark/HTML5. Nenhuma escrita realizada.', flush=True)
if not args.apply:
    raise SystemExit(0)

# Todas as validações e a confirmação do HEAD precedem a primeira escrita.
D = BASE / ('aplicacao_ROOT_' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
D.mkdir(exist_ok=False)
intent = []
for index, record in enumerate(pending, 1):
    backup = D / (f'{index:03}_' + Path(record['path']).name + '.preimagem')
    durable_new(backup, record['before'])
    assert sha(backup.read_bytes()) == ps[record['path']]['sha256_preimagem']
    intent.append({'path': record['path'], 'backup': str(backup.relative_to(ROOT)),
        'sha256_preimagem': sha(record['before']), 'sha256_final': sha(record['final']), 'ja_promovido': record['skip']})
durable_new(D / 'intencao.json', (json.dumps({'HEAD': head, 'substituicoes': intent}, ensure_ascii=False, indent=2) + '\n').encode())
sync_dir(D)
log = D / 'aplicacao.jsonl'
for record in pending:
    target = safe(record['path'])
    expected = ps[record['path']]['sha256_candidato'] if record['skip'] else ps[record['path']]['sha256_preimagem']
    assert sha(target.read_bytes()) == expected, record['path']
    if not record['skip']:
        temp = target.with_name('.' + target.name + f'.promocao191.{os.getpid()}.tmp')
        assert not temp.exists()
        durable_new(temp, record['final'])
        assert sha(temp.read_bytes()) == ps[record['path']]['sha256_candidato']
        os.replace(temp, target)
        sync_dir(target.parent)
    assert sha(target.read_bytes()) == ps[record['path']]['sha256_candidato']
    with log.open('a') as stream:
        stream.write(json.dumps({'path': record['path'], 'sha256_final': sha(record['final']),
            'estado': 'já promovido' if record['skip'] else 'promovido'}, ensure_ascii=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
assert all(sha(safe(record['path']).read_bytes()) == ps[record['path']]['sha256_candidato'] for record in pending)
sync_dir(D)
print('ROOT: 191 destinos finais conferidos; nenhuma operação Git de escrita. Backups/recibo:', D, flush=True)
