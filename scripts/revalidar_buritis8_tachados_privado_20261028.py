"""Replay privado a partir dos snapshots; não depende de promover o canônico."""
from pathlib import Path
import argparse,collections,gzip,hashlib,json,re,sys
R=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(R/'scripts/bin/qa-20261027/python'),str(R/'scripts')]
from perfil_ta_tachados_preservados_20261027 import converter,comparar
from auditar_municipal import metadados
from auditar_colisoes_lote_municipal import keys
from auditar_commonmark_ta_v2 import NOTE
from materializar_textos_articulados_sapl_v7_privado_20261027 import dia_captura
B=R/'municipais/_indice/_recuperacao_20261027'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--saida',type=Path,required=True);a=ap.parse_args()
 map_path=B/'buritis8-tachados-reparo-privado-v2-20261027/mapa-candidato.json';m=json.loads(map_path.read_text());old=(R/m['preimagem']).read_bytes();new=(R/m['candidato']).read_bytes();assert sha(old)==m['sha256_preimagem'] and sha(new)==m['sha256_candidato'];source=(R/m['fonte']['arquivo']).read_bytes();assert sha(source)==m['fonte']['sha256']
 source_proof=m['materializacao_original']['registro']['prova_frontend'];info=json.loads((R/source_proof['arquivo']).with_suffix('.meta.json').read_text());assert info['status']==200 and info['sha256']==m['fonte']['sha256'] and all(info[k]==source_proof[k] for k in ['url','url_final','capturado_em'])
 om=metadados(old.decode());nm=metadados(new.decode());assert {k:v for k,v in om.items() if k!='sha256_texto'}=={k:v for k,v in nm.items() if k!='sha256_texto'}
 ob=old.decode().split('\n---\n',1)[1].lstrip('\n').split('\n\n',1)[1];nb=new.decode().split('\n---\n',1)[1].lstrip('\n').split('\n\n',1)[1];assert nb.endswith('\n');body=nb[:-1];expected,parsed=converter(source.decode());assert body==expected and sha(body.encode())==nm['sha256_texto']
 prefix,n=re.subn(r'(?m)^sha256_texto: .*$', 'sha256_texto: '+json.dumps(nm['sha256_texto']),old.decode()[:-len(ob)]);assert n==1 and prefix==new.decode()[:-len(nb)]
 assert ob.count(NOTE)==1 and nb.replace('~~Sebastião Alves~~\n\n~~Secretário~~\n\n','',1).rstrip('\n')==ob.replace('\n\n'+NOTE,'').rstrip('\n')
 proof=comparar(source.decode(),body);assert proof['aprovado'] and [x['texto'] for x in proof['markup_tachado_renderizado']]==['Sebastião Alves','Secretário'];assert 'Secretário Substituto' in body and 'Nota editorial' not in body
 assert nm['capturado_em_fonte']==info['capturado_em'] and nm['baixado_em']==dia_captura(info['capturado_em'])[0]
 baseline_path=B/'baseline-head-buritis-preservado/manifesto.json';base=json.loads(baseline_path.read_text());index=collections.defaultdict(set);paths=set()
 for r in base['arquivos']:
  raw=(R/r['arquivo']).read_bytes();assert sha(raw)==r['sha256'] and len(raw)==r['bytes']
 for r in map(json.loads,gzip.open(R/base['metadados'],'rt')):
  paths.add(r['path'])
  for key in r['chaves']:index[tuple(key)].add(r['path'])
 assert m['path'] not in paths and len(paths)==base['total'];newkeys=keys(new.decode(),m['path']);assert newkeys==keys(old.decode(),m['path']);collisions=[dict(chave=k,existentes=sorted(index[k])) for k in newkeys if index[k]];assert not collisions
 result=dict(candidatos=1,promovidos=0,problemas=0,path=m['path'],sha256_preimagem=sha(old),sha256_candidato=sha(new),fonte_sha256=sha(source),capturado_em_original=info['capturado_em'],baixado_em_preservado=nm['baixado_em'],replay=proof,alteracao_exata_demonstrada=True,metadados_H1_exceto_sha256_texto_iguais=True,baseline_commit=base['commit'],baseline_sha256=sha(baseline_path.read_bytes()),comparados=len(paths),colisoes=collisions,limite='Somente replay dos snapshots privados. ROOT deve revalidar HEAD e preimagem corrente antes de promover; nenhuma alteração de canônico ou índice.')
 with a.saida.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps(dict(candidatos=1,promovidos=0,problemas=0,comparados=len(paths))))
if __name__=='__main__':main()
