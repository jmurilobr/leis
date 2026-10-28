import json,hashlib,datetime
from pathlib import Path
SHA=lambda b:hashlib.sha256(b).hexdigest()
base=Path(__file__).parent
m=json.load(open('scripts/estados/manifestos/se8782-8783-duvida-cronologica-20261027-001.json'));rows=[]
for r in m['documentos']:
 old=Path(r['preimagem']).read_bytes();assert SHA(old)==r['sha256_MD'];head,body=old.split(b'\n---\n',1)
 note='Epígrafe, fecho e cartão da ALESE indicam 06/11/2020; o rodapé editorial transcrito informa D.O.E. de 27/10/2020. Divergência da referência de edição ainda não cotejada com o DOE primário; datas, demais campos e corpo foram preservados literalmente.'
 new=head+b'\nobservacao_edicao: '+json.dumps(note,ensure_ascii=False).encode()+b'\n---\n'+body
 out=base/'candidatos'/r['path'];out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(new)
 assert new.split(b'\n---\n',1)[1]==body and new.replace(b'\nobservacao_edicao: '+json.dumps(note,ensure_ascii=False).encode(),b'',1)==old
 rows.append(dict(**r,privado=str(out),sha256_candidato=SHA(new),sha256_corpo=SHA(body),alteracao_unica='Acréscimo do campo observacao_edicao; todos os campos anteriores e corpo byte a byte preservados.'))
manifest=Path('scripts/estados/manifestos/se8782-8783-observacao-privada-20261027-002.json')
manifest.write_text(json.dumps(dict(preparado_em=datetime.datetime.now().astimezone().isoformat(),total=2,normas_novas=0,sem_promocao=True,sem_mascara=True,documentos=rows,base='scripts/estados/manifestos/se8782-8783-duvida-cronologica-20261027-001.json'),ensure_ascii=False,indent=2)+'\n')
paths={str(manifest),str(Path(__file__)),'scripts/estados/manifestos/se8782-8783-duvida-cronologica-20261027-001.json'}
paths.update(json.load(open('estaduais/SE/_fonte/auditorias/duvida-rodape-8782-8783-20261027-001/hashes.json')))
paths.update(r['privado'] for r in rows)
(base/'paths.txt').write_text(''.join(p+'\n' for p in sorted(paths)));(base/'hashes.json').write_text(json.dumps({p:SHA(Path(p).read_bytes()) for p in sorted(paths)},ensure_ascii=False,indent=2)+'\n')
print(str(manifest),SHA(manifest.read_bytes()),len(paths))
