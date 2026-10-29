"""Esquema README para novos PDFs TO; não infere situação jurídica."""
import datetime,json,hashlib
from observacao_catalogo_to import observacao_catalogo
ORDEM=('titulo','uf','tipo','numero','data','ano','ementa','situacao','revogada','versao_texto','publicacao','data_publicacao','urn','fonte','arquivo','baixado_em')
VERSAO='PDF digital ALETO, camada textual capturada; edição não certificada'
VERSAO_ANOTADA='PDF digital ALETO, edição histórica com anotações textuais preservadas; vigência não certificada'
VERSAO_REFERENCIAS='PDF digital ALETO, transcrição histórica com ocorrências textuais de alterações; vigência não certificada'
MODO='camada-textual-preformatada-pdf-aleto-v1'
SHA=lambda b:hashlib.sha256(b).hexdigest()
def data_captura(row):
 stamp=row.get('capturado_em')
 if not isinstance(stamp,str):raise ValueError('captura real ausente')
 t=datetime.datetime.fromisoformat(stamp.replace('Z','+00:00'))
 if t.tzinfo is None or t.utcoffset() is None:raise ValueError('captura sem fuso')
 return t.astimezone(datetime.timezone(datetime.timedelta(hours=-3))).date().isoformat()
def verificar(meta,row):
 if any(k not in meta for k in ['titulo','tipo','numero','data','versao_texto','fonte','baixado_em']):raise ValueError('campo obrigatório README ausente')
 if meta.get('uf')!='TO' or meta['versao_texto'] not in (VERSAO,VERSAO_ANOTADA,VERSAO_REFERENCIAS) or meta['baixado_em']!=data_captura(row) or meta.get('representacao_corpo')!=MODO:raise ValueError('esquema/edição/captura divergente')
 if (meta['versao_texto']==VERSAO_ANOTADA)!=(bool(meta.get('anotacoes_editoriais')) and not meta.get('referencias_alteracao_textuais')):raise ValueError('rótulo histórico/anotações não correspondem')
 if (meta['versao_texto']==VERSAO_REFERENCIAS)!=bool(meta.get('referencias_alteracao_textuais')):raise ValueError('rótulo histórico/ocorrências não correspondem')
 if (meta.get('anotacoes_editoriais') or meta.get('referencias_alteracao_textuais')) and ('histórica' not in str(meta.get('edicao')) or meta.get('revogada') is not None or meta.get('situacao') is not None):raise ValueError('edição anotada não autoriza inferir situação jurídica')
 note=observacao_catalogo(row)
 if meta.get('observacao_edicao')!=note:raise ValueError('observação do catálogo diverge da fonte literal')
 expected=[k for k in ORDEM if k in meta]
 if list(meta)[:len(expected)]!=expected:raise ValueError('ordem canônica README divergente')
 return True

def criar(row,q,body):
 if SHA(body.encode())!=q['sha256_corpo']:raise ValueError('corpo não auditado')
 meta=dict(titulo=q['epigrafe'],uf='TO',tipo=q['tipo'],numero=q['numero'],data=q['data'],situacao=None,revogada=None,versao_texto=VERSAO_REFERENCIAS if q.get('referencias_alteracao_textuais') else VERSAO_ANOTADA if q.get('anotacoes_editoriais') else VERSAO,fonte=row['url'],arquivo=row['url_final'],baixado_em=data_captura(row))
 if q.get('ementa_PDF'):meta['ementa']=q['ementa_PDF']
 if q.get('publicacao_literal'):meta['publicacao']=q['publicacao_literal']
 meta={k:meta[k] for k in ORDEM if k in meta};meta.update(id_fonte='ALETO:'+row['item']['id_ALETO'],representacao_corpo=MODO,sha256_texto=q['sha256_corpo'],sha256_fonte=row['sha256_fonte'],edicao='PDF distribuído pelo portal oficial da Assembleia Legislativa do Tocantins, na edição capturada. Camada textual inteira preservada com linhas, números e paginação; nenhum OCR aplicado nesta coleta. Edição de publicação no DOE e vigência global não certificadas.')
 if q.get('anotacoes_editoriais'):
  meta['anotacoes_editoriais']=q['anotacoes_editoriais'];meta['edicao']='Edição histórica anotada do PDF distribuído pelo portal oficial ALETO, na captura preservada. Notas textuais de redação posterior, revogação ou decisão judicial e todo o articulado foram transcritos literalmente; nenhuma redação foi eliminada ou apresentada como texto vigente. Nenhum OCR aplicado nesta coleta. Edição de publicação no DOE e situação jurídica global não certificadas.'
 if q.get('referencias_alteracao_textuais'):
  meta['referencias_alteracao_textuais']=q['referencias_alteracao_textuais'];meta['edicao']='Transcrição histórica integral do PDF ALETO capturado, com ocorrências literais de redação/alteração/revogação/decisão judicial identificadas no texto. Ocorrências internas não são classificadas automaticamente como anotações editoriais nem interpretadas quanto a seus efeitos jurídicos. Nenhuma redação foi eliminada ou apresentada como texto vigente. Notas editoriais delimitadas, quando existentes, são identificadas separadamente e preservadas. Nenhum OCR aplicado nesta coleta; edição DOE e situação jurídica global não certificadas.'
 note=observacao_catalogo(row)
 if note:meta['observacao_edicao']=note
 verificar(meta,row);return ('---\n'+''.join(k+': '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in meta.items())+'---\n# '+meta['titulo']+'\n\n'+body).encode()
