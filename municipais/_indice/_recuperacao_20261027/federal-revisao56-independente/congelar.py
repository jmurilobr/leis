"""Parecer privado de leitura dos 56 corpos; não altera normas ou máscaras."""
from pathlib import Path
import base64, collections, datetime, difflib, gzip, hashlib, json, re, subprocess, sys
from lxml import html

R = Path.cwd()
B = Path(__file__).resolve().parent
S = R / 'federal/_fonte/auditorias/inventario_objetos_tecnicos1347_20261027_001'
sha = lambda b: hashlib.sha256(b).hexdigest()
rows = list(map(json.loads, gzip.open(S / 'fontes_contextos.jsonl.gz', 'rt')))
strata = {r['path']:r for r in json.loads((S/'revisao_estratos56.json').read_text())['registros']}
assert len(rows) == len(strata) == 56
head = subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
raw = subprocess.check_output(['git','cat-file','--batch'], input=''.join(head+':'+r['diagnostico']['path']+'\n' for r in rows).encode())
pos = 0
out = []
specific = {
 1344: 'As especificações do hangar também são aprovadas como documentos que baixam rubricados. Os dois totais e a conta do excesso não reproduzem as especificações. Não é um caso de orçamento isolado.',
 1920: 'A relação a–e, com cinco obras/aquisições e respectivos valores, está representada integralmente no articulado, assim como os cinco prazos. Não classifico essa relação como ausente. O vínculo adicional a projetos rubricados permanece sem representação própria.',
 2249: 'As seis alíneas a–f e seus valores estão presentes, seguidas dos artigos 2º–4º sobre substituições, exclusões e custeio. Não falta a relação de aquisições. Os projetos rubricados adicionais não são representados.',
 3405: 'As alíneas a–c discriminam integralmente as três obras e os valores; o parágrafo único conserva a retificação dos orçamentos. Isso preserva a relação aprovada. Não comprova os projetos que o mesmo artigo declara baixar. A menção ao programa de 1935 não transforma o vínculo atual em referência somente histórica.',
 1922: 'As condições 1ª–3ª estão presentes, inclusive a obrigação futura de apresentar orçamento mais detalhado e projetos com maiores detalhes. Essa obrigação futura não é documento já omitido por si só; contudo o caput aprova projeto e orçamento estimativo atuais que declara baixar. Esses objetos atuais não aparecem separadamente.',
 3028: 'A alteração do recobrimento do concreto (0m,03/0m,05) está transcrita no art. 2º. A mesma nova redação aprova novo orçamento e remete expressamente a planta e memória descritiva que baixam com este decreto. Trata-se de objeto do ato modificador, não só da remissão histórica ao Decreto 689/1936.',
 3165: 'A menção preliminar ao Decreto 2.702/1938 é histórica; o artigo único aprova novo projeto e orçamento, que com este baixam. O objeto atual é distinto da referência ao ato anterior.',
 3027: 'O artigo exige correspondência às especificações dos orçamentos inclusos. Quantidades, bitola e total não reproduzem essas especificações; há evidência textual adicional à mera menção a um total.',
 3265: 'O artigo descreve quantidade, trucks, bitola, capacidade e material dos vagões, mas exige também correspondência às especificações do orçamento incluso. Não equiparo automaticamente a descrição resumida às especificações declaradas inclusas.',
 3019: 'Só o orçamento provável baixa. Total e descrição dos componentes da obra estão presentes. Sem documento original discriminado, o cache não prova se havia outras rubricas ou se o ato resumia todo o orçamento; retenção por dúvida documental, não omissão quantitativa provada.',
 3061: 'Só o orçamento provável baixa. Estão presentes o total e os componentes da obra. O vínculo documental é explícito, mas o cache não permite provar detalhamento adicional ausente; não classifico o total como faltante.',
 3175: 'Só o orçamento provável baixa. O total e o objeto da duplicação estão transcritos. Há dúvida de representação do documento rubricado, sem prova de rubricas adicionais ou de omissão do valor.',
 6115: 'O orçamento não é numericamente ausente: o art. 2º traz 13:815$830. Os arts. 1º–3º e o fecho estão presentes. O projeto e orçamento próprios declarados no art. 1º continuam sem representação documental separada.',
 6114: 'A capacidade de 9.000 litros, os componentes, o total, o custeio, o prazo e o fecho estão presentes. Esses dados resumidos não reproduzem o projeto e orçamento básico próprios declarados no art. 1º.',
}
for row in rows:
 d = row['diagnostico']; p = d['path']; number = int(re.search(r'/dec-(\d+)-',p)[1])
 raw_html = base64.b64decode(row['HTML_primario_base64']); md = row['MD_candidato_utf8']
 assert sha(raw_html)==d['sha256_HTML_primario'] and sha(md.encode())==d['sha256_MD_candidato']
 assert sha(row['metadados_raw'].encode())==d['sha256_API']
 end = raw.index(b'\n',pos); hdr=raw[pos:end].split();pos=end+1
 if hdr[-1]==b'missing': current={'commit':head,'estado':'ausente'}
 else:
  size=int(hdr[2]); blob=raw[pos:pos+size];pos+=size+1
  current={'commit':head,'OID':hdr[0].decode(),'sha256':sha(blob),'igual_candidato':sha(blob)==d['sha256_MD_candidato']}
  assert current['igual_candidato']
 doc=html.fromstring(raw_html)
 areas=doc.xpath('//div[contains(concat(" ",normalize-space(@class)," ")," textoNorma ")]')
 if areas: assert len(areas)==1;area=areas[0];selection='div.textoNorma único (DOM lxml independente)'
 else: area=doc.find('body');assert area is not None;selection='body integral do HTML autônomo'
 for node in area.xpath('.//script|.//style'):node.drop_tree()
 media=[{'tag':e.tag,'atributos':dict(e.attrib)} for e in area.xpath('.//img|.//svg|.//canvas|.//object|.//embed|.//table')]
 links=[{'texto':e.text_content(),'href':e.get('href')} for e in area.xpath('.//a[@href]')]
 assert not media and not links
 body=md.split('\n---\n',1)[-1]
 st=strata[p]['estrato_contextual']
 if number in (3019,3061,3175): category='duvida_documental_orcamento_total'; recommendation='Submeter a decisão ROOT como dúvida de integralidade documental, sem afirmar orçamento ou rubricas numericamente omitidos.'
 elif number in (1920,2249,3405):category='relacao_integral_presente_projeto_proprio_nao_representado';recommendation='Preservar a relação completa; considerar pendência somente do projeto próprio não representado, sem declarar a relação truncada.'
 elif 'planta_' in st: category='planta_propria_nao_representada';recommendation='Propor pendência de representação da planta própria; o texto de autorização e seus limites permanece válido como transcrição do articulado.'
 elif number in (1344,3027,3265):category='especificacoes_proprias_nao_representadas';recommendation='Propor pendência do documento/especificações que o articulado declara baixar/incluir; os totais e descrições presentes não são omissões.'
 else:category='projeto_estudos_proprios_nao_representados';recommendation='Propor pendência do projeto/estudos atuais declarados próprios; não afirmar ausência em todas as publicações oficiais nem defeito de conversão.'
 rationale=specific.get(number)
 if rationale is None:
  if 'planta_' in st:rationale='A autorização descreve a ligação e seus extremos, mas declara baixar planta própria autenticada. A área normativa integral não contém imagem, tabela, anexo textual substitutivo ou link para essa planta; os extremos da ligação não representam seu desenho.'
  else:rationale='O dispositivo de aprovação vincula o projeto/estudos e orçamento atuais ao próprio decreto, com autenticação/rubrica. O restante do corpo conserva custeio, prazo ou fecho, conforme aplicável, sem reproduzir o projeto/estudos. Valor e localização da obra identificam o objeto, mas não substituem sua representação técnica.'
 out.append({'path':p,'numero':number,'HEAD_atual':current,'sha256_MD':d['sha256_MD_candidato'],'sha256_HTML':d['sha256_HTML_primario'],'sha256_API':d['sha256_API'],'fonte':d['fonte_HTML'],'categoria':category,'parecer':rationale,'recomendacao_privada':recommendation,'trechos_vinculo_integrais':d['vinculos_tecnicos_antes_fecho'],'leitura_integral_MD':body,'selecao_HTML':selection,'texto_integral_HTML_area':area.text_content(),'midias_tabelas_area':media,'links_area':links,'referencia_somente_historica':False,'objeto_proprio_integralmente_demonstrado':False,'limite':'Ausência de representação no snapshot examinado; não prova que o documento deixou de existir, nunca foi publicado ou que houve perda pelo conversor. Decisão e máscaras reservadas ao ROOT.'})
assert pos==len(raw)
counts=dict(collections.Counter(x['categoria'] for x in out));published=[x for x in out if 'OID' in x['HEAD_atual']]
assert len(published)==32
result={'data_parecer':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3))).isoformat(),'commit_HEAD':head,'casos':56,'publicados':32,'privados':24,'contagens':counts,'publicados_por_categoria':dict(collections.Counter(x['categoria'] for x in published)),'rede':False,'mascaras_aplicadas':0,'canonicos_modificados':0,'criterio':'Leitura individual do corpo integral e contexto, inspeção DOM integral da área normativa e confirmação SHA/OID atual. Parecer documental privado, não regra de regex. Relações completas não são invalidadas pela remissão; a lacuna de projeto pode coexistir com a relação presente. Orçamento apenas total permanece dúvida separada.','entradas':[{'path':str(x.relative_to(R)),'sha256':sha(x.read_bytes())} for x in [S/'fontes_contextos.jsonl.gz',S/'revisao_estratos56.json']],'registros':out}
(B/'parecer56.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
for name,rr in [('publicados32.paths.txt',published),('privados24.paths.txt',[x for x in out if 'OID' not in x['HEAD_atual']])]: (B/name).write_text(''.join(x['path']+'\n' for x in rr))
files=[B/'congelar.py',B/'parecer56.json',B/'publicados32.paths.txt',B/'privados24.paths.txt']
(B/'manifesto.json').write_text(json.dumps({'casos':56,'arquivos':[{'path':str(x.relative_to(R)),'sha256':sha(x.read_bytes()),'bytes':x.stat().st_size} for x in files],'fontes_referenciadas':result['entradas']},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'contagens':counts,'publicados':32,'privados':24,'manifesto':str((B/'manifesto.json').relative_to(R)),'sha256':sha((B/'manifesto.json').read_bytes())},ensure_ascii=False))
