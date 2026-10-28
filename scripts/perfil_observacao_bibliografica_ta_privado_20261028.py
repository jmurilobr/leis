"""Perfil privado estrito: observação bibliográfica da API em metadados da fonte.

Somente o modelo literal AEMERJ examinado é reconhecido nesta versão. Outras
observações, inclusive outras bibliografias ainda não modeladas, ficam retidas.
Não altera corpo, H1, identidade, datas, vigência ou o perfil V7 congelado.
"""
from pathlib import Path
import datetime as dt,hashlib,json,re,sys
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(ROOT/'scripts/bin/qa-20261027/python'),str(ROOT/'scripts')]
from auditar_municipal import metadados
from auditar_contexto_completo_ta import ContextoCompleto
from auditar_colisoes_lote_municipal import keys
from perfil_ta_tachados_preservados_20261027 import converter,comparar,css_analisar
from auditar import validar
from auditar_emissores_sapl import analisar
from comum import normalizar_chave,decodificar
import promover_reparos_ta47_20261028 as q
PATTERN=re.compile(r'Matéria publicada no Diário Oficial dos Municípios do Estado do Rio de Janeiro no dia (?P<data>\d{2}/\d{2}/\d{4})\. Edição (?P<edicao>[1-9]\d*[A-Za-z]?) A verificação de autenticidade da matéria pode ser feita informando o código identificador no site: (?P<url>https://www\.diariomunicipal\.com\.br/aemerj/?)\Z')
FIELDS=('observacao_fonte','fonte_metadados','sha256_metadados_fonte')

def classificar(note,norma_data,capturado_em):
 if not isinstance(note,str) or not note:raise ValueError('Observação vazia ou não textual')
 match=PATTERN.fullmatch(note)
 if not match:raise ValueError('Observação não é o modelo bibliográfico literal examinado; revisão individual')
 try:published=dt.datetime.strptime(match['data'],'%d/%m/%Y').date();norm=dt.date.fromisoformat(norma_data);capt=dt.datetime.fromisoformat(capturado_em.replace('Z','+00:00'))
 except ValueError:raise ValueError('Data bibliográfica inválida')
 if capt.tzinfo is None:raise ValueError('Captura bibliográfica sem fuso explícito requer revisão')
 if not norm<=published<=capt.astimezone(ZoneInfo('America/Recife')).date():raise ValueError('Data de publicação conflita com norma/captura')
 return dict(modelo='AEMERJ-publicacao-data-edicao-autenticidade-v1',data_publicacao_atribuida_API=published.isoformat(),edicao_atribuida_API=match['edicao'],URL_literal=match['url'],observacao_literal=note,limite='Descrição bibliográfica atribuída à API; não confirma acesso ao diário, autenticidade externa, vigência ou equivalência entre edições.')

def representar(old,note,proof):
 meta=metadados(old.decode())
 if any(k in meta for k in FIELDS):raise ValueError('Campo de fonte já existente; não sobrescrever')
 fields=dict(observacao_fonte=note,fonte_metadados=proof['url'],sha256_metadados_fonte=proof['sha256'])
 if b'\n---\n' not in old:raise ValueError('Cabeçalho inválido')
 addition=('\n'+'\n'.join(k+': '+json.dumps(v,ensure_ascii=False) for k,v in fields.items())).encode()
 new=old.replace(b'\n---\n',addition+b'\n---\n',1)
 if new.split(b'\n---\n',1)[1]!=old.split(b'\n---\n',1)[1]:raise ValueError('Corpo/H1 mudaram')
 after=metadados(new.decode())
 if {k:v for k,v in after.items() if k not in FIELDS}!=meta or after['observacao_fonte']!=note:raise ValueError('Metadados originais/literalidade divergem')
 return new,addition

def validar_candidato(row,require_current=True):
 old=q.safe(row['preimagem']).read_bytes();new=q.safe(row['candidato']).read_bytes();target=q.safe(row['path'])
 if q.sha(old)!=row['sha256_preimagem'] or q.sha(new)!=row['sha256_candidato']:raise ValueError('Preimagem/candidato mudaram')
 if require_current and target.read_bytes()!=old:raise ValueError('Canônico privado diverge da preimagem')
 raw_material=q.safe(row['materializacao']).read_bytes()
 if q.sha(raw_material)!=row['sha256_materializacao']:raise ValueError('Materialização original mudou')
 originals=[r for r in map(json.loads,raw_material.decode().splitlines()) if r.get('path')==row['path']]
 if len(originals)!=1:raise ValueError('Materialização ambígua')
 r=originals[0]
 if not r['aprovado'] or r['sha256']!=q.sha(old) or r['gates']['anexos_proprios']!=0:raise ValueError('Gates de materialização original divergem')
 proofs={k:q.prova_arquivo(r[k]) for k in ['prova_frontend','prova_norma','prova_ta','prova_casa']};api,api_info=proofs['prova_norma'];norm=json.loads(api);front,front_info=proofs['prova_frontend'];meta=metadados(old.decode());after=metadados(new.decode());classification=classificar(norm.get('observacao'),norm['data'],api_info['capturado_em']);expected,added=representar(old,norm['observacao'],r['prova_norma'])
 if new!=expected:raise ValueError('Candidato muda bytes além dos três campos bibliográficos')
 if keys(old.decode(),row['path'])!=keys(new.decode(),row['path']):raise ValueError('Identidade alterada')
 if norm.get('esfera_federacao')!='M' or str(norm['id'])!=str(r['norma_id']) or str(norm['numero'])!=meta['numero'] or norm['data']!=meta['data'] or str(norm['ano'])!=meta['data'][:4]:raise ValueError('API municipal/identidade divergem')
 ta_json=json.loads(proofs['prova_ta'][0]);tas=ta_json.get('results',[]) if isinstance(ta_json,dict) else ta_json;ta=next((t for t in tas if t['id']==r['ta_id']),None)
 if ta is None or ta.get('privacidade') not in {0,69} or str(ta.get('object_id'))!=str(norm['id']) or ta.get('data')!=norm['data'] or str(ta.get('numero'))!=str(norm['numero']):raise ValueError('TA não é público/concordante')
 houses=json.loads(proofs['prova_casa'][0]);houses=houses.get('results',[]) if isinstance(houses,dict) else houses;cities=[c for c in json.loads((ROOT/'municipais/_indice/ibge-municipios.json').read_text()) if str(c['id'])==str(meta['codigo_ibge'])]
 if len(houses)!=1 or len(cities)!=1 or normalizar_chave(houses[0]['municipio'])!=normalizar_chave(meta['municipio']) or normalizar_chave(cities[0]['nome'])!=normalizar_chave(meta['municipio']) or houses[0]['uf']!=meta['uf'] or cities[0]['regiao-imediata']['regiao-intermediaria']['UF']['sigla']!=meta['uf']:raise ValueError('Casa/IBGE divergem')
 literal=r['gates']['identidade_literal']
 if literal.get('divergencias') or not literal.get('numero_literal_confirmado') or not literal.get('data_literal_confirmada'):raise ValueError('Epígrafe original pendente')
 if meta['capturado_em_fonte']!=front_info['capturado_em'] or meta['sha256_fonte']!=q.sha(front):raise ValueError('Captura original diverge')
 source=decodificar(front,r['prova_frontend']['content_type']);context=ContextoCompleto();context.feed(source);context.close()
 if context.fora or context.media or context.cp_encontrados!=1 or context.dispositivos_fora_da_area or context.ativos_em_ancestral_historico:raise ValueError('Conteúdo extradispositivos permanece retido')
 body=q.corpo(new.decode())
 if not body.endswith('\n') or q.sha(body[:-1].encode())!=after['sha256_texto']:raise ValueError('sha256_texto diverge')
 extracted,_=converter(source)
 if body[:-1]!=extracted:raise ValueError('Corpo diverge da reextração integral V7')
 replay=comparar(source,body)
 if not replay['aprovado']:raise ValueError('Replay V3 diverge')
 names=[c['nome'] for c in json.loads((ROOT/'municipais/_indice/ibge-municipios.json').read_text())]
 if analisar(body,meta['municipio'],names):raise ValueError('Jurisdição pendente')
 errors,warnings=validar(new.decode(),row['path'],dt.date.today())
 if errors or warnings:raise ValueError('Formato pendente: '+str((errors,warnings)))
 css=css_analisar(source,front,row['path'],q.sha(new),r['prova_frontend']['url_final'],'observacao_bibliografica_privada')
 if any(not e['rotulo_literal_revogado'] for e in css['dispositivos_ativos_classe_revogado']):raise ValueError('Rótulo de revogação sem contexto')
 return dict(aprovado=True,classificacao=classification,replay=replay,CSS=css,corpo_H1_identidade_datas_captura_iguais=True,campos_acrescentados=list(FIELDS),sha256_metadados_fonte=q.sha(api),API_status=api_info['status'],API_capturado_em_original=api_info['capturado_em'],gates_originais=r['gates'],fonte=r['prova_frontend'],prova_norma=r['prova_norma'],matrizes=replay['prova_tabelas'])
