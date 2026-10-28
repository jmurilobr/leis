"""Congela metadados TA antes dos corpos, sem misturar paginas de epocas distintas.

Somente indice: nao gera normas, nao altera caches anteriores nem confirma
integralidade juridica. Bloqueios 403/429 interrompem a fonte sem nova tentativa.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit
import urllib.request
import urllib.error
from zoneinfo import ZoneInfo
sys.path.insert(0,str(Path(__file__).resolve().parent))
from baixar_organicas_sapl import rede_host
from comum import normalizar_chave
ROOT=Path(__file__).resolve().parent.parent

def sha(raw):return hashlib.sha256(raw).hexdigest()

class FonteInterrompida(RuntimeError):pass

def paginar(api,host):
    page=1;pages=set();ids=set();rows=[];proofs=[];expected=None
    while page is not None:
        if type(page) is not int or page<1 or page in pages:raise ValueError('Paginacao ciclica ou invalida')
        pages.add(page);data,proof=api(f'https://{host}/api/compilacao/textoarticulado/?page_size=100&page={page}');proofs.append(proof);p=data.get('pagination',{});total=p.get('total_entries',data.get('count'))
        if type(total) is not int or total<0:raise ValueError('Total oficial ausente/invalido')
        if expected is None:expected=total
        if total!=expected:raise ValueError('Total mudou durante congelamento')
        for row in data['results']:
            if type(row.get('id')) is not int or row['id'] in ids:raise ValueError('ID repetido/invalido na pagina '+str(page))
            ids.add(row['id']);rows.append(row)
        page=p.get('next_page')
        if page is None and data.get('next'):raise ValueError('Proximo endereco sem numero; nao inferir')
    if len(ids)!=expected:raise ValueError('Catalogo nao fecha com total oficial')
    return rows,proofs,expected

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--host',required=True);ap.add_argument('--saida',type=Path,required=True);a=ap.parse_args();host=a.host
    if not re.fullmatch(r'[a-z0-9.-]+\.leg\.br',host):raise ValueError('Origem oficial .leg.br exigida')
    block_marker=ROOT/'municipais/_indice/organicas-sapl'/host/'bloqueio-http-indice-ta.json'
    if block_marker.exists():raise FonteInterrompida('Bloqueio persistente registrado; exige revisao manual')
    # Nao usar outra pasta para ultrapassar bloqueio ja registrado no portal.
    for meta in (ROOT/'municipais/_fonte/texto-articulado-sapl'/host).rglob('*.meta.json'):
        if json.loads(meta.read_text()).get('status') in (403,429):raise FonteInterrompida('Bloqueio anterior registrado; nao recapturar automaticamente')
    catalog=json.loads((ROOT/'municipais/_indice/organicas-sapl/sigi/catalogo.json').read_text())['candidatos_sapl'];links=[r for r in catalog if urlsplit(r['url']).hostname==host];bindings={(str(r['codigo_ibge']),normalizar_chave(r['municipio']),r['uf']) for r in links}
    if len(bindings)!=1:raise ValueError('Vinculo SIGI ausente/ambiguo')
    binding=links[0];a.saida.mkdir(parents=True,exist_ok=False);rede=rede_host(host,1);captured=[]
    def api(url):
        if urlsplit(url).hostname!=host:raise ValueError('URL fora da origem')
        rede.limite.esperar();request=urllib.request.Request(url,headers={**rede.headers,'Accept-Encoding':'identity'})
        try:
            with urllib.request.urlopen(request,timeout=90) as response:
                raw=response.read();info=dict(url=url,url_final=response.geturl(),status=response.status,content_type=response.headers.get('Content-Type',''))
        except urllib.error.HTTPError as exc:
            raw=b'';info=dict(url=url,url_final=exc.geturl(),status=exc.code,content_type='')
        info.update(sha256=sha(raw),bytes=len(raw),capturado_em=dt.datetime.now(ZoneInfo('America/Recife')).isoformat());path=a.saida/(sha(url.encode())+'.json');meta=path.with_suffix('.meta.json');path.write_bytes(raw);meta.write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n');proof=dict(arquivo=str(path),metadata=str(meta),**info);captured.append(proof)
        if info['status'] in (403,429):
            block_marker.parent.mkdir(parents=True,exist_ok=True)
            block_marker.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
            raise FonteInterrompida('HTTP '+str(info['status'])+'; parar portal')
        if info['status']!=200 or urlsplit(info['url_final']).hostname!=host:raise FonteInterrompida('Fonte indisponivel ou redirecionada; parar portal')
        return json.loads(raw),proof
    try:
        house,hproof=api('https://'+host+'/api/base/casalegislativa/');records=house.get('results',[])
        if len(records)!=1 or normalizar_chave(records[0].get('municipio',''))!=normalizar_chave(binding['municipio']) or records[0].get('uf')!=binding['uf']:raise ValueError('Casa diverge do vinculo SIGI')
        rows,proofs,total=paginar(api,host)
        (a.saida/'metadados.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows));result=dict(coerente=True,host=host,total=total,ids_unicos=len(rows),vinculo_sigi=binding,prova_casa=hproof,paginas=proofs,corpos_capturados=0,normas_publicadas=0,limite='Indice numericamente coerente deste snapshot. Sem corpos, sem afirmar cobertura juridica ou vigencia.')
    except Exception as exc:
        result=dict(coerente=False,host=host,erro=type(exc).__name__+': '+str(exc),capturas=captured,corpos_capturados=0,normas_publicadas=0)
    result['codigo_sha256']=sha(Path(__file__).read_bytes());(a.saida/'manifesto.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('paginas','capturas','prova_casa','vinculo_sigi')},ensure_ascii=False),flush=True)
    return int(not result['coerente'])
if __name__=='__main__':raise SystemExit(main())
