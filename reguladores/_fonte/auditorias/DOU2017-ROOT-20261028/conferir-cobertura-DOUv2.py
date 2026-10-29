from pathlib import Path
import json,gzip,hashlib,subprocess,re
sha=lambda b:hashlib.sha256(b).hexdigest();B=Path('reguladores/_fonte/auditorias/orgao_dedup_2017_20261028_002');mp=B/'cobertura_v2_manifesto.json';assert sha(mp.read_bytes())=='b9bba20f3721d112aa17620c152729b2a729ffac4af82121356eff0357f782b1';m=json.loads(mp.read_bytes())
for r in m['arquivos']:
 p=Path(r['path']);assert p.stat().st_size==r['bytes'] and sha(p.read_bytes())==r['sha256'],str(p)
i=json.loads(gzip.decompress((B/'indice_transversal_v2.json.gz').read_bytes()));t=gzip.decompress((B/'federal_HEAD_tree_completo.z.gz').read_bytes());head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();assert subprocess.check_output(['git','ls-tree','-rz',i['HEAD'],'--','federal'])==t;subprocess.run(['git','diff','--quiet',i['HEAD'],head,'--','federal'],check=True)
canon={}
for r in t.split(b'\0'):
 if not r:continue
 d,p=r.split(b'\t',1);mode,kind,oid=d.split();path=p.decode()
 if kind==b'blob' and path.endswith('.md') and not any(x.startswith('_') for x in Path(path).parts):canon[path]=oid.decode()
rows={r['path']:r for r in i['registros']};held={r['path']:r for r in i['reservas']};assert len(rows)==174393 and len(held)==14615 and not set(rows)&set(held) and set(rows)|set(held)==set(canon) and len(canon)==189008
for p,r in {**rows,**held}.items():assert r['OID']==canon[p],p
fallback=list(map(json.loads,gzip.decompress((B/'metadados_fallback_OID.jsonl.gz').read_bytes()).splitlines()));assert len(fallback)==16915 and len({r['path'] for r in fallback})==16915;proc=subprocess.Popen(['git','cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE);bindings={}
for r in fallback:
 p=r['path'];assert r['OID']==canon[p];proc.stdin.write((r['OID']+'\n').encode());proc.stdin.flush();hdr=proc.stdout.readline().split();assert hdr[0].decode()==r['OID'] and hdr[1]==b'blob';raw=proc.stdout.read(int(hdr[2]));assert proc.stdout.read(1)==b'\n' and len(raw)==r['bytes_MD_HEAD'] and sha(raw)==r['sha256_MD_HEAD'];header=raw[4:].split(b'\n---\n',1)[0].decode() if raw.startswith(b'---\n') and b'\n---\n' in raw[4:] else None;assert header==r['cabecalho_UTF8_completo'];bindings[p]={'OID':r['OID'],'sha256_MD':sha(raw)}
proc.stdin.close();assert proc.wait()==0;assert head==subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();out={'HEAD_ROOT':head,'HEAD_snapshot':i['HEAD'],'manifesto':str(mp),'sha256_manifesto':sha(mp.read_bytes()),'artefatos_conferidos':len(m['arquivos']),'MD_canonicos':len(canon),'registros_com_chave':len(rows),'reservas_sem_chave':len(held),'fallbacks_lidos_integrais_por_OID':len(fallback),'blobs':bindings,'limite':'ROOT verificou toda árvore e ausência de delta federal, partição exata de caminhos/OIDs e hashes/cabeçalhos dos 16.915 fallbacks lidos integralmente. Não é dedup universal e não libera os 14.615 sem chave. Comparabilidade e conteúdo dos candidatos exigem replay separado.'};p=Path('_fonte/operacao_root_20261027/DOUv2-cobertura-root.json');assert not p.exists();p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in out.items() if k!='blobs'})
