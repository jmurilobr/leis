"""Retenções individuais privadas e controles documentados, sem guard vivo."""
from pathlib import Path
import json,gzip,hashlib,re,sys,base64
B=Path(__file__).resolve().parent;R=B.parents[3];sys.path.insert(0,str(R/'scripts'))
import baixar_federal as f
from identidade_decreto_revisao import normal
sha=lambda b:hashlib.sha256(b).hexdigest()
prep=json.loads((B/'qa_final_v4/preparo.json').read_bytes());rows={r['path']:r for r in prep['registros']}
contexts=json.loads((B/'contextos1230.json').read_bytes());links=json.loads((B/'vinculos_tecnicos.json').read_bytes())
control='federal/decretos/1933/dec-23254-1933-10-19.md'
holds={r['path']:('objeto_tecnico_proprio_a_conferir','Projeto, planta, estudo, orçamento ou tabela própria expressamente baixada com o ato; conteúdo resumido ou retificação não basta para provar representação integral.') for r in links if r['path']!=control}
holds['federal/decretos/1933/dec-22610-1933-04-04.md']=('desenhos_proprios_nao_representados','Artigo 2º descreve insígnia e remete a desenhos anexos; descrição textual não substitui os desenhos na transcrição atual.')
holds['federal/decretos/1933/dec-22310-1933-01-04.md']=('duvida_reforma_estatutaria_integral','Aprova alterações deliberadas em assembleia com modificações pontuais dos artigos 16 e 52; a reprodução destas condições não prova por si só a representação de todas as alterações aprovadas. Retido para confronto documental, sem concluir ausência definitiva.')
assert len(links)==36 and len(holds)==37
D=B/'retencoes_contextuais001';D.mkdir(exist_ok=False);out=[];proof=[]
for path,(state,reason) in holds.items():
 r=rows[path];h=gzip.decompress((R/r['coleta']['texto']['arquivo_raw']).read_bytes());a=gzip.decompress((R/r['coleta']['metadados']['arquivo_raw']).read_bytes());m=(R/r['candidato']).read_bytes();assert sha(h)==r['sha256_html'] and sha(a)==r['sha256_metadados'] and sha(m)==r['sha256_candidato'];blocks=f.convert(h.decode()).split('\n\n');closing=next((i for i,b in enumerate(blocks) if re.match(r'^RIO DE JANEIRO[,.;\s]+(?:EM\s*)?\d',normal(b))),None);link=next((x for x in links if x['path']==path),None)
 row={'path':path,'urn':r['urn'],'estado':state,'motivo':reason,'sha256_MD_preliminar':sha(m),'sha256_HTML':sha(h),'sha256_API':sha(a),'fontes':r['coleta'],'vinculos_literais':link['blocos'] if link else [],'fecho_literal':blocks[closing] if closing is not None else None,'conteudo_integral_apos_fecho':'\n\n'.join(blocks[closing+1:]) if closing is not None else None,'contexto_prefixo':next(x for x in contexts['registros'] if x['path']==path),'limites':'Retenção privada por este SHA, sem máscara ou alteração de qualquer candidato/canônico.'};out.append(row);proof.append({'registro':row,'HTML_primario_base64':base64.b64encode(h).decode(),'metadados_raw':a.decode(),'MD_preliminar_utf8':m.decode()})
gp=D/'fontes_provas37.jsonl.gz';gp.write_bytes(gzip.compress(('\n'.join(json.dumps(x,ensure_ascii=False) for x in proof)+'\n').encode(),mtime=0))
(D/'retencoes37.json').write_text(json.dumps({'resumo':{'retidos':37,'vinculos_tecnicos_proprios':35,'desenhos_proprios':1,'duvida_estatutaria':1},'registros':out,'fontes_provas':{'path':str(gp.relative_to(R)),'sha256':sha(gp.read_bytes())}},ensure_ascii=False,indent=2)+'\n')
review=[]
for r in contexts['alertas']:
 path=r['path'];reason='Variante literal da fórmula de autoridade (Govêno, Privisorio, Gov~erno, pontuação ou erro tipográfico), preservada sem emenda. Epígrafe, índice, API e fecho próprios concordam.'
 if r['comando_RESOLVE_com_operando_antes_primeiro_artigo']:reason='Comando próprio de alteração pontual, com dispositivo alterado reproduzido antes do fecho do ato; não exige reprodução integral da norma anterior.'
 if path in holds:reason=holds[path][1]
 elif not r['autoridade_literal'] and not r['comando_RESOLVE_com_operando_antes_primeiro_artigo']:reason='Fonte inicia a fundamentação por considerandos ou Usando das atribuições e contém comando Decreta/Resolve, artigos e fecho próprios. A fórmula sem sujeito nominal foi preservada literalmente; identidade não depende só da presença da palavra Presidente.'
 review.append({'path':path,'sha256_HTML':r['sha256_HTML'],'sha256_MD_preliminar':r['sha256_MD_preliminar'],'decisao':'retido' if path in holds else 'controle_contextual_liberado_para_dedup_final','fundamento':reason,'contexto':r})
controls=[{'path':control,'sha256_MD_preliminar':rows[control]['sha256_candidato'],'fundamento':'Plano de uniformes efetivamente reproduzido após o fecho: boné, túnica, charlateiras, cinto, calça, distintivos e uniformes branco/interno; não há comando de anexar desenho próprio. Referências a modelos de oficiais são comparativas.'},{'path':'federal/decretos/1932/dec-22165-1932-12-05.md','fundamento':'Desenhos vinculados expressamente ao regulamento a ser baixado, objeto futuro; não exige que este decreto contenha o futuro regulamento.'},{'path':'federal/decretos/1933/dec-23201-1933-10-12.md','fundamento':'Ilegível é comando legítimo sobre cancelamento de nota em documento militar, não lacuna editorial.'}]
(B/'revisao_contextual1230.json').write_text(json.dumps({'alertas20_revisados':review,'controles':controls,'limites':'Leitura dirigida dos alertas e vínculos, não revisão humana universal de 1.230 atos. Todo corpo e fontes preservados; sem exclusão de trechos incorporados.'},ensure_ascii=False,indent=2)+'\n')
print('37 retenções privadas, 20 alertas documentados e três controles; nenhum canônico alterado.')
