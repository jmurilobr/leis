"""Gate offline estreito: fragmento ALMG somente p, sem atributos/objetos próprios."""
from pathlib import Path
import csv,gzip,hashlib,json,re,xml.etree.ElementTree as ET
from lxml import html
from markdown_it import MarkdownIt
SHA=lambda b:hashlib.sha256(b).hexdigest()
PARSER=MarkdownIt('commonmark',{'html':True})

def metadata(blob):
    head,body=blob.split(b'\n---\n',1);meta={}
    for line in head.decode().splitlines()[1:]:
        if ': ' not in line:continue
        k,v=line.split(': ',1)
        try:meta[k]=json.loads(v)
        except json.JSONDecodeError:meta[k]=v
    return meta,body

def compact(text):return ''.join(c for c in text if not c.isspace())

def fiel(source,body):
    root=html.fromstring('<div>'+source+'</div>')
    for e in root.iter():
        if e is root:continue
        if e.tag!='p' or e.attrib:raise ValueError('elemento/atributo fora do perfil p sem atributos')
    if re.search(r'anex|tabela|aprova|conv[eê]nio|omiti|n[aã]o reproduz',root.text_content(),re.I):raise ValueError('objeto/remissão/omissão exige contexto separado')
    rendered=html.fromstring('<div>'+PARSER.render(body)+'</div>')
    a=compact(root.text_content());b=compact(rendered.text_content())
    if a!=b:raise ValueError('caractere visível divergiu; números/sinais/pontuação não normalizados')
    return dict(sha256_visivel_sem_brancos=SHA(a.encode()),igualdade_literal_nao_branca=True,normalizacao='Somente whitespace de layout; pontuação, sinais, Unicode e algarismos exatos.',tags_fonte=['p'],atributos_fonte=0)

def auditar(root,doc):
    root=Path(root);blob=(root/doc['path']).read_bytes();meta,body=metadata(blob)
    if SHA(blob)!=doc['sha256_md']:raise ValueError('MD mudou')
    source=gzip.decompress((root/doc['cache']).read_bytes()).decode('utf8')
    xml=gzip.decompress((root/doc['xml']).read_bytes())
    if ET.fromstring(xml).findtext('.//conteudo')!=source:raise ValueError('fragmento não corresponde ao XML primário')
    row=doc['CSV'];rows=list(csv.DictReader((root/doc['indice']).open(encoding='utf8',newline='')))
    matches=[r for r in rows if all(r[k]==row[k] for k in ['Tipo','Numero','Ano','Complemento'])]
    if len(matches)!=1 or matches[0]!=row:raise ValueError('identidade CSV ausente/ambígua/modificada')
    if meta['numero']!=row['Numero'] or row['Complemento']:raise ValueError('número/sufixo fora do perfil')
    if meta['data']!='-'.join(reversed(row['DataLegislacao'].split('/'))):raise ValueError('data não confere')
    if meta['situacao'].upper()!=row['Situacao'].upper() or row['Situacao']!='VIGENTE' or meta['revogada'] is not False:raise ValueError('situação não comprovada literalmente')
    if meta['versao_texto']!='original' or row['LinkTextoAtualizado']:raise ValueError('edição fora do perfil original API')
    if meta['fonte']!=row['LinkTextoOriginal'].replace('conteudo=true&',''):raise ValueError('fonte fora da identidade oficial')
    if meta['ementa']!=' '.join(row['Ementa'].split()):raise ValueError('ementa difere do CSV')
    content=body.decode().split('\n\n',1)[1];proof=fiel(source,content)
    if not re.search(r'(?i)Artigo\s+(?:1|[uú]nico)',content):raise ValueError('dispositivo próprio fora do perfil')
    return dict(path=doc['path'],**proof,sha256_fonte=SHA(source.encode()),sha256_XML=SHA(xml),identidade_CSV_literal=True,situacao_literal=row['Situacao'],data_literal=row['DataLegislacao'],epigrafe='O fragmento dedicado pode não imprimir o número; identidade pelo endpoint XML oficial e CSV anual, sem usar H1 gerado como prova.',edicao='Transcrição API ALMG identificada como texto original tipoDoc142, não cotejada com edição impressa/PDF.',captura='Data 2026-10-16 registrada pelo coletor original; timestamp HTTP não disponível neste lote offline.')
