"""Confronto independente de raiz normativa e irmãos preservados, sem remoção."""
import re
import html5lib
from comparadores_HTML5_snapshot import visible,matrices,lists

def tokens(el):return set(re.split(r'[\t\n\f\r ]+',el.attrib.get('class','')))
def conferir(src,fragment):
 full=html5lib.parse(src,treebuilder='etree',namespaceHTMLElements=False);frag=html5lib.parse(fragment,treebuilder='etree',namespaceHTMLElements=False);roots=[e for e in full.iter()if'texto-dou'in tokens(e)];froots=[e for e in frag.iter()if'texto-dou'in tokens(e)];assert len(roots)==len(froots)==1,'Raiz normativa ausente ou concorrente'
 assert visible(roots[0])==visible(froots[0])and matrices(roots[0])==matrices(froots[0])and lists(roots[0])==lists(froots[0]),'Corpo normativo diverge do DOM completo'
 parents={c:p for p in full.iter()for c in p};siblings=list(parents[roots[0]]);pos=siblings.index(roots[0]);body=frag.find('body');children=list(body);assert children and children[0]is froots[0]and not(body.text or'').strip(),'Texto ou elemento estranho antes da raiz';assert not any((e.tail or'').strip()for e in children),'Texto solto após a raiz'
 extras=[]
 for j,e in enumerate(children[1:],1):
  assert pos+j<len(siblings),'Irmão inexistente no documento completo';original=siblings[pos+j];cls=tokens(original);assert original.tag=='p'and bool(cls&{'assina','cargo'})or original.tag=='div'and'informacao-conteudo-dou'in cls,'Irmão externo sem classificação primária admitida'
  assert original.tag==e.tag and original.attrib==e.attrib and visible(original)==visible(e)and matrices(original)==matrices(e)and lists(original)==lists(e),'Irmão externo diverge da fonte completa'
  extras.append({'tag':e.tag,'atributos':e.attrib,'texto_literal':visible(e)})
 return {'raiz_normativa_inteira_igual':True,'irmaos_externos_integrais':extras,'limite':'Classes são da fonte; nenhum irmão foi removido nem convertido em corpo normativo por inferência.'}
