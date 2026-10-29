"""Complemento final: IO relativo e dependências locais, sem tocar no antecedente."""
from pathlib import Path
import sys,json,hashlib,shutil,importlib,importlib.metadata,subprocess,difflib
E=Path(__file__).resolve().parent;R=E.parents[3];A=E.with_name('export730_legado87_20261028_001');sha=lambda b:hashlib.sha256(b).hexdigest();sys.path[:0]=[str(R/'scripts/bin/qa-20261027/python'),str(R/'scripts/bin/qa-html5-20261027/python')];vendor=E/'vendor/python';vendor.mkdir(parents=True);libs=[]
for module,distname in [('markdown_it','markdown-it-py'),('mdurl','mdurl'),('html5lib','html5lib'),('webencodings','webencodings'),('six','six')]:
 mod=importlib.import_module(module);src=Path(mod.__file__);dist=importlib.metadata.distribution(distname)
 if src.name=='__init__.py':shutil.copytree(src.parent,vendor/module,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 else:shutil.copy2(src,vendor/src.name)
 metadata_path=Path(dist._path);shutil.copytree(metadata_path,vendor/metadata_path.name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'));libs.append({'modulo':module,'distribuicao':distname,'versao':dist.version,'origem_local':str(src),'limites':'Versão usada no complemento, sem inventar pinagem antecedente que não foi registrada.'})
(E/'vendor/marked-LICENSE.txt').write_bytes((R/'reguladores/_fonte/auditorias/orgao_dedup_2017_20261028_002/codigo/marked-LICENSE.txt').read_bytes())
for name in ['mapa_versoes.json','versoes_exportadas.py','original_promover730.py','original_replay730.py','original_recibo730.json','original_recibo_promocao730.json']:(E/name).write_bytes((A/name).read_bytes())
s=(A/'replay730_export.py').read_text();s=s.replace("sys.path.insert(0,str(B/'codigo/scripts'));sys.path.insert(0,str(ROOT/'scripts/bin/qa-20261027/python'));sys.path.insert(0,str(ROOT/'scripts/bin/qa-html5-20261027/python'))","sys.path.insert(0,str(ROOT/'federal/_fonte/auditorias/export730_legado87_20261028_001/codigo/scripts'));sys.path.insert(0,str(B/'vendor/python'))")
uri=(A/'codigo/vendor/marked.esm.mjs').as_uri();replacement='"+(ROOT/\'federal/_fonte/auditorias/export730_legado87_20261028_001/codigo/vendor/marked.esm.mjs\').as_uri()+"';assert uri in s;s=s.replace(uri,replacement)
s=s.replace("import html5lib","for path,digest in export['vendor_sha256'].items():assert sha((ROOT/path).read_bytes())==digest,path\nimport html5lib",1);(E/'replay730_export.py').write_text(s)
p=(A/'promover730_export.py').read_text();(E/'promover730_export.py').write_text(p)
for original,name in [(A/'original_replay730.py','replay730_export.py'),(A/'original_promover730.py','promover730_export.py')]:
 (E/(name+'.patch')).write_text(''.join(difflib.unified_diff(original.read_text().splitlines(True),(E/name).read_text().splitlines(True),fromfile=original.name,tofile=name)))
receipt=json.loads((A/'recibo_exportacao.json').read_bytes());receipt['sha256_replay_exportado']=sha((E/'replay730_export.py').read_bytes());receipt['sha256_promotor_exportado']=sha((E/'promover730_export.py').read_bytes());receipt['sha256_resolvedor']=sha((E/'versoes_exportadas.py').read_bytes());receipt['vendor_sha256']={str(p.relative_to(R)):sha(p.read_bytes())for p in(E/'vendor').rglob('*')if p.is_file()};receipt['limites']='IO relativo ao repositório, módulos originais por SHA no export antecedente e bibliotecas Python locais. Comparadores, candidatos e SHAs originais preservados. Default dry-run; --apply exclusivo ROOT.';(E/'recibo_exportacao.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');(E/'runtime.json').write_text(json.dumps({'python':sys.version,'node':subprocess.check_output(['node','--version'],text=True).strip(),'bibliotecas':libs,'arquivos_vendor':len(receipt['vendor_sha256'])},ensure_ascii=False,indent=2)+'\n')
for name in ['testes_limites_export.py','testes_seguranca_export.py','test_isolamento_export.py']:
 s=(A/name).read_text().replace("B/'codigo/scripts'","ROOT/'federal/_fonte/auditorias/export730_legado87_20261028_001/codigo/scripts'").replace("B/'codigo/federal/_fonte/auditorias/alimentacao_normas_20261028_019/qualificar_snapshot_v4.py'","ROOT/'federal/_fonte/auditorias/export730_legado87_20261028_001/codigo/federal/_fonte/auditorias/alimentacao_normas_20261028_019/qualificar_snapshot_v4.py'")
 (E/name).write_text(s)
print('Bibliotecas locais',libs,'arquivos',len(receipt['vendor_sha256']),flush=True)
