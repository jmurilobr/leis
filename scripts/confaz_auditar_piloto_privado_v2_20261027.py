"""Auditoria privada CONFAZ v2: campo integral, CSS e renderização independente.

Não filtra redações antigas nem decide efeitos. Tachados, histórico, recursos
visuais ou CSS potencialmente oculto ficam retidos para tratamento explícito.
"""
import argparse
import datetime as dt
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import unicodedata
import urllib.parse

ROOT=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/bin/qa-confaz-20261027/python'),
             str(ROOT/'scripts/bin/qa-html5-20261027/python'),str(ROOT/'scripts/bin/qa-20261027/python')]
import cssselect2
import html5lib
import tinycss2
from markdown_it import MarkdownIt
from confaz_capturar_piloto_privado_v2_20261027 import Recursos
from representacao_html_dou_v2 import _SemNewlinesSensiveis,assinatura_dom
from representacao_html_dou import _CSS_RISCO
from estados.pe_fidelidade_visivel import texto_visivel_html,assinatura_numerica
from auditar_dou_css_tabelas_privado_20261027 import matrizes

ID='parent-fieldname-text'


def normal(text):return ' '.join(unicodedata.normalize('NFKD',text).encode('ascii','ignore').decode().upper().split())
def sha(b):return hashlib.sha256(b).hexdigest()


class Extrator(HTMLParser):
    def __init__(self,text):
        super().__init__(convert_charrefs=False);self.text=text;self.starts=[0]+[m.end() for m in re.finditer('\n',text)];self.depth=0;self.begin=None;self.fields=[]
    def position(self):
        line,column=self.getpos();return self.starts[line-1]+column
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag=='div' and d.get('id')==ID:
            if self.depth:raise ValueError('Campo normativo aninhado/duplicado')
            self.begin=self.position();self.depth=1
        elif tag=='div' and self.depth:self.depth+=1
    def handle_endtag(self,tag):
        if tag=='div' and self.depth:
            self.depth-=1
            if self.depth==0:
                pos=self.position();end=pos+self.text[pos:].index('>')+1
                self.fields.append(self.text[self.begin:end]);self.begin=None


def campo(text):
    p=Extrator(text);p.feed(text);p.close()
    if p.depth or len(p.fields)!=1:raise ValueError('Não há exatamente um campo normativo fechado')
    return p.fields[0]


class Validador(_SemNewlinesSensiveis):
    def handle_starttag(self,tag,attrs):
        if not self.abriu:
            if tag!='div' or dict(attrs).get('id')!=ID:raise ValueError('Raiz diferente do campo CONFAZ')
            self.abriu=True
        super().handle_starttag(tag,attrs)
        cls=dict(attrs).get('class','')
        if re.search(r'(?:redacao|texto|versao)[_-]?(?:anterior|antig)|historico',normal(cls).replace(' ',''),re.I):
            raise ValueError('Classe histórica exige versão e tratamento explícitos')


def representar(fragment):
    text=fragment.replace('\r\n','\n').replace('\r','\n')
    p=Validador(text);p.feed(text);p.close()
    if not p.abriu or not p.fechou or p.divs:raise ValueError('Campo não fechado')
    swaps=[]
    for m in re.finditer(r'[ \t]+(?=\n|$)',text):
        if not any(a<=m.start() and m.end()<=b for a,b in p.textos):raise ValueError('Whitespace em tag/atributo exige revisão')
        swaps.append((m.start(),m.end(),''.join('&#32;' if c==' ' else '&#9;' for c in m[0])))
    output=text
    for a,b,value in reversed(swaps):output=output[:a]+value+output[b:]
    p=Validador(output);p.feed(output);p.close()
    positions=[]
    for m in re.finditer(r'(?m)^[ \t]*\n',output):
        pos=m.end()-1
        if not any(a<=pos<b for a,b in p.textos):raise ValueError('Linha vazia em tag/atributo')
        positions.append(pos)
    for pos in reversed(positions):output=output[:pos]+'&#10;'+output[pos+1:]
    if assinatura_dom(text)!=assinatura_dom(output):raise ValueError('DOM textual ou atributos alterados')
    return output


def identidade(text):
    value=normal(text)
    m=re.match(r'CONVENIO\s+ICMS\s+(?:N[.Oº°]*\s*)?(\d[\d.]*)\s*,?\s*DE\s+(\d{1,2})\s+DE\s+([A-Z]+)\s+DE\s+((?:19|20)\d{2})\b',value)
    if not m:raise ValueError('Epígrafe ICMS com número/data completos não comprovada')
    months={name:i+1 for i,name in enumerate(['JANEIRO','FEVEREIRO','MARCO','ABRIL','MAIO','JUNHO','JULHO','AGOSTO','SETEMBRO','OUTUBRO','NOVEMBRO','DEZEMBRO'])}
    n,day,month,year=m.groups();date=dt.date(int(year),months[month],int(day))
    return dict(tipo='Convênio ICMS',numero=int(n.replace('.','')),ano=int(year),data=date.isoformat(),epigrafe_normalizada=m[0])


def import_url(prelude):
    tokens=[t for t in prelude if t.type not in {'whitespace','comment'}]
    if not tokens:return None
    first=tokens[0]
    if first.type in {'url','string'}:return first.value
    if first.type=='function' and first.lower_name=='url':return tinycss2.serialize(first.arguments).strip().strip('\"\'')
    return None


def auditar_css(page,url,captures):
    parser=html5lib.HTMLParser(tree=html5lib.getTreeBuilder('etree'));doc=parser.parse(page)
    root=cssselect2.ElementWrapper.from_html_root(doc);all_wrappers=list(root.iter_subtree())
    targets=[w for w in all_wrappers if w.etree_element.get('id')==ID]
    if len(targets)!=1:raise ValueError('Campo CSS não único')
    relevant=list(targets[0].iter_subtree());ancestor=targets[0].parent
    while ancestor is not None:relevant.append(ancestor);ancestor=ancestor.parent
    resources=Recursos();resources.feed(page);resources.close();sources=[];incomplete=[];seen=set()

    def load(cssurl,contexts):
        cssurl=urllib.parse.urljoin(url,cssurl)
        if cssurl in seen:return
        seen.add(cssurl)
        proof=captures.get(cssurl)
        if not proof:incomplete.append(dict(url=cssurl,motivo='CSS importado sem captura'));return
        raw=(ROOT/proof['arquivo']).read_bytes()
        if sha(raw)!=proof['sha256'] or proof['status']!=200:raise ValueError('Prova CSS divergente')
        headers={k.lower():v for k,v in proof.get('headers',{}).items()}
        if not headers.get('content-type','').lower().startswith('text/css'):
            incomplete.append(dict(url=cssurl,motivo='Resposta não comprova MIME text/css'));return
        sources.append((raw.decode('utf-8'),cssurl,contexts))

    for item in resources.css:load(urllib.parse.urljoin(url,item['href']),[item['media']])
    for i,item in enumerate(resources.styles):sources.append((item['texto'],url+'#style-'+str(i),[item['media']]))
    rules=[];cursor=0
    def parse(nodes,origin,contexts):
        for rule in nodes:
            if rule.type=='error':incomplete.append(dict(origem=origin,motivo='Erro de parsing CSS',erro=rule.message))
            elif rule.type=='at-rule' and rule.lower_at_keyword=='import':
                child=import_url(rule.prelude)
                if child:
                    childurl=urllib.parse.urljoin(origin.split('#',1)[0],child)
                    load(childurl,contexts+['@import '+tinycss2.serialize(rule.prelude)])
                else:incomplete.append(dict(origem=origin,motivo='@import sem URL comprovada'))
            elif rule.type=='at-rule' and rule.content is not None and rule.lower_at_keyword in {'media','supports','layer','container'}:
                parse(tinycss2.parse_rule_list(rule.content,skip_whitespace=True,skip_comments=True),origin,contexts+['@'+rule.lower_at_keyword+' '+tinycss2.serialize(rule.prelude)])
            elif rule.type=='qualified-rule':
                declarations=tinycss2.parse_declaration_list(rule.content,skip_whitespace=True,skip_comments=True)
                sensitive=[]
                for d in declarations:
                    if d.type!='declaration':continue
                    value=tinycss2.serialize(d.value).strip();declaration=d.lower_name+':'+value
                    if _CSS_RISCO.search(declaration) or (d.lower_name=='font-family' and re.search(r'wingdings|webdings|symbol',value,re.I)) or d.lower_name in {'counter-increment','counter-reset'} or (d.lower_name=='content' and value not in {'','none','normal','""',"''"}) or (d.lower_name in {'animation','animation-name'} and value!='none'):
                        sensitive.append(dict(propriedade=d.lower_name,valor=value,important=d.important))
                if sensitive:rules.append(dict(seletor=tinycss2.serialize(rule.prelude).strip(),declaracoes=sensitive,origem=origin,contextos=contexts))
    while cursor<len(sources):
        text,origin,contexts=sources[cursor];cursor+=1
        parse(tinycss2.parse_stylesheet(text,skip_whitespace=True,skip_comments=True),origin,contexts)
    risks=[]
    for rule in rules:
        selector=rule['seletor']
        # Sobreaproxima estados transitórios. Uma regra potencialmente aplicável
        # retém o caso; não declara ocultação efetiva ou revogação jurídica.
        selector=re.sub(r':not\(\s*:(?:hover|active|visited|focus|target|checked)\s*\)','',selector)
        selector=re.sub(r':(?:hover|active|visited|link|focus(?:-within|-visible)?|target|checked|disabled|enabled)\b','',selector)
        try:compiled=cssselect2.compile_selector_list(selector)
        except cssselect2.SelectorError as error:
            incomplete.append(dict(regra=rule,motivo='Seletor sensível não comprovado',erro=str(error)));continue
        matches=[]
        for w in relevant:
            if any(s.test(w) for s in compiled):
                e=w.etree_element;matches.append(dict(tag=e.tag.rsplit('}',1)[-1],id=e.get('id'),classe=e.get('class'),texto=' '.join(''.join(e.itertext()).split())[:240]))
        if matches:risks.append(dict(regra=rule,elementos=matches,limite='Regra potencial, sem resolver cascade/media; tratamento explícito necessário antes de liberar.'))
    return dict(css_capturados=sorted(seen),regras_sensiveis=len(rules),riscos_aplicaveis=risks,incompletos=incomplete,
                criterio='CSS completos e imports capturados; tinycss2/cssselect2 sobre a árvore HTML5 completa, incluindo ancestrais. Regras sensíveis são conservadoramente retidas; não se infere revogação de todo ato.')


def historico_identificado(fragment):
    doc=html5lib.parseFragment(fragment,treebuilder='etree');ns='{http://www.w3.org/1999/xhtml}';found=[]
    for element in doc.iter(ns+'p'):
        text=' '.join(''.join(element.itertext()).split());cls=element.get('class') or ''
        if re.search(r'(?:RedacaoAnt(?:erior)?|RemissaoAnt(?:erior)?)(?:\b|[ _-])',cls,re.I) or re.match(r'^(?:REDACAO|TEXTO|VERSAO) (?:ANTERIOR|ORIGINAL)\b',normal(text)):
            found.append(dict(classe=cls,texto_literal=text,criterio='Rótulo ou classe editorial da própria fonte identifica redação anterior/original; não é inferência de revogação do ato.'))
    return found


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--captura',type=Path,required=True);ap.add_argument('--saida',type=Path,required=True);a=ap.parse_args()
    manifest=json.loads((a.captura/'manifesto-captura.json').read_text());assert not manifest['incompletos']
    captures={p['url']:p for p in manifest['capturas']};a.saida.mkdir(parents=True,exist_ok=False)
    engine=MarkdownIt('commonmark',{'html':True}).enable('table').enable('strikethrough');rows=[]
    ns='{http://www.w3.org/1999/xhtml}'
    for item in manifest['paginas']:
        proof=item['fonte'];raw=(ROOT/proof['arquivo']).read_bytes();assert sha(raw)==proof['sha256']
        page=raw.decode('utf-8');field=campo(page);directory=a.saida/str(item['numero']);directory.mkdir()
        (directory/'campo-original.html').write_text(field)
        r=dict(numero_indice=item['numero'],ano_indice=item['ano'],fonte=proof,estado='retido',css=auditar_css(page,item['url'],captures))
        try:
            identity=identidade(texto_visivel_html(field));assert identity['numero']==item['numero'] and identity['ano']==item['ano']
            r['identidade']=identity
            history=historico_identificado(field);r['historico_identificado']=history
            if history:
                r['versao']='Compilação com redações anteriores/originais identificadas pela fonte; retida até modo explícito de versões.'
                raise ValueError('Histórico declarado pela fonte exige versão e tratamento próprios; igualdade textual não libera o caso')
            native=representar(field)
            rendered=engine.render(native)
            assert texto_visivel_html(field)==texto_visivel_html(rendered),'Texto visível integral diverge'
            assert assinatura_numerica(texto_visivel_html(field))==assinatura_numerica(texto_visivel_html(rendered)),'Numeração/sinais divergem'
            assert matrizes(field)[0]==matrizes(rendered)[0],'Distribuição de células/tabelas HTML5 diverge'
            if r['css']['incompletos'] or r['css']['riscos_aplicaveis']:raise ValueError('CSS sensível/inconclusivo; nenhuma liberação por simples igualdade textual')
            doc=html5lib.parseFragment(field,treebuilder='etree');notes=[];effects=[];links=[]
            for e in doc.iter():
                text=' '.join(''.join(e.itertext()).split())
                if e.tag==ns+'p':
                    if 'A2DataPublicacao' in (e.get('class') or '').split():notes.append(text)
                    if re.search(r'entra(?:m)? em vigor|produz\w* efeitos|ratifica',text,re.I):effects.append(text)
                if e.tag==ns+'a' and e.get('href'):links.append(dict(url=e.get('href'),texto=text))
            binary=[l for l in links if re.search(r'\.(?:pdf|docx?|xlsx?)(?:$|[?#])|@@download',l['url'],re.I)]
            if binary:raise ValueError('Arquivo externo no campo exige prova de escopo/anexo: '+str(binary))
            (directory/'representacao.html').write_text(native)
            (directory/'render-commonmark.html').write_text(rendered)
            r.update(estado='representacao_privada_verificada_aguarda_confronto_HEAD',sha256_campo=sha(field.encode()),
                sha256_representacao=sha(native.encode()),sha256_visivel=sha(texto_visivel_html(field).encode()),
                notas_publicacao_ratificacao_literais=notes,condicoes_efeitos_literais=effects,links=links,
                prova=dict(dom_textual_atributos_preservados=True,texto_visivel_integral=True,assinatura_numerica=True,matrizes_html5=True),
                versao='Texto e notas oficiais do portal CONFAZ conforme a captura; não se afirma vigência ou edição original imutável.')
        except Exception as error:r['motivo']=type(error).__name__+': '+str(error)
        (directory/'controle.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');rows.append(r)
    output=dict(piloto=True,resultados=rows,aprovados_representacao=sum(r['estado'].startswith('representacao') for r in rows),retidos=sum(r['estado']=='retido' for r in rows),
        runtime=dict(html5lib=html5lib.__version__,tinycss2=tinycss2.__version__,cssselect2=cssselect2.__version__),
        limite='Nenhuma promoção, coleta volumosa ou inferência de vigência. Ainda exige confronto independente com HEAD por tipo/número/ano; aliases DOU/CONFAZ não contam como normas novas.')
    (a.saida/'resumo.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(aprovados_representacao=output['aprovados_representacao'],retidos=output['retidos'])))


if __name__=='__main__':main()
