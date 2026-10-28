"""Revalida os 46 candidatos privados contra preimagem e fontes; não promove."""
from pathlib import Path
import argparse, datetime, gzip, hashlib, json, re, sys
R=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(R/'scripts/bin/qa-20261027/python'),str(R/'scripts')]
from preparar_reparos_escapes_ta_46_20261027 import escapar
from auditar_commonmark_ta_v2 import comparar
from auditar_municipal import metadados
from auditar_emissores_sapl import analisar
from auditar import validar

def sha(b): return hashlib.sha256(b).hexdigest()

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--saida',type=Path,required=True);a=ap.parse_args()
 b=R/'municipais/_indice/_recuperacao_20261027';m=json.loads((b/'reparos-escapes-ta-46-privado-20261027/mapa-candidatos.json').read_text())
 baseline=json.loads((b/'baseline-head-reparos46/manifesto.json').read_text())
 existing={r['path'] for r in map(json.loads,gzip.open(R/baseline['metadados'],'rt'))}
 municipalities=[x['nome'] for x in json.loads((R/'municipais/_indice/ibge-municipios.json').read_text())]
 rows=[];seen=set()
 for r in m['candidatos']:
  p=r['path'];assert p not in existing and p not in seen;seen.add(p)
  old=(R/r['preimagem']).read_bytes();new=(R/r['candidato']).read_bytes()
  assert sha(old)==r['sha256_preimagem'] and sha(new)==r['sha256_candidato']
  assert (R/p).read_bytes()==old
  om=metadados(old.decode());nm=metadados(new.decode())
  assert {k:v for k,v in om.items() if k!='sha256_texto'}=={k:v for k,v in nm.items() if k!='sha256_texto'}
  ob=old.decode().split('\n---\n',1)[1].lstrip('\n').split('\n\n',1)[1]
  nb=new.decode().split('\n---\n',1)[1].lstrip('\n').split('\n\n',1)[1]
  op=old.decode()[:-len(ob)];np=new.decode()[:-len(nb)]
  expected,n=re.subn(r'(?m)^sha256_texto: .*$', 'sha256_texto: '+json.dumps(nm['sha256_texto']),op)
  assert n==1 and expected==np
  assert nb==escapar(ob[:-1])+'\n' and nb!=ob and sha(nb[:-1].encode())==nm['sha256_texto']
  assert old.decode().split('\n---\n',1)[1].lstrip('\n').split('\n\n',1)[0]==new.decode().split('\n---\n',1)[1].lstrip('\n').split('\n\n',1)[0]
  assert sha((R/r['materializacao']).read_bytes())==r['sha256_materializacao']
  mr=next(x for x in map(json.loads,(R/r['materializacao']).read_text().splitlines()) if x.get('path')==p)
  assert mr['aprovado'] and mr['sha256']==sha(old) and mr['gates']['anexos_proprios']==0
  for k in ['prova_frontend','prova_norma','prova_ta','prova_casa']:
   pr=mr[k];assert sha((R/pr['arquivo']).read_bytes())==pr['sha256']
  norm=json.loads((R/mr['prova_norma']['arquivo']).read_text());assert norm['esfera_federacao']=='M'
  proof=comparar((R/mr['prova_frontend']['arquivo']).read_text(),nb[:-1]);assert proof['aprovado'] and proof['assinatura_numerica_confere']
  assert not analisar(nb,nm['municipio'],municipalities)
  errors,warnings=validar(new.decode(),p,datetime.date(2026,10,27));assert not errors and not warnings
  context=json.loads((R/r['controle_contexto']).read_text());assert sha((R/r['controle_contexto']).read_bytes())==r['sha256_controle_contexto']
  assert p in (R/r['controle_contexto']).parent.joinpath('aprovados.paths.txt').read_text().splitlines()
  rows.append(dict(path=p,sha256_preimagem=sha(old),sha256_candidato=sha(new),replay=proof,metadados_exceto_sha256_texto_iguais=True,anexos_proprios=0,ausente_HEAD_e_reservas=True))
 assert len(rows)==46
 with a.saida.open('x') as stream:json.dump(dict(propostas=46,promovidas=0,problemas=[],resultados=rows,baseline_commit=baseline['commit'],comparados=baseline['total'],limite='Revalidação privada, sem escrita de canônicos ou índice. Promoção ainda requer decisão ROOT e preimagem atual.'),stream,ensure_ascii=False,indent=2);stream.write('\n')
 print(json.dumps(dict(propostas=46,promovidas=0,problemas=0)))

if __name__=='__main__': main()
