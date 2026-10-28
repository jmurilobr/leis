"""Uma consulta comum, sem retries, redirects, cookies ou promoção de texto."""
from pathlib import Path
import datetime as dt,difflib,hashlib,html.parser,json,re,subprocess,sys
from zoneinfo import ZoneInfo
ROOT=Path.cwd();B=ROOT/'_fonte/vigencia_cf_20261028_001';URL='https://www.planalto.gov.br/ccivil_03/constituicao/constituicaocompilado.htm'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def info(path):
 raw=path.read_bytes();return dict(arquivo=str(path.relative_to(ROOT)),sha256=sha(raw),bytes=len(raw))
def save(name,value):
 with (B/name).open('x') as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
start=dt.datetime.now(dt.timezone.utc)
command=['/usr/bin/curl','--http1.1','--silent','--show-error','--connect-timeout','15','--max-time','45','--retry','0','--max-redirs','0','--dump-header',str(B/'headers.http.txt'),'--output',str(B/'resposta.http-body'),'--write-out','%{http_code}\n%{url_effective}\n%{content_type}\n%{size_download}\n%{num_redirects}\n',URL]
proc=subprocess.run(command,capture_output=True,timeout=55)
finish=dt.datetime.now(dt.timezone.utc);(B/'curl.stdout.txt').write_bytes(proc.stdout);(B/'curl.stderr.txt').write_bytes(proc.stderr);output=proc.stdout.decode('utf-8','replace').splitlines();status=int(output[0]) if output and output[0].isdigit() else None
headers=(B/'headers.http.txt').read_bytes() if (B/'headers.http.txt').exists() else b'';body=(B/'resposta.http-body').read_bytes() if (B/'resposta.http-body').exists() else None
receipt=dict(url=URL,inicio_UTC=start.isoformat(),fim_UTC=finish.isoformat(),inicio_America_Recife=start.astimezone(ZoneInfo('America/Recife')).isoformat(),fim_America_Recife=finish.astimezone(ZoneInfo('America/Recife')).isoformat(),dia_captura_America_Recife=start.astimezone(ZoneInfo('America/Recife')).date().isoformat(),comando=command,curl_exit=proc.returncode,HTTP_status=status,url_efetiva=output[1] if len(output)>1 else None,content_type=output[2] if len(output)>2 else None,redirects_seguidos=output[4] if len(output)>4 else None,headers=info(B/'headers.http.txt') if (B/'headers.http.txt').exists() else None,corpo_recebido=info(B/'resposta.http-body') if body is not None else None,erro=proc.stderr.decode('utf-8','replace'),consultas_HTTP_solicitadas=1,retries_configurados=0,cookies_enviados=False,redirects_automaticos=False)
save('recibo-http.json',receipt)
# Referências são lidas do disco, sem reconstrução de qualquer snapshot ausente.
sys.path.insert(0,str(ROOT/'scripts'));import converter_constituicao as cf
old20=ROOT/'fonte/constituicao-compilado.htm';meta20=json.loads((ROOT/'fonte/constituicao-compilado.json').read_text());raw20=old20.read_bytes();assert sha(raw20)==meta20['sha256'];b20=cf.converter(raw20.decode(meta20['encoding']));canon=(ROOT/'constituicao.md').read_bytes();assert canon.decode()==cf.documento(raw20,meta20)
refs=dict(snapshot20=info(old20),metadata20=info(ROOT/'fonte/constituicao-compilado.json'),canonico=info(ROOT/'constituicao.md'),corpo20_sha256=sha(b20.encode()),corpo20_caracteres=len(b20),canonico_reproduz_snapshot20=True,emenda141=info(ROOT/'fonte/emc141.htm'))
path27=ROOT/'_fonte/operacao_root_20261027/constituicao-compilado-20261027.htm';meta27path=ROOT/'_fonte/operacao_root_20261027/constituicao-consulta-20261027.json';b27=None
if meta27path.exists():
 m27=json.loads(meta27path.read_text());refs['recibo27']=info(meta27path);refs['snapshot27_hash_registrado']=m27['sha256']
 if path27.exists():
  r27=path27.read_bytes();refs['arquivo27_presente']=info(path27)
  if sha(r27)==m27['sha256'] and len(r27)==m27['bytes']:b27=cf.converter(r27.decode(meta20['encoding']));refs.update(snapshot27_bruto_verificado=True,corpo27_sha256=sha(b27.encode()))
  else:refs['snapshot27_bruto_verificado']=False
 else:refs.update(snapshot27_bruto_verificado=False,limite27='Raw ausente; não reconstruído.')
comparison=dict(referencias=refs,HTTP200_HTML_valido=False,canonicо_alterado=False,limite='Consulta da edição oficial servida; não certifica vigência hoje, eficácia imediata ou ausência de outras alterações/emendas.')
if proc.returncode==0 and status==200 and body and receipt['content_type'] and 'html' in receipt['content_type'].lower():
 charset=re.search(r'charset\s*=\s*["\']?([a-zA-Z0-9_-]+)',receipt['content_type'],re.I)
 if not charset:charset=re.search(br'charset\s*=\s*["\']?([a-zA-Z0-9_-]+)',body[:15000],re.I)
 encoding=(charset[1].decode('ascii') if isinstance(charset[1],bytes) else charset[1]) if charset else meta20['encoding']
 try:
  source=body.decode(encoding);current=cf.converter(source)
  if '<html' not in source.lower() or len(current)<500000:raise ValueError('HTML/corpo insuficientes para a CF compilada')
  (B/'corpo-compilado-consulta.md').write_bytes(current.encode());(B/'corpo-20-vs-consulta.diff').write_text(''.join(difflib.unified_diff(b20.splitlines(True),current.splitlines(True),fromfile='corpo-snapshot20',tofile='corpo-consulta')));(B/'html-20-vs-consulta.diff').write_text(''.join(difflib.unified_diff(raw20.decode(meta20['encoding']).splitlines(True),source.splitlines(True),fromfile='HTML20',tofile='HTML-consulta')))
  if b27 is not None:(B/'corpo-27-vs-consulta.diff').write_text(''.join(difflib.unified_diff(b27.splitlines(True),current.splitlines(True),fromfile='corpo-snapshot27-verificado',tofile='corpo-consulta')))
  prefix=canon.decode().split('## PREÂMBULO\n',1)[0];(B/'notas-canonicas-para-revisao.txt').write_text(prefix)
  comparison.update(HTTP200_HTML_valido=True,encoding=encoding,corpo_consulta=info(B/'corpo-compilado-consulta.md'),corpo_consulta_caracteres=len(current),corpo20_igual=current==b20,corpo27_igual=current==b27 if b27 is not None else None,corpo_canonico_igual=current==canon.decode()[canon.decode().index('## PREÂMBULO\n'):],HTML20_bytes_iguais=body==raw20,HTML27_bytes_iguais=body==path27.read_bytes() if b27 is not None else None,modo='ConstituicaoParser(exclude_struck=True); rótulos de revogação, notas e transições da fonte preservados; nota editorial EC141 antiga separada, sem emenda nova consultada.',strikes_tags_fonte=len(re.findall(r'<(?:strike|s|del)(?:\s|>)',source,re.I)),estilos_line_through_fonte=len(re.findall('line-through',source,re.I)))
 except Exception as error:comparison['erro_validacao']=repr(error)
else:comparison['resultado']='Sem resposta HTTP 200 com HTML válido; nenhuma inferência de atualização ou vigência.'
save('comparacao.json',comparison)
code=B/'codigo';code.mkdir();
for filename in ['converter_constituicao.py','html2md.py']:(code/filename).write_bytes((ROOT/'scripts'/filename).read_bytes())
(B/'README.txt').write_text('Uma única requisição comum ao compilado oficial do Planalto, sem retries, redirects ou cookies. Resposta, headers, stdout/stderr e horários preservados. Comparação somente com bytes locais existentes e hashes registrados; nenhum raw ausente foi reconstruído. Nenhum canônico, HEAD ou índice alterado. O corpo, quando válido, passa pelo conversor específico de CF que exclui tachados; indicações literais de revogação/vigência e notas da fonte são preservadas. A nota editorial EC141 de 20/10 é mantida separada para revisão, sem afirmar eficácia atual ou fazer segunda consulta à emenda. Não executar consultar_uma_vez.py novamente sem nova autorização.\n')
files=[info(p) for p in sorted(B.rglob('*')) if p.is_file()];save('manifesto.json',dict(consulta=info(B/'recibo-http.json'),comparacao=info(B/'comparacao.json'),arquivos=files,consultas_HTTP=1,alteracoes_canonicas=0,limite=comparison['limite']))
print(json.dumps(dict(HTTP=status,curl_exit=proc.returncode,HTML_valido=comparison['HTTP200_HTML_valido'],manifesto=info(B/'manifesto.json'),corpo20_igual=comparison.get('corpo20_igual'),corpo27_igual=comparison.get('corpo27_igual')),ensure_ascii=False))
