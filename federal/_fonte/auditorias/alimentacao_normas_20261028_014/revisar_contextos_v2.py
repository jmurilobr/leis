"""Revisão contextual dirigida, sem promover candidatos ou alterar guard."""
from pathlib import Path
import json,gzip,hashlib,re,sys,base64
B=Path(__file__).resolve().parent;R=B.parents[3];sys.path.insert(0,str(R/'scripts'))
import baixar_federal as f
from identidade_decreto_revisao import normal
sha=lambda b:hashlib.sha256(b).hexdigest()
rows={r['path']:r for r in json.loads((B/'qa_final_v4/preparo.json').read_bytes())['registros']};contexts=json.loads((B/'contextossnapshot.json').read_bytes());links=json.loads((B/'vinculos_tecnicos.json').read_bytes());formulas=json.loads((B/'formulas_legislativas.json').read_bytes())['registros']
holds={r['path']:('objeto_tecnico_proprio_a_conferir','Projeto ou orçamento próprio expressamente acompanhando o ato; valores, descrições ou cláusulas não bastam para representar plantas e projetos documentais. Retenção da transcrição examinada, sem afirmar ausência em todas as fontes.') for r in links}

for path in list(holds):
 if any('-'+n+'-' in path for n in ['16315','16433']):holds.pop(path)
for num in ['16246','17102','17363','17167']:
 path=next(p for p,r in rows.items() if r['epigrafe']['numero']==num);holds[path]=('duvida_estatutos_aprovados','Ato aprova estatutos ou resoluções de assembleia com alterações especificadas, mas reproduz somente modificações selecionadas; conjunto documental aprovado não comprovado na transcrição. Retenção contextual, sem concluir ausência em outras fontes.')
for x in formulas:
 holds[x['path']]=('identidade_tipo_historico_a_conferir','Fórmula de sanção de resolução do Congresso em documento indexado como DEC. Retenção privada até confronto das séries históricas, sem afirmar duplicação ou erro de tipo pela fórmula isolada.')
holds['federal/decretos/1924/dec-16433-1924-03-29.md']=('glifo_fonte_Symbol_a_conferir','Fonte aplica font-family:Symbol a caracteres ½ na relação normativa. Igualdade de Unicode não prova equivalência visual do glifo; retenção até confronto visual ou fonte oficial equivalente. A relação textual está representada, mas isso não resolve fidelidade tipográfica.')
assert len(links)==53 and len(holds)==60,(len(links),len(holds));assert set(holds)<=set(rows)
D=B/'retencoes_contextuais002';D.mkdir(exist_ok=False);out=[];proof=[]
for path,(state,reason) in holds.items():
 r=rows[path];h=gzip.decompress((R/r['coleta']['texto']['arquivo_raw']).read_bytes());a=gzip.decompress((R/r['coleta']['metadados']['arquivo_raw']).read_bytes());m=(R/r['candidato']).read_bytes();assert sha(h)==r['sha256_html'] and sha(a)==r['sha256_metadados'] and sha(m)==r['sha256_candidato'];blocks=f.convert(h.decode()).split('\n\n');closing=next((i for i,b in enumerate(blocks) if re.match(r'^RIO DE JANEIRO[,.;\s]+(?:EM\s*)?\d',normal(b))),None);link=next((x for x in links if x['path']==path),None)
 row={'path':path,'urn':r['urn'],'estado':state,'motivo':reason,'sha256_MD_preliminar':sha(m),'sha256_HTML':sha(h),'sha256_API':sha(a),'fontes':r['coleta'],'vinculos_literais':link['blocos'] if link else [],'fecho_literal':blocks[closing] if closing is not None else None,'conteudo_integral_apos_fecho':'\n\n'.join(blocks[closing+1:]) if closing is not None else None,'contexto_prefixo':next(x for x in contexts['registros'] if x['path']==path),'limites':'Retenção privada individual por SHA; não máscara ou alteração de candidato.'};out.append(row);proof.append({'registro':row,'HTML_primario_base64':base64.b64encode(h).decode(),'metadados_raw':a.decode(),'MD_preliminar_utf8':m.decode()})
gp=D/'fontes_provas60.jsonl.gz';gp.write_bytes(gzip.compress(('\n'.join(json.dumps(x,ensure_ascii=False) for x in proof)+'\n').encode(),mtime=0));(D/'retencoes60.json').write_text(json.dumps({'resumo':{'retidos':60,'glifos_Symbol':1,'objetos_tecnicos_ou_orcamentos':51,'duvida_estatutos':4,'identidade_tipo_historico':4},'registros':out,'fontes_provas':{'path':str(gp.relative_to(R)),'sha256':sha(gp.read_bytes())}},ensure_ascii=False,indent=2)+'\n')
controls={'16315':'Relação própria dos materiais integralmente presente após o fecho; planos aprovados por outro decreto são remissão histórica. Referências internas a especificações comerciais não foram tratadas como comando de novo projeto próprio.','16433':'Relação dos materiais presente, incluindo grupos I a XIII; projetos aprovados pelo decreto 16.405 são objeto de outra norma.','15426':'Novas redações expressamente delimitadas aos artigos 6 e 45, ambos presentes; reforma pontual, não aprovação genérica de estatuto omitido.','16836':'Grafia literal Presidenle preservada; transferência de favores anteriores sem nova aprovação das plantas antigas.','17249':'Grafia literal Presidenta preservada; desapropriação para executar projeto aprovado por ato anterior, sem comando de anexo novo.'}
review=[]
for r in contexts['alertas']:
 num=r['epigrafe']['numero'];reason=holds[r['path']][1] if r['path'] in holds else controls.get(num,'Fórmula literal de autoridade preservada; comando, epígrafe, metadados e fecho próprios concordam.')
 review.append({'path':r['path'],'sha256_HTML':r['sha256_HTML'],'sha256_MD_preliminar':r['sha256_MD_preliminar'],'decisao':'retido' if r['path'] in holds else 'controle_contextual_para_dedup_final','fundamento':reason,'contexto':r})
(B/'revisao_contextual499_v2.json').write_text(json.dumps({'alertas_revisados':review,'controles_explicitos':controls,'limites':'Leitura dirigida dos vínculos e alertas, sem afirmar revisão humana universal de 499 atos. Corpo e documentos incorporados permanecem integrais; limites servem apenas para avaliar o fecho principal.'},ensure_ascii=False,indent=2)+'\n');print('60 retenções individuais privadas; 439 candidatos sujeitos ao congelamento/dedup.')
