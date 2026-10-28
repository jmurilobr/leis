"""Recupera candidatos por forma dispositiva literal, sem rede ou canônicos.

A guarda inicial exigia Art. 1. Esta recuperação admite artigo único no início
de dispositivo ativo, ou Portaria com RESOLVE e dispositivo iniciado por 1.
Não altera palavras nem dispensa qualquer gate de publicação posterior.
"""
import argparse
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/bin/qa-20261027/python')]
from converter_organica_fortaleza import converter
from estados.pe_fidelidade_visivel import texto_visivel_html
from comum import decodificar
from baixar_organicas_sapl import categoria_norma
from baixar_textos_articulados_sapl import comparar_norma, elegibilidade


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def normal(text):
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().upper()


def reconhecer(ativos, tipo, norma):
    texts = [texto_visivel_html(block['html']).strip() for block in ativos]
    for block, text in zip(ativos, texts):
        match = re.match(r'^(?:ARTIGO|ART\.)\s+UNICO\s*[.:–—-]\s*(.+)', normal(text))
        if match and len(match[1].strip()) >= 5 and re.search(r'[A-Z]', match[1]):
            return dict(forma='artigo_unico_literal', dispositivo=block['id'], inicio_literal=text[:220])
    if normal(tipo).strip() == 'PORTARIA':
        resolve = False
        for block, text in zip(ativos, texts):
            if re.search(r'\bRESOLV(?:E|EM)\s*:?\s*$', normal(text)):
                resolve = True
            match = re.match(r'^1\.\s*(.+)', text)
            if resolve and match and len(match[1].strip()) >= 5 and re.search(r'[^\W\d_]', match[1]):
                return dict(forma='portaria_resolve_numerada_literal', dispositivo=block['id'], inicio_literal=text[:220])
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--captura', type=Path, required=True)
    parser.add_argument('--cache-api', type=Path, required=True)
    parser.add_argument('--saida', type=Path, required=True)
    parser.add_argument('--referencia', type=dt.date.fromisoformat, required=True)
    args = parser.parse_args()
    args.saida = args.saida.resolve()
    args.captura = args.captura.resolve()
    args.cache_api = args.cache_api.resolve()
    args.saida.mkdir(parents=True, exist_ok=False)
    proofs, recovered, held = [], [], []
    for journal in sorted(args.captura.glob('*/resultados.jsonl')):
        host = journal.parent.name
        raw = journal.read_bytes()
        prefix = raw[:raw.rfind(b'\n') + 1]
        directory = args.saida / host
        directory.mkdir()
        (directory / 'prefixo-original.jsonl').write_bytes(prefix)
        records = {row['ta_id']: row for row in map(json.loads, prefix.decode().splitlines())}
        types_url = f'https://{host}/api/norma/tiponormajuridica/?page_size=100&page=1'
        types_path = ROOT / 'municipais/_indice/organicas-sapl' / host / (sha(types_url.encode()) + '.json')
        data = json.loads(types_path.read_text())
        if data['pagination'].get('next_page'):
            raise ValueError('Tipos de norma incompletos')
        types = {row['id']: row['descricao'] for row in data['results']}
        kinds_url = f'https://{host}/api/compilacao/tipotextoarticulado/'
        kinds_path = args.cache_api / host / (sha(kinds_url.encode()) + '.json')
        kinds_raw = kinds_path.read_bytes()
        kinds_meta = json.loads(kinds_path.with_suffix('.meta.json').read_text())
        assert kinds_meta['url'] == kinds_url and kinds_meta['status'] == 200 and sha(kinds_raw) == kinds_meta['sha256']
        kinds = {row['id']: row for row in json.loads(kinds_raw)['results']}
        additions = []
        for original in records.values():
            if original.get('pendencia') != 'Corpo normativo ativo não reconhecido':
                continue
            row = copy.deepcopy(original)
            try:
                if elegibilidade(row['metadado_ta'], kinds, args.referencia) or comparar_norma(row['metadado_ta'], row['metadado_norma']):
                    raise ValueError('Metadados não concordam ou modelo não público')
                if row['metadado_norma'].get('esfera_federacao') != 'M':
                    raise ValueError('Esfera municipal não confirmada')
                np = row['prova_norma']
                binary = (ROOT / np['arquivo']).read_bytes()
                assert sha(binary) == np['sha256'] and json.loads(binary) == row['metadado_norma']
                hp = row['prova_frontend']
                binary = (ROOT / hp['arquivo']).read_bytes()
                assert sha(binary) == hp['sha256'] and hp['status'] == 200
                assert hp['url_final'].rstrip('/') == f'https://{host}/ta/{row["ta_id"]}/text'
                body, parsed = converter(decodificar(binary, hp['content_type']))
                evidence = reconhecer(parsed.ativos, types[row['metadado_norma']['tipo']], row['metadado_norma'])
                if not evidence:
                    raise ValueError('Forma dispositiva ainda não confirmada')
                candidate = directory / 'candidatos' / f'{row["norma_id"]}-{row["ta_id"]}.txt'
                candidate.parent.mkdir(exist_ok=True)
                with candidate.open('x') as stream:
                    stream.write(body)
                row.update(estado='candidato_estruturado_para_auditoria', pendencia=None,
                           transcricao=str(candidate.relative_to(ROOT)), sha256_transcricao=sha(candidate.read_bytes()),
                           dispositivos_ativos=len(parsed.ativos), dispositivos_historicos=len(parsed.historicos),
                           recuperacao_offline=dict(**evidence, pendencia_anterior=original['pendencia'],
                               categoria_admitida_atualmente=categoria_norma(types[row['metadado_norma']['tipo']], row['metadado_norma']) is not None,
                               sha256_registro_anterior=sha(json.dumps(original, ensure_ascii=False, sort_keys=True).encode()),
                               limite='Somente candidato. Os gates de epígrafe, anexos, contexto, imagens/cores, tabelas, CommonMark e jurisdição permanecem obrigatórios.'))
                additions.append(row)
                recovered.append(dict(host=host, ta_id=row['ta_id'], norma_id=row['norma_id'], prova=evidence))
            except Exception as error:
                held.append(dict(host=host, ta_id=row['ta_id'], motivo=str(error)))
        # Prefixo congelado seguido apenas das recuperações: latest por TA ID.
        (directory / 'resultados.jsonl').write_bytes(prefix + ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in additions).encode())
        annex = (journal.parent / 'anexos-index.json').read_bytes()
        (directory / 'anexos-index.json').write_bytes(annex)
        proofs.append(dict(host=host, diario_origem=str(journal), sha256_prefixo=sha(prefix), bytes_prefixo=len(prefix),
                           tipos_norma=str(types_path.relative_to(ROOT)), sha256_tipos_norma=sha(types_path.read_bytes()),
                           tipos_ta=str(kinds_path), sha256_tipos_ta=sha(kinds_raw), sha256_anexos=sha(annex)))
    result = dict(recuperados=recovered, retidos=held, fontes=proofs, codigo_sha256=sha(Path(__file__).read_bytes()),
                  rede=False, canônicos_alterados=False, limite='Formas detectadas são rótulos literais dos dispositivos; nenhuma inferência de vigência, integralidade ou autorização de publicação.')
    (args.saida / 'manifesto.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(recuperados=len(recovered), retidos=len(held), rede=False, publicados=0)))


if __name__ == '__main__':
    main()
