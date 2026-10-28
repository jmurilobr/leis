from pathlib import Path
import json,subprocess,hashlib
from PIL import Image
sha=lambda b:hashlib.sha256(b).hexdigest();B=Path('federal/_fonte/auditorias/recuperacao18351-ROOT-render-20261028');B.mkdir(exist_ok=False);m=json.loads(Path('federal/_fonte/auditorias/clbr_recuperacoes1945_20261028_002/candidato18351.json').read_bytes());pdf=m['fonte_PDF_anual'];assert sha(Path(pdf['path']).read_bytes())==pdf['sha256'];proof=[]
for a in m['ativos_em_ordem_impressa']:
 q=B/Path(a['path']).stem;cmd=['pdftoppm','-f',str(a['pagina_PDF']),'-l',str(a['pagina_PDF']),'-r','300','-png','-singlefile']
 if a['recorte']:
  for key in ['x','y','W','H']:cmd.extend(['-'+key,str(a['recorte'][key])])
 subprocess.run(cmd+[pdf['path'],str(q)],check=True);q=q.with_suffix('.png');p=Path(a['path']);assert sha(p.read_bytes())==a['sha256'];one=Image.open(p);two=Image.open(q);assert one.size==two.size and one.mode==two.mode and one.tobytes()==two.tobytes(),str(p);proof.append({'ativo':str(p),'sha256_ativo':sha(p.read_bytes()),'render_ROOT':str(q),'sha256_render_ROOT':sha(q.read_bytes()),'pixels_sha256':sha(one.tobytes()),'dimensoes':one.size,'modo':one.mode,'igualdade_pixels':True,'pagina_impressa':a['pagina_impressa'],'pagina_PDF':a['pagina_PDF']})
p=B/'recibo.json';p.write_text(json.dumps({'fonte':pdf,'ativos':proof,'aprovados':22,'limite':'Render ROOT independente Poppler 300 dpi, recorte inicial direto e 22 ativos pixel iguais. Complementa inspeção visual de todas as folhas e provas bibliográficas; não certifica vigência nem outra edição.'},ensure_ascii=False,indent=2)+'\n');print('22/22 imagens 18351 pixel iguais')
