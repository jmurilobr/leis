from pathlib import Path
import subprocess,re,hashlib,json
r=subprocess.run(['git','diff','--cached','--check'],capture_output=True);lines=r.stdout.decode().split('\n');points={};i=0;whitelist=json.loads(Path('_fonte/operacao_root_20261027/municipal352-publicar-hashes.json').read_text())
while i<len(lines):
 line=lines[i]
 if not line:i+=1;continue
 m=re.fullmatch(r'(municipais/.+\.(?:md|txt)):(\d+): (trailing whitespace\.|new blank line at EOF\.)',line);assert m,line;path,n,kind=m[1],int(m[2]),m[3];assert (path.startswith('municipais/_indice/_recuperacao_20261027/') and path.endswith('.txt') and ('/transcricoes-preservadas/' in path or '/exportados/' in path)) or path.endswith('.md') or path in {'municipais/_indice/_recuperacao_20261027/buritis8-tachados-reparo-privado-20261027/candidato.txt','municipais/_indice/_recuperacao_20261027/buritis8-tachados-reparo-privado-v2-20261027/candidato.txt','municipais/_indice/_recuperacao_20261027/css-glifos-ta4735-20261027/porto-velho-controle-1-preimagem.md.txt','municipais/_indice/_recuperacao_20261027/css-glifos-ta4735-20261027/porto-velho-controle-2-preimagem.md.txt','municipais/_indice/_recuperacao_20261027/css-glifos-ta4735-20261027/porto-velho-controle-3-preimagem.md.txt'} or ('/candidatos/' in path and path.startswith(('municipais/_lotes/','municipais/_indice/_recuperacao_20261027/')) and path.endswith('.txt')),path;points.setdefault(path,{'hardbreaks':[],'eof':[]})['hardbreaks' if kind=='trailing whitespace.' else 'eof'].append(n);i+=2 if kind=='trailing whitespace.' else 1
p=subprocess.Popen(['git','cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE);proof={}
for path,nums in points.items():
 p.stdin.write((':'+path+'\n').encode());p.stdin.flush();h=p.stdout.readline().split();assert len(h)==3;data=p.stdout.read(int(h[2]));assert p.stdout.read(1)==b'\n';assert hashlib.sha256(data).hexdigest()==whitelist[path],path;ls=data.split(b'\n')
 for n in nums['hardbreaks']:
  line=ls[n-1];assert line.endswith(b'  ') and not line.endswith(b'   ') and line.rstrip()==line[:-2],(path,n)
 for n in nums['eof']:assert all(x in (b'',b'  ') for x in ls[n-1:]),(path,n)
 proof[path]={'sha256_md':hashlib.sha256(data).hexdigest(),**nums}
p.stdin.close();assert p.wait()==0;out={'hardbreaks':sum(len(v['hardbreaks']) for v in proof.values()),'eof':sum(len(v['eof']) for v in proof.values()),'criterio':'Somente quebras de exatamente dois espacos e finais vazios comprovados no index; nenhuma outra classe dispensada.','arquivos':proof};Path('scripts/dados/municipais352-whitespace-root-20261028.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n');subprocess.run(['git','-c','core.whitespace=-blank-at-eol,-blank-at-eof','diff','--cached','--check'],check=True);print({k:v for k,v in out.items() if k!='arquivos'})
