from pathlib import Path
import json,subprocess,hashlib
from PIL import Image
B=Path('federal/_fonte/auditorias/recuperacao53480-ROOT-render-20261028');B.mkdir(exist_ok=False);m=json.loads(Path('federal/_fonte/auditorias/recuperacao53480_facs_20261028_003/candidato53480.json').read_text());pdf=m['fonte_primaria']['path'];sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(Path(pdf).read_bytes())==m['fonte_primaria']['sha256']
subprocess.run(['pdftoppm','-f','135','-l','153','-r','300','-png',pdf,str(B/'pagina')],check=True)
for name,rect in [('p81-esquerda-ato',[200,1380,710,1138]),('p81-direita-ato',[900,150,800,2300])]:
 x,y,w,h=rect;subprocess.run(['pdftoppm','-f','135','-l','135','-r','300','-x',str(x),'-y',str(y),'-W',str(w),'-H',str(h),'-png','-singlefile',pdf,str(B/name)],check=True)
proof=[]
for a in m['ativos_em_ordem_de_leitura']:
 p=Path(a['path']);q=B/p.name;assert q.exists(),q;one=Image.open(p);two=Image.open(q);assert one.size==two.size and one.mode==two.mode and one.tobytes()==two.tobytes(),str(p);proof.append({'ativo':str(p),'sha256_ativo':sha(p.read_bytes()),'render_ROOT':str(q),'sha256_render_ROOT':sha(q.read_bytes()),'pixels_sha256':sha(one.tobytes()),'dimensoes':one.size,'modo':one.mode,'igualdade_pixels':True})
p=B/'recibo.json';p.write_text(json.dumps({'fonte':m['fonte_primaria'],'ativos':proof,'aprovados':20,'limite':'ROOTrenderindependentePoppler300dpi e recortesdiretos; vinteativos pixeliguais. Complementa inspeção visual de20ativos,capa/índices/scanoriginal. Não certificaoutraediçãoDOU ouvigência.'},ensure_ascii=False,indent=2)+'\n');print('20/20imagens53480pixeliguais em renderROOTindependente')
