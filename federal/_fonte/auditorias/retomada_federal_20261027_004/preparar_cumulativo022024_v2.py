from pathlib import Path
import json,gzip,hashlib,sys,re,collections
B=Path(__file__).resolve().parent;ROOT=B.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from preparar_lote_decretos_cache import fields
from identidade_decreto import extrair_epigrafe_decreto,numero_normalizado
from auditar_pontuacao_federal import normalizar_marcador_administrativo
import baixar_federal as f
sha=lambda b:hashlib.sha256(b).hexdigest();D=B/'cumulativo022024_v2';D.mkdir(exist_ok=False);C=D/'candidatos';C.mkdir();overlay=json.loads((ROOT/'federal/_overlay_contexto_integridade_022024_20261027_001.json').read_text());holds={r['path']:r for r in overlay['registros']};index=collections.defaultdict(list)
for d in f.carregar_indice('DEC-n'):
 q=f.montar(d);index[(numero_normalizado(f.numero_oficial(d)),q['data'][:4])].append({'urn':q['urn'],'data':q['data'],'id':d.get('id')})
fixes={'9850':[('\n-\n','\n\\-\n')],'9106':[('a*, da*','a, da')],'8997':[('a*, d*a','a, da')],'8977':[('a*, d*a','a, da')],'8918':[('**Art. 79.**','**Art.79.**')],'8401':[('**Art. 11º**','**Art.11º**')],'8399':[('**Art. 1º**','**Art.1º**')],'8381':[('**Art. 1º**','**Art.1º**')],'7847':[('**Art. 105.**','**Art.105.**')],'7824':[('**Art. 1º**','**Art.1º**')],'7664':[('**Art. 1º**','**Art.1º**')],'7603':[('110*. S*ebastião','110. Sebastião')],'7595':[('**Art. 1º**','**Art.1º**')],'7193':[('Oficial*, s*ob','Oficial, sob')],'7196':[('a*, d*a','a, da')],'6944':[('10*. Seb*astião','10. Sebastião')],'4647':[('**Art. 1º**','**Art.1º**')]}
native={'7603','6944','8886','8263','7839','7809','7614','6823','5364','5313','6406','6050'};allrows=[];ret=[];prom=[];notes=[];errors=[]
for n in [22,23,24]:
 m=json.loads((ROOT/f'federal/_lote_dec_continuacao_20261020_{n:03}.json').read_text());a=json.loads((ROOT/f'federal/_auditoria_pontuacao_federal_20261020_{n:03}_v1.json').read_text());proofs={r['path']:r for r in a['auditados']+a['divergencias_para_revisao']};tb=ROOT/'federal/_fonte/auditorias/retomada_federal_20261027_003' if n==22 else B;suffix='022' if n==22 else str(n);tri=json.loads((tb/f'triagem-fechos{suffix}-v1.json').read_text());u=json.loads((tb/f'contextos-fechos-inconclusivos{suffix}.json').read_text());fechos={r['path']:{'tipo':'fecho_divergente','contexto':r} for r in tri['divergencias']};fechos.update({r['path']:{'tipo':'fecho_nao_reconhecido','contexto':r} for r in u});ret.extend([dict(r,lote=n) for r in m['retidos']])
 for r in m['publicaveis']:
  p=r['path'];num=numero_normalizado(r['epigrafe']['numero']);raw=(ROOT/p).read_bytes();assert sha(raw)==r['sha256'];meta,cab,body=fields(raw.decode());src=gzip.decompress((ROOT/p.replace('federal/decretos/','federal/_fonte/decretos/').replace('.md','.html.gz')).read_bytes());assert sha(src)==r['sha256_fonte_html'];mr=gzip.decompress((ROOT/r['captura_metadados']).read_bytes());assert sha(mr)==r['sha256_metadados'];md=json.loads(mr);assert md['legislationDate']==r['epigrafe']['data'] and md['legislationIdentifier']==r['urn'];ep=extrair_epigrafe_decreto(body);assert ep and ep['data']==r['epigrafe']['data'] and ep['numero']==num;ix=index[(num,ep['data'][:4])];assert any(x['urn']==r['urn'] for x in ix)
  if p in holds:ret.append(dict(holds[p]));continue
  if any(x['urn']!=r['urn'] for x in ix):ret.append(dict(r,lote=n,status='retido_identidade_indice_concorrente',indice_identidades=ix));continue
  reasons=[];before=body
  for old,new in fixes.get(num,[]):
   if body.count(old)!=1:errors.append({'path':p,'literal_esperado':old,'ocorrencias':body.count(old)});continue
   body=body.replace(old,new,1);reasons.append({'tipo':'reparo_markup_literal','antes':old,'depois':new})
  if num in native:
   normalized,admin=normalizar_marcador_administrativo(src.decode(),r)
   for match in reversed(list(re.finditer(r'###DEC-(\d+)-([A-Za-z0-9]+)-000-(\d\d)-(\d\d)-(\d{4})@@@',normalized))):
    nu,c,d,mo,y=match.groups();no=str(int(nu))+('' if c=='0' else '-'+c)
    if numero_normalizado(no)==num and y+'-'+mo+'-'+d==ep['data']:normalized=normalized[:match.start()]+normalized[match.end():]
   match=re.search(r'<body\b[^>]*>([\s\S]*?)</body>',normalized,re.I);assert match
   body=before.lstrip().partition('\n')[0]+'\n\n'+match[1].strip()+'\n';reasons.append({'tipo':'HTML_original_area_normativa','motivo':'Preserva pontuação, zeros literais e eventos ol/ul/li/type/start/value da fonte, inclusive em tabelas. Sem afirmação de identidade visual CSS.'})
  if p in fechos:
   tr=fechos[p];ctx=tr['contexto'];lit=ctx['fechos'][-1]['literal'] if tr['tipo']=='fecho_divergente' else ctx['contexto'];note='Nota editorial: a epígrafe do texto oficial, o índice do Senado e os metadados oficiais identificam este decreto como nº '+num+', de '+ep['data']+'. A fonte consultada apresenta no trecho de encerramento a literalidade '+json.dumps(lit,ensure_ascii=False)+'. Esse trecho pode pertencer ao comando principal ou a documento incorporado; o contexto está preservado no recibo. O corpo não foi emendado para corrigir datas, ortografia ou números. Não se certifica retificação da data pela presente nota. Fonte: '+r['url_texto']+'; SHA-256 do HTML: '+sha(src)+'.';assert 'observacao_literalidade_fecho:' not in cab;cab=cab.rstrip('\n')+'\nobservacao_literalidade_fecho: '+json.dumps(note,ensure_ascii=False)+'\n';notes.append({'path':p,'nota':note,'triagem':tr,'indice':ix});reasons.append({'tipo':'nota_literalidade_fecho_sem_emenda','triagem':tr})
  new=('---\n'+cab.rstrip('\n')+'\n---\n'+body).encode() if reasons else raw;candidate=p
  if new!=raw:
   cp=C/Path(p).name;assert not cp.exists();cp.write_bytes(new);candidate=str(cp.relative_to(ROOT));prom.append({'path':p,'candidate':candidate,'sha256_preimagem':sha(raw),'sha256_candidato':sha(new),'HTML_original':num in native,'alteracoes':reasons})
  q=dict(r,lote=n,sha256=sha(new),sha256_preimagem=sha(raw),arquivo_final=candidate,HTML_original=num in native,proof=proofs[p]);allrows.append(q)
print('erros literais',errors);assert not errors
(D/'preparo.json').write_text(json.dumps({'publicaveis':allrows,'retidos':ret,'promocoes':prom,'notas_contextuais':notes},ensure_ascii=False,indent=2)+'\n');(D/'render_input.json').write_text(json.dumps([{'path':r['path'],'markdown':fields((ROOT/r['arquivo_final']).read_text())[2].lstrip().partition('\n')[2]} for r in allrows]));print('PUBLICAVEIS',len(allrows),'RETIDOS',len(ret),'PROMOS',len(prom),'NOTAS',len(notes),'NATIVOS',len(native),flush=True)
