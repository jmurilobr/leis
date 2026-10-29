"""Exporta bytes exatos por SHA sem tocar nos módulos compartilhados."""
from pathlib import Path
import json,hashlib,subprocess,ast
E=Path(__file__).resolve().parent;R=E.parents[3];O=R/'federal/_fonte/auditorias/promocao730_20261028_001';A=R/'federal/_fonte/auditorias/alimentacao_normas_20261028_019';sha=lambda b:hashlib.sha256(b).hexdigest();rr=json.loads((O/'recibo730.json').read_bytes());head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();versions={}
for row in rr['codigos']:
 logical=row['path'];expected=row['sha256'];current=(R/logical).read_bytes();raw=current;origin='Artefato antecedente no disco, já confrontado com o SHA original'
 if sha(raw)!=expected:
  raw=subprocess.check_output(['git','show',head+':'+logical],cwd=R);origin='Git HEAD '+head+':'+logical
 assert sha(raw)==expected,(logical,expected,sha(raw));dest=E/'codigo'/logical;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);versions[logical]={'path_exportado':str(dest.relative_to(R)),'sha256_original_esperado':expected,'origem_bytes':origin,'sha256_worktree_observado':sha(current),'divergente_no_worktree':sha(current)!=expected}
# Importações transitivas não declaradas no recibo original são explicitadas separadamente.
aux=[]
for logical in ['scripts/auditar.py','scripts/datas.py']:
 raw=subprocess.check_output(['git','show',head+':'+logical],cwd=R);dest=E/'codigo'/logical;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);aux.append({'path_logico':logical,'path_exportado':str(dest.relative_to(R)),'sha256':sha(raw),'origem_bytes':'Git HEAD '+head+':'+logical,'papel':'Dependência transitiva auxiliar declarada neste complemento; não inventa SHA antecedente'})
marked=R/'reguladores/_fonte/auditorias/orgao_dedup_2017_20261028_002/codigo/marked.esm.mjs';live=Path('/Users/joaodavisn/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/marked/lib/marked.esm.js');assert marked.read_bytes()==live.read_bytes();dest=E/'codigo/vendor/marked.esm.mjs';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(marked.read_bytes());aux.append({'path_logico':'runtime Node marcado no replay original','path_exportado':str(dest.relative_to(R)),'sha256':sha(dest.read_bytes()),'origem_bytes':str(marked.relative_to(R)),'papel':'Mesmos bytes do runtime observado; replay dos candidatos comprova os resultados armazenados'})
for name in ['promover730.py','replay730.py','recibo730.json','recibo_promocao730.json']:
 (E/('original_'+name)).write_bytes((O/name).read_bytes())
manifest={'HEAD_recuperacao':head,'originais':{str((O/name).relative_to(R)):sha((O/name).read_bytes())for name in ['promover730.py','replay730.py','recibo730.json','recibo_promocao730.json']},'versoes_logicas':versions,'auxiliares':aux,'limites':'Não altera recibos antecedentes nem SHA esperado. O caminho lógico usa um arquivo arquivado com exatamente os bytes originalmente exigidos; módulos do worktree divergentes são preservados e excluídos do mapa efetivo. Dados/candidatos continuam nos snapshots imutáveis.'};(E/'mapa_versoes.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print('Exportados',len(versions),'insumos com SHA original; divergentes:',[p for p,r in versions.items()if r['divergente_no_worktree']],flush=True)
