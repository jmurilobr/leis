"""QA escopado de textos HTML integrais recentes ES/SE; sem promoção canônica."""
import gzip,hashlib,json,re,datetime
from pathlib import Path
from urllib.parse import urljoin
from lxml import html
from markdown_it import MarkdownIt
from comum import decodificar
from html2md import convert
from pe_fidelidade_visivel import texto_visivel_html,assinatura_numerica
SHA=lambda b:hashlib.sha256(b).hexdigest()
MESES={m:i for i,m in enumerate('janeiro fevereiro março abril maio junho julho agosto setembro outubro novembro dezembro'.split(),1)}
BRASAO_SE='e28829cca5ca685d2f9462e54c508b5a2800f26803bab460ed7eb9e7f9eb826f'

def identidade(text,item):
    m=re.search(r'\b(LEI(?: COMPLEMENTAR)?)\s+N[º°.]*(?:\s+)([\d.]+),?\s+DE\s+(\d{1,2})\s+DE\s+([A-ZÇ]+)\s+DE\s+(\d{4})',text[:900],re.I)
    if not m:raise ValueError('epígrafe própria ausente')
    tipo='Lei Complementar' if m[1].upper()=='LEI COMPLEMENTAR' else 'Lei Ordinária';date=f'{m[5]}-{MESES[m[4].lower()]:02d}-{int(m[3]):02d}'
    if (tipo,m[2].replace('.',''),date)!=(item['tipo'],item['numero'],item['data']):raise ValueError('identidade própria diverge do cartão')
    if not re.search(r'\bArt[.]\s*1[º°.]?\s',text):raise ValueError('artigo próprio inicial ausente')
    f=re.search(r'\bAracaju,\s*(\d{1,2})\s+de\s+([a-zç]+)\s+de\s+(\d{4})',text,re.I)
    if not f or f'{f[3]}-{MESES[f[2].lower()]:02d}-{int(f[1]):02d}'!=date:raise ValueError('data do fecho diverge')
    return dict(epigrafe=m[0],fecho=f[0],data=date,numero=m[2].replace('.',''),tipo=tipo)

def comparar(source,body):
    parser=MarkdownIt('commonmark',{'html':True}).enable('table');tokens=parser.parse(body)
    if any(t.type=='ordered_list_open' for t in tokens):raise ValueError('contadores CommonMark exigem revisão contextual')
    v=texto_visivel_html(parser.render(body));s=texto_visivel_html(source)
    if s!=v or assinatura_numerica(s)!=assinatura_numerica(v):raise ValueError('texto visível/sinais divergem da fonte integral')
    return dict(sha256_visivel_fonte=SHA(s.encode()),sha256_visivel_commonmark=SHA(v.encode()),sha256_html_renderizado=SHA(parser.render(body).encode()),caracteres_visiveis=len(s))

def auditar(captura,imagens,body_atual=None):
    r=captura;it=r['item'];z=Path(r['cache']).read_bytes();b=gzip.decompress(z)
    if r['http']!=200 or SHA(z)!=r['sha256_cache'] or SHA(b)!=r['sha256_fonte']:raise ValueError('fonte/captura diverge')
    if r['url'] not in it['textos_completos_observados'] or r['url_final']!=r['url']:raise ValueError('link integral não observado/redirect inesperado')
    source=decodificar(b)
    if '\ufffd' in source:raise ValueError('decodificação contém substituição')
    doc=html.fromstring(source);bodies=doc.xpath('//body')
    if len(bodies)!=1:raise ValueError('body não único')
    if any(k.lower().startswith('on') for e in doc.iter() for k in e.attrib):raise ValueError('evento ativo exige revisão')
    if any(re.match(r'\s*(javascript|vbscript):',v,re.I) for e in doc.iter() for k,v in e.attrib.items() if k.lower() in ('href','src')):raise ValueError('URL ativa exige revisão')
    if re.search(r'@import\b',source,re.I):raise ValueError('CSS importado exige captura/contexto')
    if doc.xpath('//script|//iframe|//object|//embed|//svg|//canvas|//del|//strike|//s'):raise ValueError('ativo, visual ou tachado exige revisão')
    if doc.xpath('//link[translate(@rel,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="stylesheet"]'):raise ValueError('CSS externo não capturado')
    if re.search(r'line-through|display\s*:\s*none|visibility\s*:\s*hidden|mso-hide\s*:',source,re.I):raise ValueError('CSS potencialmente oculto/tachado exige revisão')
    if bodies[0].xpath('.//ol|.//ul'):raise ValueError('listas HTML exigem prova de contadores')
    proof=[]
    for node in doc.xpath('//img'):
        url=urljoin(r['url_final'],node.get('src',''));m=[x for x in imagens if x.get('url')==url and x.get('id')==it['id']]
        if len(m)!=1 or m[0]['http']!=200 or m[0]['sha256']!=BRASAO_SE or SHA(Path(m[0]['arquivo']).read_bytes())!=BRASAO_SE:raise ValueError('imagem sem prova literal do brasão revisto')
        proof.append(dict(url=url,sha256=BRASAO_SE,arquivo=m[0]['arquivo'],revisao='Brasão oficial de Sergipe examinado visualmente; apenas decorativo.'))
    if len(proof)!=1:raise ValueError('esperado exatamente um brasão no escopo revisto')
    # Só a tag raster cujo recurso foi conferido é omitida da apresentação textual.
    filtered=re.sub(r'<img\b[^>]*>','',source,flags=re.I);body=convert(filtered)
    q=identidade(texto_visivel_html(source),it);q.update(comparar(source,body));q.update(imagens=proof,total_tabelas=len(doc.xpath('//table')),sha256_corpo=SHA(body.encode()),sha256_fonte=SHA(b),codificacao='UTF-16 com BOM' if b.startswith((b'\xff\xfe',b'\xfe\xff')) else 'charset/meta e decodificação estrita sem U+FFFD',limite='Fidelidade ao HTML integral publicado pela ALESE; não certifica igualdade à edição DOE. Alinhamento, fonte e CSS de apresentação não são reproduzidos integralmente pelo Markdown.')
    if body_atual is not None and body_atual!=body:raise ValueError('corpo privado diverge da reconversão')
    return body,q
