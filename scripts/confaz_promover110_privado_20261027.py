"""Valida os 110 candidatos CONFAZ; dry-run padrão, --apply exclusivo ROOT.

Sem HTTP ou operações de escrita Git. Repete os gates congelados e confronta
HEAD atual. A promoção explícita usa link exclusivo de um arquivo completo,
sem sobrescrever alvos ou promover históricos/retificações/aliases.
"""
import argparse
import datetime as dt
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from confaz_auditar_piloto_privado_v3_20261027 import campo, representar, identidade, texto_visivel_html
from confaz_confrontar_head_privado_v3_20261027 import meta_corpo, key, MarkdownIt
from confaz_preparar_candidatos_privados_20261027 import dia_captura
from auditar import validar

BASE = ROOT / 'reguladores/_fonte/auditorias'
FINAL = BASE / 'confaz-indice2026-final110-dependencias-20261027/manifesto.json'
FINAL_SHA = 'a1bc691ded46d9b401312c9c2f0aafbfc26c1d3335a20aa38f909ada43da6b77'
QA = BASE / 'confaz-indice2026-qa-002-20261027'
ENTRY = BASE / 'confaz-indice2026-entrada-qa-002-20261027'
CANDIDATES = BASE / 'confaz-indice2026-candidatos-002-20261027/mapa-candidatos.json'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def checked_path(value):
    path = Path(value)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('Caminho fora do repositório')
    result = ROOT / path
    if not result.resolve().is_relative_to(ROOT):
        raise ValueError('Caminho resolve fora do repositório')
    return result


def verify_manifest(path, expected):
    raw = path.read_bytes()
    if sha(raw) != expected:
        raise ValueError('Manifesto mudou: ' + str(path))
    manifest = json.loads(raw)
    seen = set()
    for row in manifest['arquivos']:
        if row['arquivo'] in seen:
            raise ValueError('Artefato repetido no manifesto')
        seen.add(row['arquivo'])
        data = checked_path(row['arquivo']).read_bytes()
        if sha(data) != row['sha256'] or len(data) != row['bytes']:
            raise ValueError('Artefato mudou: ' + row['arquivo'])
    return manifest


def validate_candidate(row, control):
    raw = checked_path(row['candidato']).read_bytes()
    packed = checked_path(row['candidato_gzip']).read_bytes()
    if sha(raw) != row['sha256_md'] or len(raw) != row['bytes_md'] or sha(packed) != row['sha256_gzip'] or gzip.decompress(packed) != raw:
        raise ValueError('Candidato ou cópia gzip mudou')
    source = checked_path(row['fonte']['arquivo']).read_bytes()
    if sha(source) != row['fonte']['sha256']:
        raise ValueError('Fonte mudou')
    fragment = campo(source.decode())
    native = representar(fragment)
    identity = identidade(texto_visivel_html(fragment))
    meta, body = meta_corpo(raw.decode())
    expected = ('Convênio ICMS', identity['numero'], identity['ano'])
    if (meta.get('tipo') != identity['tipo'] or str(meta.get('numero')) != str(identity['numero'])
            or meta.get('data') != identity['data']
            or key(meta, body, MarkdownIt('commonmark', {'html': True})) != expected):
        raise ValueError('Identidade formal do candidato diverge da fonte')
    target = f'reguladores/confaz/convenios/{identity["ano"]}/convenio-icms-{identity["numero"]}-{identity["ano"]}.md'
    if target != row['path_canonico_proposto'] or meta != row['metadata']:
        raise ValueError('Destino ou metadados mudaram')
    # O corpo contém um H1 editorial seguido exatamente do campo integral.
    if body.split('\n\n', 1)[1] != native + '\n' or meta['sha256_texto'] != sha(native.encode()):
        raise ValueError('Corpo não corresponde ao campo integral validado')
    if meta['revogada'] is not None or 'data_vigencia' in meta:
        raise ValueError('Candidato introduz afirmação de vigência não autorizada')
    if meta['baixado_em'] != dia_captura(row['fonte'], '2026-10-27')[0]:
        raise ValueError('Data de captura alterada')
    if meta['publicacao_fonte'] != ' | '.join(control['notas_publicacao_ratificacao_literais']):
        raise ValueError('Notas de publicação/ratificação alteradas')
    if control['estado'] == 'retido' or control['sha256_representacao'] != sha(native.encode()):
        raise ValueError('Controle de representação não aprova o candidato')
    errors, warnings = validar(raw.decode(), target, dt.date.today())
    if errors:
        raise ValueError('Formato inválido: ' + str(errors))
    return raw, target, warnings


def create_exclusive(prepared, target):
    if target.exists() or target.is_symlink():
        raise FileExistsError('Alvo existente: ' + str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    os.link(prepared, target)  # EEXIST atômico, inclusive contra corrida/symlink.
    prepared.unlink()  # Não deixa um alias gravável do arquivo canônico.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida', type=Path, required=True, help='Diretório novo persistente no mesmo volume do repositório')
    parser.add_argument('--apply', action='store_true', help='Uso exclusivo ROOT: grava os 110 após todas as validações; nunca sobrescreve')
    args = parser.parse_args()
    fingerprint = sha(Path(__file__).read_bytes())
    output = args.saida.resolve()
    if not output.is_relative_to(ROOT) or not (ROOT / '.git').exists():
        raise ValueError('Saída deve ficar no repositório montado')
    output.mkdir(parents=True, exist_ok=False)
    final = verify_manifest(FINAL, FINAL_SHA)
    original = BASE / 'confaz-indice2026-final110-20261027/manifesto.json'
    expected_original = next(r['sha256'] for r in final['arquivos'] if checked_path(r['arquivo']) == original)
    verify_manifest(original, expected_original)
    subprocess.run([sys.executable, '-I', str(ROOT / 'scripts/confaz_auditar_piloto_privado_v3_20261027.py'),
                    '--captura', str(ENTRY), '--saida', str(output / 'qa-replay')], check=True, cwd=ROOT)
    replay = json.loads((output / 'qa-replay/resumo.json').read_text())
    frozen = json.loads((QA / 'resumo.json').read_text())
    if replay != frozen:
        raise ValueError('Replay independente difere dos controles congelados')
    subprocess.run([sys.executable, '-I', str(ROOT / 'scripts/confaz_confrontar_head_privado_v3_20261027.py'),
                    '--qa', str(QA), '--saida', str(output / 'confronto-head')], check=True, cwd=ROOT)
    head = json.loads((output / 'confronto-head/confronto-head.json').read_text())
    results = {r['numero']: r for r in head['resultados']}
    controls = {r['numero_indice']: r for r in replay['resultados']}
    candidates = json.loads(CANDIDATES.read_text())
    if candidates['candidatos'] != 110 or len(candidates['resultados']) != 110:
        raise ValueError('Seleção diferente dos 110 revisados')
    prepared = output / 'validados'
    prepared.mkdir()
    proposals = []
    for row in candidates['resultados']:
        current = results[row['numero']]
        if current['estado'] != 'candidato_privado_sem_alias_HEAD' or current['aliases'] or current['aliases_potenciais']:
            raise ValueError('Alias ou retenção no HEAD atual: ' + str(row['numero']))
        raw, path, warnings = validate_candidate(row, controls[row['numero']])
        target = checked_path(path)
        if target.exists() or target.is_symlink():
            raise FileExistsError('Alvo já existe: ' + path)
        private = prepared / (str(row['numero']) + '.txt')
        with private.open('xb') as stream:
            stream.write(raw)
        proposals.append(dict(path=path, sha256=sha(raw), bytes=len(raw), preparado=str(private.relative_to(ROOT)), avisos=warnings))
    if len({r['path'] for r in proposals}) != 110:
        raise ValueError('Destinos repetidos')
    actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
    if actual != head['commit']:
        raise ValueError('HEAD mudou durante a validação; repetir em saída nova')
    if sha(Path(__file__).read_bytes()) != fingerprint:
        raise ValueError('Runner mudou durante a validação')
    receipt = dict(modo='apply' if args.apply else 'dry-run', commit_confrontado=actual,
                   propostas=proposals, publicados=[], codigo_sha256=fingerprint,
                   manifesto=str(FINAL.relative_to(ROOT)), sha256_manifesto=FINAL_SHA,
                   limite='Edição capturada do portal; condições literais preservadas, sem afirmar vigência ou equivalência editorial DOU. Arquivos preparados são temporários e removidos após link exclusivo bem-sucedido; candidatos originais preservados. Nenhuma reserva DOU não publicada é presumida; ROOT deve conferir suas seleções privadas antes de --apply.')
    report = output / 'resultado.json'
    report.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    if args.apply:
        try:
            for row in proposals:
                if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() != actual:
                    raise ValueError('HEAD mudou antes da gravação')
                private = checked_path(row['preparado'])
                if sha(private.read_bytes()) != row['sha256']:
                    raise ValueError('Arquivo preparado mudou')
                create_exclusive(private, checked_path(row['path']))
                receipt['publicados'].append(row)
                report.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
        except Exception as error:
            receipt['erro_apply'] = repr(error)
            report.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
            raise
    print(json.dumps(dict(modo=receipt['modo'], propostas=len(proposals), gravados=len(receipt['publicados']), commit=actual, resultado=str(report.relative_to(ROOT)))))


if __name__ == '__main__':
    main()
