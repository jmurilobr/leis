"""Revisão independente offline: hashes, pixels, ordem impressa e vínculos do fac-símile."""
from pathlib import Path
import json,hashlib,re,posixpath,subprocess
from PIL import Image,ImageChops
R=Path.cwd(); B=R/'federal/_fonte/auditorias/revisao_independente18351_vigencia_20261028'; O=R/'federal/_fonte/auditorias/clbr_recuperacoes1945_20261028_001'
sha=lambda b:hashlib.sha256(b).hexdigest()
c=json.loads((O/'candidato18351.json').read_text()); entries=json.loads((O/'entrega18351-hashes.json').read_text())
for e in entries:
 b=(R/e['path']).read_bytes(); assert sha(b)==e['sha256'] and len(b)==e['bytes'],e['path']
a=c['ativos_em_ordem_impressa']; assert [e['pagina_impressa'] for e in a]==list(range(132,154)); assert sorted(e['pagina_PDF'] for e in a)==list(range(1082,1104))
checks=[]
for e in a:
 im=Image.open(B/f"pdf-{e['pagina_PDF']}.png").convert('RGB')
 if e['recorte']:
  q=e['recorte']; im=Image.open(B/'p132-recorte-direto.png').convert('RGB')  # Poppler renderiza o recorte diretamente; não recorta um raster já renderizado.
 other=Image.open(R/e['path']).convert('RGB'); assert im.size==other.size; assert ImageChops.difference(im,other).getbbox() is None,e['path']
 checks.append({'pagina_impressa':e['pagina_impressa'],'pagina_PDF':e['pagina_PDF'],'pixels_identicos':True,'recorte':e['recorte'],'destino':e['destino'],'sha256':e['sha256']})
for ours,theirs in [('capa_IV.png','render/capa_IV.png'),('indice_XIV.png','render/indice_18351_pXIV.png')]:
 x=Image.open(B/ours).convert('RGB'); y=Image.open(O/theirs).convert('RGB'); assert x.size==y.size and ImageChops.difference(x,y).getbbox() is None
md=(R/c['candidato']['path']).read_text(); links=re.findall(r'!\[[^\]]*\]\(([^)]+)\)',md)
resolved=[posixpath.normpath(posixpath.join(posixpath.dirname(c['path_canonico']),x)) for x in links]; assert resolved==[e['destino'] for e in a],resolved
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(); original=subprocess.check_output(['git','show',f"HEAD:{c['path_canonico']}"]); assert sha(original)==c['preimagem']['sha256']
result={'HEAD':head,'preimagem_HEAD_sha256':sha(original),'hashes_da_entrega_verificados':len(entries),'pixels_identicos':len(checks),'capa_PDF877_identica':True,'indice_PDF890_identico':True,'links_22_exatos_em_ordem':True,'paginas':checks}
(B/'pixels-e-ordem.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='paginas'},ensure_ascii=False))
