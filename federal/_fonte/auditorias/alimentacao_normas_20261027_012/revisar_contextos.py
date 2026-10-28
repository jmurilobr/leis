"""Retenções individuais privadas e controles documentados, sem guard vivo."""
from pathlib import Path
import json,gzip,hashlib,re,sys,base64
B=Path(__file__).resolve().parent;R=B.parents[3];sys.path.insert(0,str(R/'scripts'))
import baixar_federal as f
from identidade_decreto_revisao import normal
sha=lambda b:hashlib.sha256(b).hexdigest()
prep=json.loads((B/'qa_final_v4/preparo.json').read_bytes());rows={r['path']:r for r in prep['registros']}
contexts=json.loads((B/'contextos1172.json').read_bytes());links=json.loads((B/'vinculos_tecnicos.json').read_bytes())
holds={r['path']:('objeto_tecnico_proprio_a_conferir','Projeto ou orçamento próprio expressamente acompanhando/baixando com o ato; descrição, total ou tabela resumida não bastam para representar o projeto documental. Retenção contextual privada, sem afirmar inexistência em outra fonte.') for r in links}
holds['federal/decretos/1931/dec-20213-1931-07-16.md']=('desenhos_proprios_nao_representados','Plano de uniformes contém chamadas próprias a desenho anexo/desenho junto para boné, divisas e distintivos. Descrições textuais não substituem desenhos; fonte e MD não contêm representação visual. Corpo integral preservado.')
holds['federal/decretos/1931/dec-20756-1931-12-04.md']=('duvida_orcamentos_proprios','Novos orçamentos expressamente baixados para aparelhos staffs elétricos; descrição/valores resumidos não provam a reprodução dos documentos. Dúvida separada, sem conclusão de ausência em todas as fontes.')
holds['federal/decretos/1931/dec-20581-1931-10-29.md']=('duvida_clausula_aberta_e_pontilhado','Alteração do artigo 7º termina com Serão consideramos de familia: seguida apenas de pontilhado. Pode ser convenção editorial de trecho não alterado ou lacuna; preservar literalmente e reter até confronto, sem inferir ausência só pela numeração ou preencher lista.')
assert len(links)==16 and len(holds)==17
D=B/'retencoes_contextuais001';D.mkdir(exist_ok=False);out=[];proof=[]
for path,(state,reason) in holds.items():
 r=rows[path];h=gzip.decompress((R/r['coleta']['texto']['arquivo_raw']).read_bytes());a=gzip.decompress((R/r['coleta']['metadados']['arquivo_raw']).read_bytes());m=(R/r['candidato']).read_bytes();assert sha(h)==r['sha256_html'] and sha(a)==r['sha256_metadados'] and sha(m)==r['sha256_candidato'];blocks=f.convert(h.decode()).split('\n\n');closing=next((i for i,b in enumerate(blocks) if re.match(r'^RIO DE JANEIRO[,.;\s]+(?:EM\s*)?\d',normal(b))),None);link=next((x for x in links if x['path']==path),None)
 row={'path':path,'urn':r['urn'],'estado':state,'motivo':reason,'sha256_MD_preliminar':sha(m),'sha256_HTML':sha(h),'sha256_API':sha(a),'fontes':r['coleta'],'vinculos_literais':link['blocos'] if link else [],'fecho_literal':blocks[closing] if closing is not None else None,'conteudo_integral_apos_fecho':'\n\n'.join(blocks[closing+1:]) if closing is not None else None,'contexto_prefixo':next(x for x in contexts['registros'] if x['path']==path),'limites':'Retenção privada por este SHA, sem máscara ou alteração de qualquer candidato/canônico.'};out.append(row);proof.append({'registro':row,'HTML_primario_base64':base64.b64encode(h).decode(),'metadados_raw':a.decode(),'MD_preliminar_utf8':m.decode()})
gp=D/'fontes_provas17.jsonl.gz';gp.write_bytes(gzip.compress(('\n'.join(json.dumps(x,ensure_ascii=False) for x in proof)+'\n').encode(),mtime=0))
(D/'retencoes17.json').write_text(json.dumps({'resumo':{'retidos':17,'projetos_proprios':14,'desenhos_proprios':1,'duvida_orcamentos':1,'duvida_clausula_aberta':1},'registros':out,'fontes_provas':{'path':str(gp.relative_to(R)),'sha256':sha(gp.read_bytes())}},ensure_ascii=False,indent=2)+'\n')
review=[]
for r in contexts['alertas']:
 path=r['path'];reason='Variante literal da fórmula de autoridade (Govêno, Privisorio, Gov~erno, pontuação ou erro tipográfico), preservada sem emenda. Epígrafe, índice, API e fecho próprios concordam.'
 if r['comando_RESOLVE_com_operando_antes_primeiro_artigo']:reason='Comando próprio de alteração pontual, com dispositivo alterado reproduzido antes do fecho do ato; não exige reprodução integral da norma anterior.'
 if path in holds:reason=holds[path][1]
 elif not r['autoridade_literal'] and not r['comando_RESOLVE_com_operando_antes_primeiro_artigo']:reason='Fonte inicia a fundamentação por considerandos ou Usando das atribuições e contém comando Decreta/Resolve, artigos e fecho próprios. A fórmula sem sujeito nominal foi preservada literalmente; identidade não depende só da presença da palavra Presidente.'
 if path=='federal/decretos/1931/dec-20373-1931-09-08.md':reason='Fonte inicia diretamente no Artigo único, que contém o comando de supressão do consulado; epígrafe, API, índice, fecho e assinaturas próprios preservados. Não se inventou uma fórmula de autoridade ou preâmbulo ausente.'
 review.append({'path':path,'sha256_HTML':r['sha256_HTML'],'sha256_MD_preliminar':r['sha256_MD_preliminar'],'decisao':'retido' if path in holds else 'controle_contextual_liberado_para_dedup_final','fundamento':reason,'contexto':r})
controls=[{'path':'federal/decretos/1931/dec-20594-1931-11-03.md','fundamento':'Nova redação pontual do artigo 7º reproduzida com enumeração e dois parágrafos; repetição literal do rótulo VIII preservada, sem inferência de perda pela numeração.'}]
(B/'revisao_contextual1172.json').write_text(json.dumps({'alertas8_revisados':review,'controles':controls,'limites':'Leitura dirigida dos alertas e vínculos, não revisão humana universal de 1.172 atos. Todo corpo e fontes preservados; sem exclusão de trechos incorporados.'},ensure_ascii=False,indent=2)+'\n')
print('17 retenções privadas, oito alertas documentados e controle de reforma pontual; nenhum canônico alterado.')
