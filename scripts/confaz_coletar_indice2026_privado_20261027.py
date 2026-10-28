"""Coleta autorizada somente do índice CONFAZ 2026, sem canônicos.

Cliente único por flock, 1 rps, TLS curl verificado e cache com timestamps
originais. Históricos e retificações não são limpos nem promovidos.
"""
import argparse
import datetime as dt
import fcntl
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import unicodedata
import urllib.parse
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from confaz_capturar_piloto_privado_v2_20261027 import Recursos,imports
HOST='www.confaz.fazenda.gov.br'
PREFIX='/legislacao/convenios/2026/'


def sha(b):return hashlib.sha256(b).hexdigest()
def now():return dt.datetime.now(ZoneInfo('America/Recife')).isoformat()


def dump(p,value):
    temp=p.with_suffix(p.suffix+'.novo');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');temp.replace(p)


def classify(url):
    path=urllib.parse.unquote(urllib.parse.urlsplit(url).path)
    ascii_path=unicodedata.normalize('NFKD',path).encode('ascii','ignore').decode()
    match=re.search(r'(?:/CV0*(\d+)_26|/convenio-icms-(\d+)-26)',ascii_path,re.I)
    number=int(match[1] or match[2]) if match else None
    kind='retificacao_ou_republicacao' if re.search(r'retifica|republica',ascii_path,re.I) else 'principal' if match and re.fullmatch(r'.*/(?:CV\d+_26|convenio-icms-\d+-26(?:-\d+)?)',ascii_path,re.I) else 'versao_ou_objeto_a_revisar'
    return number,kind


def execute(a):
    assert (ROOT/'.git').is_dir(),'Repositório indisponível; não criar árvore em /Volumes'
    out=a.saida.resolve();out.mkdir(parents=True,exist_ok=False)
    seed_path=a.cache_base.resolve();seed=json.loads(seed_path.read_text())
    captures={};used=set();last=0.;requests=0;validation=[];errors=[];rows=[];fingerprint=sha(Path(__file__).read_bytes())
    for proof in seed['capturas']:
        p=ROOT/proof['arquivo'];raw=p.read_bytes()
        if sha(raw)!=proof['sha256']:raise ValueError('Cache de origem mudou: '+str(p))
        captures[proof['url']]=proof
    index=next(p for p in seed['capturas'] if p['url']=='https://www.confaz.fazenda.gov.br/legislacao/convenios/2026/2026')
    parse=Recursos();parse.feed((ROOT/index['arquivo']).read_text());parse.close();targets={}
    for href in parse.links:
        url=urllib.parse.urldefrag(urllib.parse.urljoin(index['url'],href))[0]
        parsed=urllib.parse.urlsplit(url)
        if parsed.hostname!=HOST or not parsed.path.startswith(PREFIX) or url==index['url']:continue
        url=urllib.parse.quote(url,safe=':/%?=&;,+@!$()*~')
        number,kind=classify(url)
        targets[url]=dict(url=url,numero_indice=number,ano=2026,tipo_link_indice=kind)
    if not targets:raise ValueError('Índice não forneceu objetos no escopo 2026')
    (out/'indice-targets.json').write_text(json.dumps(dict(fonte=index,targets=list(targets.values())),ensure_ascii=False,indent=2)+'\n')

    def get(url,category):
        nonlocal last,requests
        if urllib.parse.urlsplit(url).hostname!=HOST:raise ValueError('Recurso externo não coletado: '+url)
        prior=captures.get(url)
        # CSS com cachekey mantém o snapshot imutável. Outros CSS são
        # revalidados uma vez, sem rebatizar a captura antiga em caso de 304.
        revalidate=category=='css' and prior and 'cachekey-' not in url and url not in used
        if prior and not revalidate:
            used.add(url);return prior,'cache'
        if url in used:
            return captures[url],'cache'
        time.sleep(max(0.,1-(time.monotonic()-last)))
        assert (ROOT/'.git').is_dir(),'Volume indisponível; parar antes de criar novos diretórios'
        key=sha(url.encode());transfer=out/(key+'.transfer');headers_path=out/(key+'.headers');stderr=out/(key+'.stderr')
        command=['/usr/bin/curl','-q','--silent','--show-error','--max-time','60','--proto','=https',
            '--user-agent','Mozilla/5.0 (compatible; Constituicao-acervo-piloto/1.0)','--header','Accept-Encoding: identity',
            '--dump-header',str(headers_path),'--output',str(transfer),'--write-out','%{http_code}\n%{url_effective}\n%{ssl_verify_result}\n']
        if revalidate:
            old_headers={k.lower():v for k,v in prior.get('headers',{}).items()}
            if old_headers.get('etag'):command+=['--header','If-None-Match: '+old_headers['etag']]
            elif old_headers.get('last-modified'):command+=['--header','If-Modified-Since: '+old_headers['last-modified']]
        started=now();p=subprocess.run(command+[url],stdout=subprocess.PIPE,stderr=subprocess.PIPE);stderr.write_bytes(p.stderr)
        last=time.monotonic();requests+=1;result=p.stdout.decode().splitlines()
        if p.returncode or len(result)!=3 or result[2]!='0':raise RuntimeError('Transporte/TLS falhou; sem insecure: '+p.stderr.decode(errors='replace'))
        response_headers={}
        for line in headers_path.read_text().splitlines():
            k,sep,v=line.partition(':')
            if sep:response_headers[k.strip()]=v.strip()
        status=int(result[0]);raw=transfer.read_bytes() if transfer.exists() else b''
        info=dict(url=url,url_final=result[1],status=status,headers=response_headers,categoria=category,sha256=sha(raw),bytes=len(raw),
            capturado_em_cliente=now(),inicio_requisicao=started,ssl_verify_result=int(result[2]),headers_arquivo=str(headers_path.relative_to(ROOT)),stderr_arquivo=str(stderr.relative_to(ROOT)))
        if status==304 and revalidate:
            validation.append(dict(**info,cache_fonte=prior['arquivo'],sha256_cache=prior['sha256']))
            if transfer.exists():transfer.unlink()
            used.add(url);return prior,'cache_revalidado_304'
        suffix='.css' if category=='css' else '.html';path=out/(key+suffix);meta=path.with_suffix('.meta.json')
        path.write_bytes(raw);meta.write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
        if transfer.exists():transfer.unlink()
        proof=dict(arquivo=str(path.relative_to(ROOT)),metadata=str(meta.relative_to(ROOT)),**info)
        captures[url]=proof;used.add(url)
        print(json.dumps(dict(url=url,status=status,bytes=len(raw))),flush=True)
        if status in {401,403,429}:
            dump(a.controle_host/'bloqueio-http.json',proof);dump(out/'bloqueio.json',proof)
            raise RuntimeError('Recusa HTTP; parar host sem contornar')
        if 300<=status<400:raise RuntimeError('Redirecionamento não seguido automaticamente; exige revisão')
        if status==200 and category=='html':
            text=raw.decode('utf-8',errors='replace')
            if 'parent-fieldname-text' not in text and re.search(r'captcha|just a moment|verify you are human|access denied|login_form',text,re.I):
                dump(a.controle_host/'bloqueio-http.json',proof);raise RuntimeError('Recusa/challenge sem campo normativo; parar host')
        return proof,'nova_captura'

    css_seen=set()
    def css_dependencies(proof):
        html=(ROOT/proof['arquivo']).read_bytes().decode('utf-8');parser=Recursos();parser.feed(html);parser.close();queue=[]
        for item in parser.css:queue.append(urllib.parse.urljoin(proof['url_final'],item['href']))
        for item in parser.styles:
            for child in imports(item['texto']):queue.append(urllib.parse.urljoin(proof['url_final'],child))
        pending=[]
        while queue:
            url=queue.pop(0)
            if url in css_seen:continue
            resource,_=get(url,'css');css_seen.add(url)
            if resource['status']!=200:pending.append(dict(url=url,status=resource['status']));continue
            text=(ROOT/resource['arquivo']).read_bytes().decode('utf-8')
            for child in imports(text):queue.append(urllib.parse.urljoin(resource['url_final'],child))
        return pending

    try:
        for item in targets.values():
            if sha(Path(__file__).read_bytes())!=fingerprint:raise RuntimeError('Código mudou durante execução')
            proof,origin=get(item['url'],'html');row=dict(**item,fonte=proof,origem=origin,estado='captura_sem_qualificacao')
            if proof['status']==200:
                row['css_pendentes']=css_dependencies(proof)
                if row['css_pendentes']:row['estado']='retido_css_incompleto'
            else:row['estado']='retido_http_nao_200'
            rows.append(row)
            with (out/'resultados.jsonl').open('a') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
            dump(out/'checkpoint.json',dict(processados=len(rows),total=len(targets),ultima_url=item['url'],requisicoes=requests))
    except Exception as error:errors.append(dict(erro=type(error).__name__+': '+str(error)))
    manifest=dict(escopo='Índice CONFAZ de 2026, conforme snapshot ROOT fornecido; nenhum outro ano.',indice=index,
        total_indice=len(targets),processados=len(rows),documentos=rows,capturas=list(captures.values()),verificacoes_cache=validation,
        novas_requisicoes=requests,css_usados=sorted(css_seen),incompletos=errors,codigo_sha256=fingerprint,
        cache_base=dict(path=str(seed_path.relative_to(ROOT)),sha256=sha(seed_path.read_bytes())),
        limite='Somente captura privada. Nenhum canônico, vigência ou qualificação inferidos. Históricos, retificações, anexos e tachas exigem modos explícitos e permanecem sujeitos a retenção na QA.')
    (out/'manifesto-captura.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(total=len(targets),processados=len(rows),novas_requisicoes=requests,incompletos=len(errors))),flush=True)
    return int(bool(errors))


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cache-base',type=Path,required=True);ap.add_argument('--saida',type=Path,required=True);ap.add_argument('--controle-host',type=Path,default=ROOT/'reguladores/_indice/confaz-cliente-20261027');a=ap.parse_args()
    assert (ROOT/'.git').is_dir();a.controle_host.mkdir(parents=True,exist_ok=True)
    if (a.controle_host/'bloqueio-http.json').exists():raise RuntimeError('Recusa já registrada; não reiniciar automaticamente')
    with (a.controle_host/'cliente.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return execute(a)


if __name__=='__main__':raise SystemExit(main())
