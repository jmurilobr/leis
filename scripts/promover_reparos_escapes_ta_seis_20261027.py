"""Runner privado dos seis reparos; dry-run padrão, --apply exclusivo ROOT.

Valida os 94 artefatos congelados, fonte, metadados, sinais/tabelas e HEAD.
Somente --apply troca preimagens não publicadas, com backup e replace atômico.
Não faz HTTP, staging ou qualquer escrita Git.
"""
import argparse
import datetime as dt
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/bin/qa-20261027/python')]
from auditar import validar
from auditar_municipal import metadados
from auditar_colisoes_lote_municipal import keys
from auditar_emissores_sapl import analisar
from auditar_commonmark_ta_v2 import comparar, MarkdownIt
from conferir_tabelas_nativas_ta import Tabelas
from preparar_reparos_escapes_ta_20261027 import escapar

BASE = ROOT / 'municipais/_indice/_recuperacao_20261027'
FROZEN = BASE / 'reparos-escapes-ta-seis-final-20261027/manifesto.json'
FROZEN_SHA = 'ac291cc44db71a8f99da43249403201c69dd5bb2895e1a05cdbaf32a71d14881'
MAP = BASE / 'reparos-escapes-ta-seis-v2-20261027/mapa-candidatos.json'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def verify_manifest(path, expected):
    raw = path.read_bytes()
    if sha(raw) != expected:
        raise ValueError('Manifesto congelado mudou')
    manifest = json.loads(raw)
    seen = set()
    for row in manifest['arquivos']:
        relative = Path(row['arquivo'])
        full = ROOT / relative
        if relative.is_absolute() or '..' in relative.parts or not full.resolve().is_relative_to(ROOT) or row['arquivo'] in seen:
            raise ValueError('Caminho de artefato externo ou repetido')
        seen.add(row['arquivo'])
        binary = full.read_bytes()
        if sha(binary) != row['sha256'] or len(binary) != row['bytes']:
            raise ValueError('Artefato congelado mudou: ' + row['arquivo'])
    return manifest


def target_path(value):
    path = Path(value)
    if path.is_absolute() or '..' in path.parts or path.parts[0] != 'municipais' or path.suffix != '.md':
        raise ValueError('Destino municipal inválido')
    target = ROOT / path
    if not target.resolve().is_relative_to(ROOT) or target.is_symlink():
        raise ValueError('Destino externo ou symlink')
    return target


def body(text):
    return text.split('\n---\n', 1)[1].lstrip('\n').split('\n\n', 1)[1]


def validate_row(row, names):
    target = target_path(row['path'])
    if not stat.S_ISREG(target.stat().st_mode):
        raise ValueError('Preimagem não é arquivo regular')
    old = (ROOT / row['preimagem']).read_bytes()
    new = (ROOT / row['candidato']).read_bytes()
    if sha(old) != row['sha256_preimagem'] or sha(new) != row['sha256_candidato']:
        raise ValueError('Backup ou candidato congelado mudou')
    if target.read_bytes() != old:
        raise ValueError('Preimagem atual diverge: ' + row['path'])
    old_meta, new_meta = metadados(old.decode()), metadados(new.decode())
    old_body, new_body = body(old.decode()), body(new.decode())
    if sha(old_body[:-1].encode()) != old_meta['sha256_texto'] or sha(new_body[:-1].encode()) != new_meta['sha256_texto']:
        raise ValueError('sha256_texto não corresponde ao corpo')
    old_meta.pop('sha256_texto')
    new_meta.pop('sha256_texto')
    if old_meta != new_meta or set(keys(old.decode(), row['path'])) != set(keys(new.decode(), row['path'])):
        raise ValueError('Metadados ou identidade alterados')
    if new_body != escapar(old_body[:-1]) + '\n':
        raise ValueError('Candidato contém alterações além dos escapes autorizados')
    # A comparação de metadados acima é semântica; esta verifica também que
    # nenhum byte do cabeçalho/H1 mudou além do valor de sha256_texto.
    import re
    prefix = old.decode()[:-len(old_body)]
    prefix, count = re.subn(r'(?m)^sha256_texto: .*$', 'sha256_texto: ' + json.dumps(sha(new_body[:-1].encode())), prefix)
    if count != 1 or (prefix + new_body).encode() != new:
        raise ValueError('Cabeçalho/H1 sofreu alteração não autorizada')
    source = (ROOT / row['fonte']['arquivo']).read_bytes()
    api = (ROOT / row['prova_norma']['arquivo']).read_bytes()
    if sha(source) != row['fonte']['sha256'] or sha(api) != row['prova_norma']['sha256'] or json.loads(api).get('esfera_federacao') != 'M':
        raise ValueError('Fonte/API municipal diverge')
    replay = comparar(source.decode(), new_body)
    if not replay['aprovado'] or not replay['assinatura_numerica_confere']:
        raise ValueError('Replay independente não confere')
    original_tables = Tabelas(True)
    original_tables.feed(source.decode())
    original_tables.close()
    rendered_tables = Tabelas()
    rendered_tables.feed(MarkdownIt('commonmark', {'html': True}).enable('table').enable('strikethrough').render(new_body))
    rendered_tables.close()
    if original_tables.current is not None or rendered_tables.current is not None or original_tables.tables != rendered_tables.tables:
        raise ValueError('Tabelas/células/mesclagens/links divergem')
    if analisar(new_body, new_meta['municipio'], names):
        raise ValueError('Jurisdição exige revisão')
    errors, warnings = validar(new.decode(), row['path'], dt.date.today())
    if errors or warnings:
        raise ValueError('Formato exige revisão: ' + str((errors, warnings)))
    return old, new, dict(replay=replay, tabelas=len(original_tables.tables), eventos_tabelas=sum(map(len, original_tables.tables)),
                          metadados_intactos_exceto_sha256_texto=True, identidade_inalterada=True)


def replace_with_backup(target, prepared, backup, expected_old, expected_new):
    if target.is_symlink() or not stat.S_ISREG(target.stat().st_mode):
        raise ValueError('Destino não é arquivo regular')
    with target.open('rb') as current:
        fcntl.flock(current, fcntl.LOCK_EX | fcntl.LOCK_NB)
        before = current.read()
        inode = os.fstat(current.fileno())
        if sha(before) != expected_old or sha(prepared.read_bytes()) != expected_new:
            raise ValueError('Preimagem/preparado diverge antes da troca')
        backup.parent.mkdir(parents=True, exist_ok=True)
        with backup.open('xb') as stream:
            stream.write(before)
            stream.flush()
            os.fsync(stream.fileno())
        prepared.chmod(stat.S_IMODE(inode.st_mode))
        now = target.lstat()
        if target.is_symlink() or (now.st_dev, now.st_ino, now.st_size, now.st_mtime_ns) != (inode.st_dev, inode.st_ino, inode.st_size, inode.st_mtime_ns):
            raise ValueError('Preimagem mudou durante a preparação')
        os.replace(prepared, target)
        if sha(target.read_bytes()) != expected_new:
            raise ValueError('Candidato gravado não confere')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida', type=Path, required=True)
    parser.add_argument('--apply', action='store_true', help='Uso exclusivo ROOT; substitui somente preimagem exata ausente de HEAD')
    args = parser.parse_args()
    output = args.saida.resolve()
    if not output.is_relative_to(ROOT) or not (ROOT / '.git').exists():
        raise ValueError('Saída fora do repositório montado')
    output.mkdir(parents=True, exist_ok=False)
    fingerprint = sha(Path(__file__).read_bytes())
    frozen = verify_manifest(FROZEN, FROZEN_SHA)
    if len(frozen['arquivos']) != 94:
        raise ValueError('Manifesto diferente dos 94 artefatos revisados')
    rows = json.loads(MAP.read_text())['candidatos']
    if len(rows) != 6 or len({r['path'] for r in rows}) != 6:
        raise ValueError('Seleção não corresponde aos seis revisados')
    indexed = subprocess.check_output(['git', 'ls-files', '-z', '--', *[row['path'] for row in rows]], cwd=ROOT)
    if indexed:
        raise ValueError('Um dos seis já está no índice; ROOT deve reconciliar antes da promoção')
    # Lock privado serializa aplicações deste runner; não altera arquivos Git.
    lock = (BASE / 'promocao-reparos-escapes-seis.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    names = [r['nome'] for r in json.loads((ROOT / 'municipais/_indice/ibge-municipios.json').read_text())]
    proposals = []
    ready = output / 'preparados'
    ready.mkdir()
    for index, row in enumerate(rows):
        _, new, proof = validate_row(row, names)
        prepared = ready / (str(index) + '.txt')
        with prepared.open('xb') as stream:
            stream.write(new)
            stream.flush()
            os.fsync(stream.fileno())
        proposals.append(dict(path=row['path'], sha256_preimagem=row['sha256_preimagem'], sha256_candidato=row['sha256_candidato'],
                              preparado=str(prepared.relative_to(ROOT)), backup=str((output / 'backups' / (str(index) + '.txt')).relative_to(ROOT)), prova=proof))
    baseline_dir = output / 'baseline-head'
    command = [sys.executable, '-I', str(ROOT / 'scripts/congelar_baseline_municipal_head_20261027.py'), '--saida', str(baseline_dir),
               '--reserva', str(BASE / 'agregado212-coerente-final/entrega-final.json'), '91dceda722ad76d03c4781eeac67e5bd880919befc690d2ebe119c2568e74edd']
    subprocess.run(command, check=True, cwd=ROOT)
    baseline = json.loads((baseline_dir / 'manifesto.json').read_text())
    with gzip.open(ROOT / baseline['metadados'], 'rt') as stream:
        head = {r['path']: r for r in map(json.loads, stream)}
    if any(row['path'] in head for row in rows):
        raise ValueError('Um dos seis já está em HEAD ou reserva qualificada')
    # Confirma os 570 publicados por path e SHA real, sem somá-los novamente.
    package570 = json.loads((BASE / 'agregado570-final/entrega-final.json').read_text())
    artifacts570 = {r['arquivo']: r for r in package570['arquivos']}
    names570 = (ROOT / package570['lista_normas']).read_text().splitlines()
    if len(names570) != 570 or any(path not in head or head[path]['origem'] != 'HEAD' or head[path]['sha256'] != artifacts570[path]['sha256'] for path in names570):
        raise ValueError('Os 570 ainda não estão integralmente em HEAD com os hashes revisados')
    listing = output / 'identidades-preimagens.paths.txt'
    listing.write_text(''.join(row['path'] + '\n' for row in rows))
    subprocess.run([sys.executable, '-I', str(ROOT / 'scripts/comparar_baseline_municipal_head_20261027.py'), '--baseline', str(baseline_dir / 'manifesto.json'),
                    '--lista', str(listing), '--saida', str(output / 'dedup.json')], check=True, cwd=ROOT)
    actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
    if actual != baseline['commit'] or sha(Path(__file__).read_bytes()) != fingerprint:
        raise ValueError('HEAD ou runner mudou durante a validação')
    result = dict(modo='apply' if args.apply else 'dry-run', commit=actual, codigo_sha256=fingerprint,
                  manifesto=str(FROZEN.relative_to(ROOT)), sha256_manifesto=FROZEN_SHA, artefatos_validados=94,
                  propostas=proposals, aplicados=[], head_normas=baseline['normas_head'], reservas=baseline['reservas'],
                  publicados570_confirmados=True, capturado_em=dt.datetime.now(ZoneInfo('America/Recife')).isoformat(),
                  limite='Somente escapes de sinais e sha256_texto. Ausência HEAD e dedup verificados de novo. Não modifica metadados de captura nem decide vigência.')
    report = output / 'resultado.json'
    def save():
        report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    save()
    if args.apply:
        try:
            for row in proposals:
                if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() != actual:
                    raise ValueError('HEAD mudou antes da troca')
                replace_with_backup(target_path(row['path']), ROOT / row['preparado'], ROOT / row['backup'], row['sha256_preimagem'], row['sha256_candidato'])
                result['aplicados'].append(row)
                save()
        except Exception as error:
            result['erro_apply'] = repr(error)
            result['estado_alvos_apos_falha'] = [dict(path=row['path'], sha256=sha(target_path(row['path']).read_bytes())) for row in proposals]
            save()
            raise
    lock.close()
    print(json.dumps(dict(modo=result['modo'], propostas=6, aplicados=len(result['aplicados']), commit=actual, resultado=str(report.relative_to(ROOT)))))


if __name__ == '__main__':
    main()
