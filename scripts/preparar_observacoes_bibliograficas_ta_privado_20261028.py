"""Propõe metadados bibliográficos literais, sem alterar canônicos ou V7 congelado."""
from pathlib import Path
import argparse,json,subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
import perfil_observacao_bibliografica_ta_privado_20261028 as p
from fechar_lotes_municipais_v7_20261028 import baseline_futuro

def save(path,value):
 with path.open('x') as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--saida',type=Path,required=True);ap.add_argument('--lote',type=int,action='append',required=True);a=ap.parse_args();out=a.saida.resolve()
 if not out.is_relative_to(p.q.BASE):raise ValueError('Saída fora do controle privado')
 out.mkdir(exist_ok=False);files={};candidates=[];retained=[];replays=[];seen=set()
 def add(path):r=p.q.info(Path(path).resolve());files[r['arquivo']]=r
 for batch in a.lote:
  material=p.q.BASE/f'lotes/ta-materializados-{batch:04d}-v7/resultados.jsonl'
  if batch==19:material=p.q.BASE/'lotes/ta-materializados-0019-v7b/resultados.jsonl'
  context=p.q.BASE/f'lotes/ta-contexto-{batch:04d}-v7/controle.json';add(material);add(context);materials={r['path']:r for r in map(json.loads,material.read_text().splitlines()) if r['aprovado']}
  for cr in json.loads(context.read_text())['resultados']:
   if not cr['observacao_api']:continue
   path=cr['path']
   if path in seen:raise ValueError('Candidato repetido')
   seen.add(path);r=materials[path];raw_api,meta_api=p.q.prova_arquivo(r['prova_norma']);norm=json.loads(raw_api);add(p.q.safe(r['prova_norma']['arquivo']));add(p.q.safe(r['prova_norma']['arquivo']).with_suffix('.meta.json'))
   reason=dict(path=path,observacao_literal=norm['observacao'],prova_norma=r['prova_norma'],controle_contexto=p.q.info(context))
   try:
    if cr['texto_fora_dos_dispositivos'] or cr['midia_fora_dos_dispositivos'] or cr['areas_normativas']!=1 or cr['dispositivos_fora_da_area'] or cr['ativos_em_ancestral_historico']:raise ValueError('Contexto extradispositivos continua retido')
    classification=p.classificar(norm['observacao'],norm['data'],meta_api['capturado_em']);old=p.q.safe(path).read_bytes()
    if p.q.sha(old)!=r['sha256'] or cr['sha256']!=r['sha256'] or norm['observacao']!=cr['observacao_api']:raise ValueError('Preimagem/contexto/API divergentes')
    new,addition=p.representar(old,norm['observacao'],r['prova_norma']);folder=out/('candidato-'+str(len(candidates)+1));folder.mkdir();(folder/'preimagem.txt').write_bytes(old);(folder/'candidato.txt').write_bytes(new)
    row=dict(path=path,preimagem=str((folder/'preimagem.txt').relative_to(ROOT)),candidato=str((folder/'candidato.txt').relative_to(ROOT)),sha256_preimagem=p.q.sha(old),sha256_candidato=p.q.sha(new),materializacao=str(material.relative_to(ROOT)),sha256_materializacao=p.q.sha(material.read_bytes()),controle_contexto=str(context.relative_to(ROOT)),sha256_controle_contexto=p.q.sha(context.read_bytes()),classificacao=classification,campos_acrescentados=list(p.FIELDS),prova_norma=r['prova_norma'],fonte=r['prova_frontend'])
    proof=p.validar_candidato(row);candidates.append(row);replays.append(dict(path=path,**proof));save(folder/'controle.json',dict(candidato=row,replay=proof));export=out/'exportados'/path;export.parent.mkdir(parents=True,exist_ok=True);export.write_bytes(new)
    for key in ['prova_frontend','prova_norma','prova_ta','prova_casa']:
     hp=r[key];p.q.prova_arquivo(hp);add(p.q.safe(hp['arquivo']));add(p.q.safe(hp.get('metadata')) if hp.get('metadata') else p.q.safe(hp['arquivo']).with_suffix('.meta.json'))
   except Exception as error:retained.append(dict(**reason,motivo=type(error).__name__+': '+str(error)))
 if not candidates:raise ValueError('Nenhum candidato bibliográfico passou todos os gates')
 if subprocess.check_output(['git','ls-files','-z','--',*[r['path'] for r in candidates]],cwd=ROOT):raise ValueError('Candidato já no índice; não propor sobre publicação')
 command=[sys.executable,'-I',str(ROOT/'scripts/congelar_baseline_municipal_head_20261027.py'),'--saida',str(out/'baseline-head')]
 for path,digest in p.q.RESERVAS:command+=['--reserva',str(p.q.BASE/path),digest]
 subprocess.run(command,cwd=ROOT,check=True,capture_output=True);baseline=baseline_futuro(out/'baseline-head/manifesto.json',out/'baseline-com-reservas47');dedup=p.q.dedup(candidates,baseline);save(out/'dedup.json',dedup)
 # A auditoria municipal é executada sobre a exportação isolada com as rotas
 # originais, sem substituir os MDs retidos do working tree.
 listing=out/'normas-futuras.paths.txt';listing.write_text(''.join(r['path']+'\n' for r in candidates));audit=out/'auditoria-exportada.json';proc=subprocess.run([sys.executable,'-I',str(ROOT/'scripts/auditar_municipal.py'),'--raiz',str(out/'exportados'),'--lista',str(listing),'--saida',str(audit)],cwd=ROOT,capture_output=True,text=True)
 if proc.returncode:raise RuntimeError(proc.stdout+proc.stderr)
 aj=json.loads(audit.read_text())
 if aj['problemas'] or aj['avisos']:raise ValueError('Exportação municipal tem pendências')
 save(out/'mapa-candidatos.json',dict(candidatos=candidates,promovidos=0,limite='Propostas privadas: apenas três campos bibliográficos da fonte; corpo/H1/identidade/captura/SHA do corpo intactos.'))
 save(out/'replay.json',dict(candidatos=len(candidates),aprovados=len(candidates),promovidos=0,problemas=0,resultados=replays));save(out/'retidos.json',dict(retidos=len(retained),resultados=retained,limite='Inclui bibliografias não modeladas e toda observação substantiva/ambígua. Nenhum campo foi descartado ou convertido em corpo.'))
 (out/'ESQUEMA.txt').write_text('Campos já existentes no acervo: observacao_fonte (baixar_planalto.py/baixar_rsf_coletaneas.py), fonte_metadados e sha256_metadados_fonte (baixar_federal.py). Aqui observacao_fonte é exatamente a string observacao da API municipal, sem prefixo ou reescrita. URL e SHA vinculam o mesmo JSON HTTP 200. Não se confirma o diário por rede nem se infere vigência.\n')
 (out/'TESTAR.txt').write_text('Python bundled -I scripts/test_observacoes_bibliograficas_ta_privado_20261028.py\nPython bundled -I scripts/revalidar_observacoes_bibliograficas_ta_privado_20261028.py --manifesto ESTE_DIRETORIO/manifesto.json --sha256 SHA_EXTERNO --saida NOVO_REPLAY.json\nSem aplicar: canônicos retidos preservados. As exportações estão em exportados/municipais/... e não contam como outras normas.\n')
 codepaths=set((p.q.BASE/'lotes/ta-final274-0018/codigo.paths.txt').read_text().splitlines())|{'scripts/perfil_observacao_bibliografica_ta_privado_20261028.py','scripts/preparar_observacoes_bibliograficas_ta_privado_20261028.py','scripts/revalidar_observacoes_bibliograficas_ta_privado_20261028.py','scripts/test_observacoes_bibliograficas_ta_privado_20261028.py','scripts/fechar_lotes_municipais_v7_20261028.py','scripts/promover_reparos_ta47_20261028.py','scripts/preparar_reparos_escapes_ta_46_20261027.py','scripts/perfil_ta_tachados_preservados_20261027.py','scripts/diagnosticar_css_glifos_ta_20261027.py','scripts/congelar_baseline_municipal_head_20261027.py','scripts/comparar_baseline_municipal_head_20261027.py','federal/_fonte/auditorias/diagnostico_glifos1347_20261027_002/diagnosticar.py','municipais/_indice/ibge-municipios.json'}
 for path in codepaths:add(ROOT/path)
 for path in out.rglob('*'):
  if path.is_file():add(path)
 m=dict(propostas=len(candidates),promovidas=0,mapa_candidatos=str((out/'mapa-candidatos.json').relative_to(ROOT)),lista_normas_futuras=str(listing.relative_to(ROOT)),baseline=str(baseline.relative_to(ROOT)),replay=str((out/'replay.json').relative_to(ROOT)),arquivos=sorted(files.values(),key=lambda r:r['arquivo']),limite='Proposta privada sem alterar canônicos ou perfil V7. Reconhece somente o modelo AEMERJ literal examinado; demais observações seguem retidas. Nenhum texto extradispositivos foi inserido.')
 receipt=out/'manifesto.json';save(receipt,m);print(json.dumps(dict(manifesto=p.q.info(receipt),propostas=len(candidates),retidos=len(retained),artefatos=len(files))))
if __name__=='__main__':main()
