"""Diagnóstico privado dos estilos inline em dispositivos ativos; sem rede."""
from pathlib import Path
import argparse,hashlib,json,re,sys
from lxml import html
R=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(R/'scripts/bin/qa-20261027/python'));sys.path.insert(0,str(R/'scripts'))
from auditar_commonmark_ta_v2 import AtivosIndependentes

def sha(raw):return hashlib.sha256(raw).hexdigest()

def riscos(node):
 result=[]
 for e in node.iter():
  if not isinstance(e.tag,str):continue
  text=' '.join(e.itertext()).strip()
  if not text:continue
  style=e.get('style','');causes=[]
  if 'hidden' in e.attrib:causes.append('atributo hidden')
  for pattern,name in [(r'(?i)(?:^|;)\s*display\s*:\s*none\b','display none'),(r'(?i)(?:^|;)\s*visibility\s*:\s*(?:hidden|collapse)\b','visibility hidden/collapse'),(r'(?i)(?:^|;)\s*opacity\s*:\s*0(?:\.0*)?\s*(?:!important\s*)?(?:;|$)','opacity zero'),(r'(?i)(?:^|;)\s*font-size\s*:\s*0(?:\.0*)?(?:px|pt|em|rem|%)?\s*(?:!important\s*)?(?:;|$)','font-size zero')]:
   if re.search(pattern,style):causes.append(name)
  if causes:result.append(dict(tag=e.tag,atributos=dict(e.attrib),texto=text,causas=causes))
 return result

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--manifesto',type=Path,action='append',required=True);ap.add_argument('--saida',type=Path,required=True);a=ap.parse_args();reports=[];seen=set();alerts=[];rev=[]
 for manifest in a.manifesto:
  m=json.loads(manifest.read_text());mapping=Path(m['mapeamento_fontes']);rows=json.loads(mapping.read_text());names=set(Path(m['lista_normas']).read_text().splitlines());assert names=={r['path'] for r in rows}
  for r in rows:
   assert r['path'] not in seen;seen.add(r['path']);source=r.get('prova_frontend') or r['fonte'];raw=Path(source['arquivo']).read_bytes();assert sha(raw)==source['sha256'];assert sha(Path(r['path']).read_bytes())==r['sha256']
   p=AtivosIndependentes();p.feed(raw.decode());p.close();doc=html.fromstring(raw)
   for ident in p.ativos:
    nodes=doc.xpath('//*[@id=$ident]',ident=ident);assert len(nodes)==1
    # Dispositivos históricos aninhados não pertencem à seleção ativa.
    node=html.fromstring(html.tostring(nodes[0]))
    for child in node.xpath('.//*[contains(concat(" ",normalize-space(@class)," ")," desativado ")]'):child.drop_tree()
    found=riscos(node)
    if found:alerts.append(dict(path=r['path'],sha256_MD=r['sha256'],sha256_HTML=sha(raw),id=ident,riscos=found))
    if 'revogado' in node.get('class','').split() and not re.search(r'\brevogad[oa]\b',node.text_content(),re.I):rev.append(dict(path=r['path'],sha256_MD=r['sha256'],sha256_HTML=sha(raw),id=ident,texto=node.text_content()))
   reports.append(dict(path=r['path'],sha256_MD=r['sha256'],sha256_HTML=sha(raw),ativos=len(p.ativos)))
 with a.saida.open('x') as f:json.dump(dict(normas=len(seen),manifestos=[dict(path=str(x),sha256=sha(x.read_bytes())) for x in a.manifesto],riscos_inline=alerts,classe_revogado_sem_rotulo_literal=rev,verificados=reports,codigo_sha256=sha(Path(__file__).read_bytes()),limite='Somente atributos hidden e estilos inline diretos dos dispositivos ativos, excluindo históricos explicitamente desativados. Não certifica CSS externo, ancestral, dinâmica JavaScript ou vigência jurídica. Achados exigem revisão contextual; não presume revogação do ato.'),f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps(dict(normas=len(seen),riscos_inline=len(alerts),revogado_sem_rotulo=len(rev))))

if __name__=='__main__':main()
