"""Reparo privado do fecho de Buritis; nenhuma promoção ou inferência jurídica."""
from pathlib import Path
import argparse,hashlib,json,re,sys
R=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(R/'scripts'))
from perfil_ta_tachados_preservados_20261027 import converter,comparar
from auditar_municipal import metadados
from auditar import validar
import datetime
TARGET='municipais/MG/buritis/leis-ordinarias/1971/leis-ordinarias-8-1971-sapl-787.md'
OLD='407f89d8c476b79487840a744769d63589d08d3968039c8ae8b9756446f470ba'
SOURCE='municipais/_fonte/texto-articulado-sapl/sapl.buritis.mg.leg.br/bac04d6234b8f858cd9e93be4c9d99385d1bc2fe94e6a3b33eb28f44d19e188c.html'
SOURCE_SHA='e23eecbbc9dff449c9206caadfee308aafec70b8504c08b31304fbbd3d71b78d'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--saida',type=Path,required=True);a=ap.parse_args()
 old=(R/TARGET).read_bytes();source=(R/SOURCE).read_bytes();assert sha(old)==OLD and sha(source)==SOURCE_SHA
 body,parsed=converter(source.decode());assert '~~Sebastião Alves~~\n\n~~Secretário~~\n\nSecretário Substituto' in body and 'Nota editorial' not in body
 proof=parsed.prova_tachados_preservados;assert proof['aprovado'] and [r['texto'] for r in proof['markup_tachado_renderizado']]==['Sebastião Alves','Secretário']
 oldbody=old.decode().split('\n---\n',1)[1].lstrip('\n').split('\n\n',1)[1];prefix=old.decode()[:-len(oldbody)];newprefix,count=re.subn(r'(?m)^sha256_texto: .*$', 'sha256_texto: '+json.dumps(sha(body.encode())),prefix);assert count==1
 new=(newprefix+body+'\n').encode();om=metadados(old.decode());nm=metadados(new.decode());assert {k:v for k,v in om.items() if k!='sha256_texto'}=={k:v for k,v in nm.items() if k!='sha256_texto'}
 errors,warnings=validar(new.decode(),TARGET,datetime.date(2026,10,27));assert not errors and not warnings
 material=[]
 for p in (R/'municipais/_indice/_recuperacao_20261027/lotes').glob('*materializados*/resultados.jsonl'):
  for r in map(json.loads,p.read_text().splitlines()):
   if r.get('aprovado') and r.get('path')==TARGET:material.append(dict(registro=r,path=str(p.relative_to(R)),sha256=sha(p.read_bytes())))
 assert len(material)==1 and material[0]['registro']['sha256']==OLD
 a.saida.mkdir(exist_ok=False,parents=True);(a.saida/'preimagem.txt').write_bytes(old);(a.saida/'candidato.txt').write_bytes(new)
 result=dict(path=TARGET,sha256_preimagem=OLD,sha256_candidato=sha(new),preimagem=str(a.saida/'preimagem.txt'),candidato=str(a.saida/'candidato.txt'),fonte=dict(arquivo=SOURCE,sha256=SOURCE_SHA),replay_preservando_tachados=proof,materializacao_original=material[0],metadados_exceto_sha256_texto_iguais=True,alteracao='Restaura os dois trechos com ~~ explícito e retira a nota que os qualificava como históricos. Secretário Substituto permanece sem tachado. Não atribui efeito jurídico.',promovido=False,codigo_sha256=sha(Path(__file__).read_bytes()))
 (a.saida/'mapa-candidato.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(candidatos=1,promovidos=0,sha256_candidato=sha(new),replay=proof['aprovado'])))
if __name__=='__main__':main()
