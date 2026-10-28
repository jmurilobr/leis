"""Captura textos articulados públicos vinculados a normas, sem publicar Markdown.

Continuação por índice coerente separado, um cliente a 1 rps por portal. Metadados, HTML e transcrição candidata ficam ligados
por hashes; projetos, textos em edição, privados e identidades divergentes não
geram candidatos. Sem limite total: checkpoints e lotes de 500 apenas organizam.
"""
import argparse
import fcntl
import os
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit
sys.path.insert(0, str(Path(__file__).resolve().parent))
from baixar_organicas_sapl import rede_host
from converter_organica_fortaleza import converter
from comum import decodificar, normalizar_chave
from preparar_cache_indice_ta_coerente_20261027 import preparar

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = {0, 69}  # SAPL models.py: Público e Imutável Público.


class PortalBloqueado(RuntimeError):
    pass


def sha(b):
    return hashlib.sha256(b).hexdigest()


def elegibilidade(ta, kinds, reference):
    if ta.get('privacidade') not in PUBLIC:
        return 'status não público; não buscar conteúdo'
    kind = kinds.get(ta.get('tipo_ta'))
    if not kind or normalizar_chave(kind.get('descricao', '')) != 'norma juridica':
        return 'modelo não é Norma Jurídica'
    if ta.get('content_type') != kind.get('content_type') or not ta.get('object_id'):
        return 'vínculo de modelo ausente/divergente'
    try:
        date = dt.date.fromisoformat(ta['data'])
    except (KeyError, TypeError, ValueError):
        return 'data ausente/inválida'
    if date > reference or date.year != ta.get('ano'):
        return 'data futura ou ano divergente'
    return None


def comparar_norma(ta, norma):
    num = lambda s: re.sub(r'\D', '', str(s)).lstrip('0')
    if ta.get('object_id') != norma.get('id'):
        return 'ID oficial divergente'
    if ta.get('data') != norma.get('data') or ta.get('ano') != norma.get('ano') or num(ta.get('numero')) != num(norma.get('numero')):
        return 'número/data/ano divergentes entre TA e norma'
    if re.search(r'\bADI[N]?\b|inconstitucional|suspens', norma.get('observacao', ''), re.I):
        return 'observação judicial exige revisão contextual'
    return None


def executar(host, folder, reference, indice_coerente, excluir_diarios):
    if not re.fullmatch(r'[a-z0-9.-]+\.leg\.br', host):
        raise ValueError('Host deve vir do catálogo oficial .leg.br')
    folder = folder.resolve()
    rede = rede_host(host, 1)
    cache = ROOT / 'municipais/_fonte/texto-articulado-coerente-sapl-20261027' / host
    cache.mkdir(parents=True, exist_ok=True)
    folder.mkdir(parents=True, exist_ok=True)
    coherent, _ = preparar(indice_coerente, host, cache)
    fingerprint = sha(Path(__file__).read_bytes())

    def destino(info):
        final = urlsplit(info.get('url_final', info['url']))
        if final.hostname != host or re.search(r'/(?:accounts?/)?(?:login|captcha)(?:/|$)', final.path, re.I):
            raise PortalBloqueado('Destino externo ou autenticação/desafio; parar para revisão')

    def capture(url):
        if urlsplit(url).hostname != host:
            raise ValueError('URL externa ao portal')
        path = cache / (sha(url.encode()) + '.json' if '/api/' in url else sha(url.encode()) + '.html')
        meta = path.with_suffix('.meta.json')
        # Corpos e APIs de norma antigos permanecem no lugar, referenciados
        # com o timestamp original. Anexos, tipos e casa usam cache novo.
        old = ROOT / 'municipais/_fonte/texto-articulado-sapl' / host / path.name
        if ('/norma/' in url and ('/api/norma/normajuridica/' in url or '/api/' not in url)
                and not path.exists() and not meta.exists()
                and old.exists() and old.with_suffix('.meta.json').exists()):
            info = json.loads(old.with_suffix('.meta.json').read_text())
            raw = old.read_bytes()
            if sha(raw) != info['sha256'] or info['url'] != url:
                raise ValueError('Cache anterior mudou')
            if info['status'] in (401, 403, 429):
                raise PortalBloqueado('Recusa registrada no cache anterior; parar sem contornar')
            destino(info)
            return raw, info, old
        if path.exists() and meta.exists():
            info = json.loads(meta.read_text())
            raw = path.read_bytes()
            if sha(raw) != info['sha256']:
                raise ValueError('Cache mudou')
            if info['status'] in (401, 403, 429):
                raise PortalBloqueado('Bloqueio registrado; parar portal sem contornar')
            destino(info)
            return raw, info, path
        rede.limite.esperar()
        req = urllib.request.Request(url, headers={**rede.headers, 'Accept-Encoding': 'identity'})
        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                raw = response.read()
                info = {'url': url, 'url_final': response.geturl(), 'status': response.status,
                        'content_type': response.headers.get('Content-Type', '')}
        except urllib.error.HTTPError as err:
            raw = err.read()
            info = {'url': url, 'url_final': err.geturl(), 'status': err.code, 'content_type': ''}
        except urllib.error.URLError as err:
            raise PortalBloqueado('Transporte interrompido; parar para revisão: ' + repr(err)) from err
        info.update({'sha256': sha(raw), 'bytes': len(raw), 'capturado_em': dt.datetime.now(ZoneInfo('America/Recife')).isoformat()})
        path.write_bytes(raw)
        meta.write_text(json.dumps(info, ensure_ascii=False, indent=2))
        if info['status'] in (401, 403, 429):
            raise PortalBloqueado('HTTP' + str(info['status']) + '; parar portal sem contornar')
        destino(info)
        return raw, info, path

    def api(url):
        raw, info, path = capture(url)
        if info['status'] != 200:
            raise ValueError('API indisponível: HTTP' + str(info['status']))
        return json.loads(raw), {'arquivo': str(path.relative_to(ROOT)), **info}

    types, typesproof = api('https://' + host + '/api/compilacao/tipotextoarticulado/')
    kinds = {r['id']: r for r in types['results']}
    house, houseproof = api('https://' + host + '/api/base/casalegislativa/')
    if len(house.get('results', [])) != 1:
        raise ValueError('Casa oficial ambígua')
    house = house['results'][0]
    ibge = json.loads((ROOT / 'municipais/_indice/ibge-municipios.json').read_text())
    matches = [r for r in ibge if normalizar_chave(r['nome']) == normalizar_chave(house['municipio']) and r['regiao-imediata']['regiao-intermediaria']['UF']['sigla'] == house['uf']]
    if len(matches) != 1 or str(matches[0]['id']) != str(coherent['vinculo_sigi']['codigo_ibge']):
        raise ValueError('Identidade IBGE divergente')
    annexes = []
    annexproof = []
    annexpage = 1
    annextotal = None
    annexseen = set()
    try:
        while annexpage:
            data, proof = api(f'https://{host}/api/norma/anexonormajuridica/?page_size=100&page={annexpage}')
            annexproof.append(proof)
            pagination = data['pagination']
            if annextotal is None:
                annextotal = int(pagination['total_entries'])
            if int(pagination['total_entries']) != annextotal:
                raise ValueError('Relação de anexos mudou durante paginação')
            for record in data['results']:
                if record['id'] in annexseen or not all(k in record for k in ('id', 'norma', 'anexo_arquivo')):
                    raise ValueError('Anexo sem identidade ou repetido')
                annexseen.add(record['id'])
                annexes.append(record)
            annexpage = pagination.get('next_page')
        if len(annexes) != annextotal:
            raise ValueError('Relação de anexos incompleta')
        annexresult = {'estado': 'indice_completo', 'total': annextotal, 'anexos': annexes, 'evidencias': annexproof}
    except PortalBloqueado:
        raise
    except Exception as err:
        annexresult = {'estado': 'pendente_api', 'erro': str(err), 'evidencias': annexproof}
    (folder / 'anexos-index.json').write_text(json.dumps(annexresult, ensure_ascii=False, indent=2))
    page = 1
    seen = set()
    checkpoint = folder / 'checkpoint.json'
    completed = json.loads(checkpoint.read_text()) if checkpoint.exists() else {}
    journal = folder / 'resultados.jsonl'
    exclusions = []
    for prior_path in excluir_diarios:
        prior_raw = prior_path.read_bytes()
        if prior_raw and not prior_raw.endswith(b'\n'):
            raise ValueError('Diário anterior incompleto; reconciliar antes de retomar')
        for line in prior_raw.decode().splitlines():
            prior = json.loads(line)
            if prior['host'] != host:
                raise ValueError('Diário de outro host')
            completed.setdefault(str(prior['ta_id']), {'estado': 'retido', 'origem': 'excluído por diário anterior; não repetir'})
        exclusions.append(dict(arquivo=str(prior_path.relative_to(ROOT)), sha256=sha(prior_raw), bytes=len(prior_raw)))
    (folder / 'exclusoes-diarios.json').write_text(json.dumps(exclusions, ensure_ascii=False, indent=2) + '\n')
    if journal.exists():
        for line in journal.read_text().splitlines():
            prior = json.loads(line)
            # Uma falha local de caminho da primeira execução não é defeito
            # da fonte. Reprocessar somente esses IDs, reutilizando o cache.
            if 'is not in the subpath' in str(prior.get('pendencia', '')):
                completed.pop(str(prior['ta_id']), None)
            else:
                completed[str(prior['ta_id'])] = {'estado': prior['estado']}
    indexproof = []
    expected = None
    while page:
        data, proof = api(f'https://{host}/api/compilacao/textoarticulado/?page_size=100&page={page}')
        indexproof.append(proof)
        pagination = data.get('pagination', {})
        if expected is None:
            expected = pagination.get('total_entries', data.get('count'))
        for ta in data['results']:
            if ta['id'] in seen:
                raise ValueError('ID repetido na paginação')
            seen.add(ta['id'])
            if str(ta['id']) in completed:
                continue
            row = {'host': host, 'ta_id': ta['id'], 'norma_id': ta.get('object_id'),
                   'codigo_ibge': str(matches[0]['id']), 'metadado_ta': ta,
                   'estado': 'retido', 'pendencia': elegibilidade(ta, kinds, reference)}
            try:
                if row['pendencia']:
                    continue
                norma, np = api(f'https://{host}/api/norma/normajuridica/{ta["object_id"]}/')
                row['metadado_norma'] = norma
                row['prova_norma'] = np
                row['pendencia'] = comparar_norma(ta, norma)
                if row['pendencia']:
                    continue
                url = f'https://{host}/norma/{ta["object_id"]}'
                raw, hp, source = capture(url)
                row['prova_frontend'] = {'arquivo': str(source.relative_to(ROOT)), **hp}
                final = urlsplit(hp.get('url_final', ''))
                match = re.fullmatch(r'/ta/(\d+)/text/?', final.path)
                if hp['status'] != 200 or final.hostname != host or not match or int(match[1]) != ta['id']:
                    row['pendencia'] = 'TA não confirmado como destino padrão da norma; não inferir versão'
                    continue
                html = decodificar(raw, hp['content_type'])
                body, parsed = converter(html)
                if not parsed.ativos or not re.search(r'\bart(?:igo)?\.?\s*1[º°o.\s]', body, re.I):
                    raise ValueError('Corpo normativo ativo não reconhecido')
                candidate = folder / 'candidatos' / (str(ta['object_id']) + '-' + str(ta['id']) + '.txt')
                candidate.parent.mkdir(exist_ok=True)
                candidate.write_text(body)
                row.update({'estado': 'candidato_estruturado_para_auditoria', 'pendencia': None,
                            'transcricao': str(candidate.relative_to(ROOT)), 'sha256_transcricao': sha(candidate.read_bytes()),
                            'dispositivos_ativos': len(parsed.ativos), 'dispositivos_historicos': len(parsed.historicos),
                            'limite': 'Fonte padrão pública, sem certificação legal. Anexos, identidade literal, tabelas/imagens e efeitos exigem gates adicionais.'})
            except PortalBloqueado as err:
                row['pendencia'] = str(err)
                raise
            except Exception as err:
                row['pendencia'] = str(err)
            finally:
                completed[str(ta['id'])] = {'estado': row['estado']}
                with journal.open('a') as log:
                    log.write(json.dumps(row, ensure_ascii=False) + '\n')
                if len(completed) % 100 == 0:
                    tmp = checkpoint.with_suffix('.tmp')
                    tmp.write_text(json.dumps(completed, ensure_ascii=False))
                    tmp.replace(checkpoint)
                if len(completed) % 500 == 0:
                    print(json.dumps({'host': host, 'metadados': len(completed), 'candidatos': sum(r['estado'] != 'retido' for r in completed.values())}), flush=True)
        nextpage = pagination.get('next_page')
        if nextpage is None and data.get('next'):
            raise ValueError('Paginação inesperada; não adivinhar próximo endereço')
        page = nextpage
        if sha(Path(__file__).read_bytes()) != fingerprint:
            raise ValueError('Código mudou durante a captura')
    result = {'host': host, 'metadados_unicos_observados': len(seen), 'total_api_declarado': expected,
              'catalogo_numericamente_consistente': expected == len(seen),
              'candidatos': sum(r['estado'] != 'retido' for r in completed.values()),
              'publicados': 0, 'prova_tipos': typesproof, 'prova_casa_ibge': houseproof,
              'paginas': indexproof, 'script_sha256': fingerprint,
              'limite': 'Captura e transcrição candidata; contagem não prova integralidade do universo, vigência ou aptidão para publicação.'}
    (folder / 'manifesto.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    checkpoint.write_text(json.dumps(completed, ensure_ascii=False))
    print(json.dumps(result, ensure_ascii=False), flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--host', required=True)
    ap.add_argument('--saida', type=Path, required=True)
    ap.add_argument('--indice-coerente', type=Path, required=True)
    ap.add_argument('--excluir-diario', type=Path, action='append', required=True)
    ap.add_argument('--data-referencia', type=dt.date.fromisoformat, required=True)
    args = ap.parse_args()
    if not re.fullmatch(r'[a-z0-9.-]+\.leg\.br', args.host):
        raise ValueError('Host deve vir do catálogo oficial .leg.br')
    if not (ROOT / '.git').exists():
        raise RuntimeError('Repositório não está montado')
    state = json.loads((ROOT / 'municipais/_lotes/20261021-textos-articulados-fila-sigi/fila.json').read_text())
    if state.get(args.host, {}).get('estado', '').startswith('iniciado'):
        raise ValueError('Host já está na fila viva')
    locks = ROOT / 'municipais/_indice/coleta-ta-coerente-20261027'
    locks.mkdir(parents=True, exist_ok=True)
    marker = locks / (args.host + '.interrompido.json')
    if marker.exists():
        raise PortalBloqueado('Interrupção anterior exige revisão, sem retentativa automática')
    lock = (locks / (args.host + '.lock')).open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    folder = args.saida.resolve() / args.host
    try:
        executar(args.host, folder, args.data_referencia, args.indice_coerente.resolve(), [p.resolve() for p in args.excluir_diario])
    except Exception as error:
        marker.write_text(json.dumps(dict(host=args.host, erro=repr(error), capturado_em=dt.datetime.now(ZoneInfo('America/Recife')).isoformat(), limite='Execução interrompida; revisar checkpoint e fontes antes de qualquer retomada.'), ensure_ascii=False, indent=2) + '\n')
        raise
    finally:
        lock.close()


if __name__ == '__main__':
    main()
