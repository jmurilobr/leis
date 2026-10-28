"""Piloto limitado CONFAZ: seis convênios e CSS, um cliente, sem canônicos.

Reutiliza as três sondagens ROOT sem rebatizar a cópia como captura nova.
Para em 401/403/429. Não cria Markdown, não decide vigência e não publica.
"""
import argparse
import datetime as dt
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parent.parent
HOST='www.confaz.fazenda.gov.br'
PROBE=ROOT/'reguladores/_fonte/auditorias/confaz-probe-root-20261027'


def sha(b):return hashlib.sha256(b).hexdigest()


class Recursos(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links=[];self.css=[];self.styles=[];self.active_style=None

    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag=='a' and d.get('href'):self.links.append(d['href'])
        if tag=='link' and 'stylesheet' in d.get('rel','').split() and d.get('href'):
            self.css.append(dict(href=d['href'],media=d.get('media','all')))
        if tag=='style':self.active_style=dict(media=d.get('media','all'),partes=[])

    def handle_data(self,data):
        if self.active_style is not None:self.active_style['partes'].append(data)

    def handle_endtag(self,tag):
        if tag=='style' and self.active_style is not None:
            item=self.active_style;self.styles.append(dict(media=item['media'],texto=''.join(item['partes'])));self.active_style=None


def imports(text):
    # tinycss2 é usado depois para a auditoria semântica; aqui apenas enumera
    # URLs explícitas de @import. Arquivos completos são preservados.
    return [a or b or c for a,b,c in re.findall(r'@import\s+(?:url\(\s*["\']?([^\s"\')]+)["\']?\s*\)|"([^"]+)"|\'([^\']+)\')',text,re.I)]


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--saida',type=Path,required=True);a=ap.parse_args()
    out=a.saida.resolve();out.mkdir(parents=True,exist_ok=False)
    captures={};last=0.0;requests=0;css_origins={};incomplete=[]

    def save(url,raw,info):
        suffix='.css' if info['categoria']=='css' else '.html'
        p=out/(sha(url.encode())+suffix);m=p.with_suffix('.meta.json')
        p.write_bytes(raw);m.write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
        proof=dict(arquivo=str(p.relative_to(ROOT)),metadata=str(m.relative_to(ROOT)),**info)
        captures[url]=proof;return proof

    for i,info in enumerate(json.loads((PROBE/'recibo.json').read_text())):
        raw=(PROBE/f'{i:02}.html').read_bytes();assert sha(raw)==info['sha256'] and info['status']==200
        save(info['url'],raw,dict(url=info['url'],url_final=info['url_final'],status=info['status'],headers=info['headers'],
            sha256=sha(raw),bytes=len(raw),categoria='html',capturado_em_cliente=None,
            captura_http_date=info['headers'].get('Date'),origem_sondagem=str((PROBE/f'{i:02}.html').relative_to(ROOT)),
            limite_data='Sondagem ROOT anterior reutilizada; HTTP Date preservado, timestamp do cliente não fornecido. Cópia não representa captura nova.'))

    def get(url,category):
        nonlocal last,requests
        if url in captures:return captures[url]
        if urllib.parse.urlsplit(url).hostname!=HOST:raise ValueError('Dependência externa ao host não autorizada no piloto: '+url)
        time.sleep(max(0,1-(time.monotonic()-last)))
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; Constituicao-acervo-piloto/1.0)','Accept-Encoding':'identity'})
        try:
            with urllib.request.urlopen(req,timeout=45) as response:
                raw=response.read();info=dict(url=url,url_final=response.geturl(),status=response.status,headers=dict(response.headers.items()))
        except urllib.error.HTTPError as error:
            raw=error.read();info=dict(url=url,url_final=url,status=error.code,headers=dict(error.headers.items()))
        last=time.monotonic();requests+=1
        info.update(sha256=sha(raw),bytes=len(raw),categoria=category,capturado_em_cliente=dt.datetime.now(ZoneInfo('America/Recife')).isoformat())
        proof=save(url,raw,info)
        print(json.dumps(dict(url=url,status=info['status'],bytes=len(raw))),flush=True)
        if info['status'] in {401,403,429}:
            (out/'bloqueio.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
            raise RuntimeError('Fonte bloqueada; piloto interrompido sem contornar')
        if info['status']!=200:raise RuntimeError('HTTP não 200; CSS/fonte incompletos')
        if urllib.parse.urlsplit(info['url_final']).hostname!=HOST:raise RuntimeError('Redirecionamento externo exige revisão')
        return proof

    index_url=json.loads((PROBE/'recibo.json').read_text())[1]['url']
    p=Recursos();p.feed((ROOT/captures[index_url]['arquivo']).read_text());p.close()
    selected={}
    for href in p.links:
        url=urllib.parse.urldefrag(urllib.parse.urljoin(index_url,href))[0]
        if urllib.parse.urlsplit(url).hostname!=HOST:continue
        path=urllib.parse.urlsplit(url).path
        match=re.search(r'/2026/(?:CV0*(\d+)_26|convenio-icms-(\d+)-26(?:-\d+)?)$',path,re.I)
        if not match:continue
        n=int(match[1] or match[2])
        if 121<=n<=126:
            if n in selected and selected[n]!=url:raise ValueError('Dois links distintos para o mesmo convênio no índice')
            selected[n]=url
    if set(selected)!=set(range(121,127)):raise ValueError('Índice não comprova os seis controles solicitados')
    pages=[];queue=[]
    try:
        for n,url in sorted(selected.items()):
            proof=get(url,'html');pages.append(dict(numero=n,ano=2026,url=url,fonte=proof))
            r=Recursos();r.feed((ROOT/proof['arquivo']).read_text());r.close()
            for item in r.css:
                cssurl=urllib.parse.urljoin(url,item['href']);queue.append(cssurl);css_origins.setdefault(cssurl,[]).append(dict(pagina=url,media=item['media'],tipo='link'))
            for i,item in enumerate(r.styles):
                for href in imports(item['texto']):
                    cssurl=urllib.parse.urljoin(url,href);queue.append(cssurl);css_origins.setdefault(cssurl,[]).append(dict(pagina=url,media=item['media'],tipo='style @import',bloco=i))
        done=set()
        while queue:
            url=queue.pop(0)
            if url in done:continue
            if len(done)>=50:raise RuntimeError('Mais de 50 dependências CSS; piloto permanece incompleto, sem coleta volumosa')
            proof=get(url,'css');done.add(url)
            raw=(ROOT/proof['arquivo']).read_bytes();text=raw.decode('utf-8')
            for href in imports(text):
                child=urllib.parse.urljoin(proof['url_final'],href);queue.append(child);css_origins.setdefault(child,[]).append(dict(css=url,tipo='CSS @import'))
    except Exception as error:
        incomplete.append(dict(erro=type(error).__name__+': '+str(error)))
    manifest=dict(piloto=True,coleta_volumosa=False,paginas=pages,capturas=list(captures.values()),css_origens=css_origins,
        requisicoes_novas=requests,cliente_unico=True,limite_por_host='1 requisição por segundo',incompletos=incomplete,
        codigo_sha256=sha(Path(__file__).read_bytes()),limite='Nenhuma publicação ou afirmação de vigência. Fontes preservam condições de ratificação/efeitos; CSS e versões históricas ainda exigem auditoria independente.')
    (out/'manifesto-captura.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(paginas=len(pages),capturas=len(captures),novas_requisicoes=requests,incompletos=len(incomplete))),flush=True)
    return int(bool(incomplete))


if __name__=='__main__':raise SystemExit(main())
