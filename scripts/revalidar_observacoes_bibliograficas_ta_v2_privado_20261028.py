"""Replay bibliográfico por cadeia de manifestos e exports vinculados por SHA.

Não assume exports ao lado do manifesto final. Só segue referências declaradas
com hash no manifesto pai e usa os exports registrados na origem verificada.
Não aplica candidatos, não muda arquivos congelados, canônicos, HEAD ou índice.
"""
from pathlib import Path
import argparse,collections,json,sys
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
import perfil_observacao_bibliografica_ta_privado_20261028 as p
REFS=('manifesto_origem','pacote_anterior','pacote_anterior_overlay')

def carregar_cadeia(path,expected):
 pending=[(path.resolve(),expected)];seen={};nodes=[]
 while pending:
  current,digest=pending.pop(0);relative=str(current.relative_to(ROOT))
  if relative in seen:
   if seen[relative]!=digest:raise ValueError('Mesmo manifesto com hashes conflitantes')
   continue
  manifest=p.q.verificar_manifesto(current,digest);seen[relative]=digest;index={r['arquivo']:r for r in manifest['arquivos']};nodes.append(dict(path=current,sha256=digest,manifesto=manifest,index=index))
  for key in REFS:
   ref=manifest.get(key)
   if not ref:continue
   if not isinstance(ref,dict) or not {'arquivo','sha256','bytes'}<=ref.keys():raise ValueError('Referência de pacote sem hash completo')
   record=index.get(ref['arquivo'])
   if record!=ref:raise ValueError('Referência não vinculada pelos arquivos do manifesto pai')
   pending.append((p.q.safe(ref['arquivo']),ref['sha256']))
 return nodes

def resolver_export(row,nodes):
 matches={}
 for node in nodes:
  candidate=node['path'].parent/'exportados'/row['path'];relative=str(candidate.relative_to(ROOT));record=node['index'].get(relative)
  if record and record['sha256']==row['sha256_candidato']:
   data=p.q.safe(relative).read_bytes()
   if p.q.sha(data)!=row['sha256_candidato'] or len(data)!=record['bytes']:raise ValueError('Exportação declarada mudou')
   matches[relative]=dict(**record,manifesto_origem=str(node['path'].relative_to(ROOT)),sha256_manifesto_origem=node['sha256'])
 if not matches:raise ValueError('Nenhuma exportação do candidato está vinculada por SHA à cadeia verificada')
 # Cópias byte idênticas não são novas versões. A seleção é determinística e
 # todas as origens equivalentes são registradas, sem busca livre no disco.
 return dict(exportacao=matches[sorted(matches)[0]],origens_equivalentes=[matches[k] for k in sorted(matches)])

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--manifesto',type=Path,required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--saida',type=Path,required=True);ap.add_argument('--exigir-promovidos',action='store_true');a=ap.parse_args();nodes=carregar_cadeia(a.manifesto,a.sha256);root=nodes[0];manifest=root['manifesto'];map_path=p.q.safe(manifest['mapa_candidatos'])
 if str(map_path.relative_to(ROOT)) not in root['index']:raise ValueError('Mapa de candidatos sem vínculo no manifesto final')
 rows=json.loads(map_path.read_text())['candidatos'];results=[];states=collections.Counter()
 if len(rows)!=manifest['propostas'] or len({r['path'] for r in rows})!=len(rows):raise ValueError('Seleção ambígua')
 for row in rows:
  for key,digest in [('preimagem','sha256_preimagem'),('candidato','sha256_candidato'),('materializacao','sha256_materializacao')]:
   binding=root['index'].get(row[key])
   if not binding or binding['sha256']!=row[digest]:raise ValueError('Candidato/preimagem/materialização sem vínculo explícito')
  proof=p.validar_candidato(row,require_current=False);export=resolver_export(row,nodes);current=p.q.sha(p.q.safe(row['path']).read_bytes())
  state='candidato já promovido' if current==row['sha256_candidato'] else 'preimagem intacta' if current==row['sha256_preimagem'] else 'destino diverge de ambos os snapshots'
  if state=='destino diverge de ambos os snapshots' or a.exigir_promovidos and state!='candidato já promovido':raise ValueError('Estado do destino incompatível: '+row['path'])
  states[state]+=1;results.append(dict(path=row['path'],sha256_candidato=row['sha256_candidato'],sha256_canonico_observado=current,estado_canonico_observado=state,resolucao_exportacao=export,**proof))
 result=dict(candidatos=len(rows),aprovados=len(results),problemas=0,aplicacoes_executadas=0,escritas_canonicas=0,promovidos_observados=states['candidato já promovido'],estados_observados=dict(states),cadeia_manifestos=[dict(arquivo=str(n['path'].relative_to(ROOT)),sha256=n['sha256']) for n in nodes],resultados=results,codigo=p.q.info(Path(__file__).resolve()),limite='Replay de arquivos e exports vinculados por SHA. Sem aplicação ou escrita Git; API atribuída literalmente, sem certificar AEMERJ ou vigência.')
 with a.saida.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({k:result[k] for k in ['candidatos','aprovados','problemas','aplicacoes_executadas','promovidos_observados']}))
if __name__=='__main__':main()
