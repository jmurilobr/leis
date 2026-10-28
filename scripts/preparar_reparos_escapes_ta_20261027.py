"""Candidatos privados para seis perdas literais de crase/hífen no CommonMark.

Não modifica canônicos nem conversores. Escapa somente crases literais e
hífens no início de linha; a comparação independente integral deve passar.
Não recupera listas HTML nativas nem altera seleção de versões/dispositivos.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / 'scripts/bin/qa-20261027/python'), str(ROOT / 'scripts')]
from auditar_commonmark_ta_v2 import comparar
from auditar_municipal import metadados
from auditar_emissores_sapl import analisar
from auditar import validar


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def escapar(body):
    body = re.sub(r'(?<!\\)`', r'\`', body)
    return re.sub(r'(?m)^([ \t]{0,3})-(?=[ \t]|$)', r'\1\\-', body)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida', type=Path, required=True)
    args = parser.parse_args()
    args.saida.mkdir(parents=True, exist_ok=False)
    base = ROOT / 'municipais/_indice/_recuperacao_20261027/lotes'
    names = [r['nome'] for r in json.loads((ROOT / 'municipais/_indice/ibge-municipios.json').read_text())]
    rows = []
    for batch in ['0008', '0009', '0010']:
        render = base / f'ta-commonmark-{batch}/controle.json'
        context = base / f'ta-contexto-{batch}/controle.json'
        material = base / f'ta-materializados-{batch}-v5/resultados.jsonl'
        materials = {r.get('path'): r for r in map(json.loads, material.read_text().splitlines()) if r['aprovado']}
        approved = set((context.parent / 'aprovados.paths.txt').read_text().splitlines())
        for original in json.loads(render.read_text())['resultados']:
            if original['aprovado'] or not original.get('contexto'):
                continue
            path = original['path']
            raw = (ROOT / path).read_bytes()
            assert sha(raw) == original['sha256'] == materials[path]['sha256'] and path in approved
            source = materials[path]['prova_frontend']
            source_raw = (ROOT / source['arquivo']).read_bytes()
            assert sha(source_raw) == source['sha256']
            text = raw.decode()
            meta = metadados(text)
            body = text.split('\n---\n', 1)[1].lstrip('\n').split('\n\n', 1)[1]
            assert body.endswith('\n') and sha(body[:-1].encode()) == meta['sha256_texto']
            new_body = escapar(body[:-1])
            proof = comparar(source_raw.decode(), new_body)
            assert proof['aprovado'] and proof['assinatura_numerica_confere'], (path, proof)
            api_proof = materials[path]['prova_norma']
            api_raw = (ROOT / api_proof['arquivo']).read_bytes()
            assert sha(api_raw) == api_proof['sha256'] and json.loads(api_raw)['esfera_federacao'] == 'M'
            assert not analisar(new_body, meta['municipio'], names)
            assert materials[path]['gates']['anexos_proprios'] == 0
            new_hash = sha(new_body.encode())
            prefix = text[:-len(body)]
            prefix, replacements = re.subn(r'(?m)^sha256_texto: .*$', 'sha256_texto: ' + json.dumps(new_hash), prefix)
            assert replacements == 1
            candidate = (prefix + new_body + '\n').encode()
            errors, warnings = validar(candidate.decode(), path, dt.date(2026, 10, 27))
            assert not errors and not warnings, (path, errors, warnings)
            directory = args.saida / f'{batch}-{len(rows) + 1}'
            directory.mkdir()
            backup = directory / 'preimagem.txt'
            output = directory / 'candidato.txt'
            backup.write_bytes(raw)
            output.write_bytes(candidate)
            row = dict(path=path, sha256_preimagem=sha(raw), preimagem=str(backup), candidato=str(output),
                       sha256_candidato=sha(candidate), sha256_texto=new_hash, fonte=source,
                       prova_norma=api_proof, controle_render=str(render.relative_to(ROOT)),
                       sha256_controle_render=sha(render.read_bytes()), controle_contexto=str(context.relative_to(ROOT)),
                       sha256_controle_contexto=sha(context.read_bytes()), materializacao=str(material.relative_to(ROOT)),
                       sha256_materializacao=sha(material.read_bytes()), replay_independente=proof,
                       esfera='M confirmada na API', anexos_proprios=0,
                       estado='candidato privado; ainda exige confronto HEAD e revalidação da preimagem antes da promoção')
            (directory / 'controle.json').write_text(json.dumps(row, ensure_ascii=False, indent=2) + '\n')
            rows.append(row)
    assert len(rows) == 6
    result = dict(candidatos=rows, promocao_automatica=False, codigo_sha256=sha(Path(__file__).read_bytes()),
                  limite='Somente escapes e sha256_texto. Mesmas palavras, sinais, números, notas e seleção ativa/histórica. Nenhum canônico ou congelado foi modificado; não inclui a lista HTML nativa de Bofete 1665.')
    (args.saida / 'mapa-candidatos.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(candidatos=len(rows), replays_aprovados=len(rows), promocao=False)))


if __name__ == '__main__':
    main()
