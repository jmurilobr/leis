import json,hashlib,shutil,datetime
from pathlib import Path
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
pub=Path('scripts/estados/manifestos/am-auditoria-PDF-publica-20261027-001');pub.mkdir(exist_ok=False);control=Path('estaduais/AM/_fonte/auditorias/am-auditoria-PDF-publica-20261027-001');control.mkdir(exist_ok=False);snap=Path('scripts/estados/snapshots/am_auditoria_pdf_20261027_001');snap.mkdir(exist_ok=False)
names=['am-amostra-PDF-cotejo-20261027-001.json','am-amostra-estratificada-PDF-20261027-001.json','am-amostra-PDF-capturas-20261027-001.json','am-amostra-PDF-capturas-20261027-002.json','am-amostra-PDF-continuacao-20261027-001.json','am-amostra-adicional12-20261027-001.json','am-amostra12-cotejo-PDF-20261027-001.json','am-amostra12-PDF-capturas-20261027-001.json','am-amostra12-continuacao-20261027-001.json','am-amostra12-continuacao-20261027-002.json','am-publicados4-cotejo-primario-20261027-001.json','am-publicacao-20261021-001.json','am-legisla-suplementos-sondagem-20261027-001.json','am-legisla-suplementos-viewer-20261027-001.json']
files=set();omitted=[];sources=[]
def walk(v):
 if isinstance(v,dict):
  for k,x in v.items():
   if k.lower() in ['set-cookie','cookie','authorization','proxy-authorization']:omitted.append(k);continue
   walk(x)
 elif isinstance(v,list):
  for x in v:walk(x)
 elif isinstance(v,str) and v.startswith(('estaduais/','scripts/')):
  p=Path(v)
  if p.is_file() and not (v.endswith('.md') and '/_fonte/' not in v):files.add(v)
def clean(v):
 if isinstance(v,dict):return {k:clean(x) for k,x in v.items() if k.lower() not in ['set-cookie','cookie','authorization','proxy-authorization']}
 if isinstance(v,list):return [clean(x) for x in v]
 return v
for n in names:
 orig=Path('scripts/estados/manifestos')/n;j=json.loads(orig.read_text());walk(j);p=pub/n;p.write_text(json.dumps(clean(j),ensure_ascii=False,indent=2)+'\n');sources.append(dict(original=str(orig),sha256_original=sha(orig),publico=str(p),sha256_publico=sha(p)))
# Exclude references to full candidate packets: audit contains only selected source records, no canonical laws.
files={f for f in files if '/manifestos/' not in f or Path(f).name in names}
files={f for f in files if not f.endswith('.md')}
for stem in ['amostra-PDF-20261027-001','amostra-PDF-20261027-002','amostra-PDF-20261027-003','amostra12-PDF-20261027-001','amostra12-continuacao-20261027-001','amostra12-continuacao-20261027-002','am-publicados4-revisao-20261027-001']:
 for p in (Path('estaduais/AM/_fonte/auditorias')/stem).rglob('*'):
  if p.is_file():files.add(str(p))
for id in ['15193','15194','15195','15197']:
 for p in (Path('estaduais/AM/_fonte/auditorias/anexos-recentes-20261021-001/QA')/id).rglob('*'):
  if p.is_file():files.add(str(p))
# Avoid publishing private unsanitized JSON; replace every selected receipt by sanitized public copy.
for orig in ['scripts/estados/manifestos/'+n for n in names]:files.discard(orig)
files.update(str(p) for p in pub.iterdir() if p.is_file())
code=['scripts/estados/reexecutar_sapl_recentes_pdf.py','scripts/estados/auditar_sapl_recentes_pdf.py','scripts/estados/pdf_texto_fiel.py','scripts/estados/auditar_rn_retomada_pdf.py','scripts/estados/legisla_am_assinatura.py','scripts/estados/coletar_rn_fontes.py']
code += [str(p) for p in Path('estaduais/AM/_fonte/auditorias/legisla-suplementos-20261027-001').glob('*.py') if p.name in ['capturar-amostra12.py','capturar-amostra12-continuacao.py','capturar-amostra12-continuacao002.py','relatar-amostra12.py','congelar-auditoria.py']]
for f in code:shutil.copyfile(f,snap/Path(f).name)
files.update(str(p) for p in snap.iterdir());files.add('_fonte/operacao_root_20261027/dependencias-qa.json')
manifest=dict(preparado_em=datetime.datetime.now().astimezone().isoformat(),normas_novas=0,canonicos_incluidos=0) if False else dict(preparado_em=datetime.datetime.now().astimezone().isoformat(),normas_novas=0,canonicos_incluidos=0)
manifest.update(escopo='Auditoria primária AM: amostra inicial de 4 + adicional de 12 e revisão dirigida dos 4 PDFs SAPL já publicados.',suspensao='Candidatos AM não cotejados suficientemente contra edição primária permanecem suspensos. Coerência interna do portal não prova fidelidade. A amostra não demonstra que todo o portal esteja incorreto; casos podem ser recuperados individualmente dos PDFs oficiais em pacote separado.',metas_inalteradas=True,sem_promocao=True,receipts_publicos=sources,omissao_headers_sessao=dict(politica='Valores Cookie/Set-Cookie/Authorization/Proxy-Authorization omitidos das cópias públicas; originais privados preservados.',ocorrencias=len(omitted)),dependencias='scripts/bin/qa-20261027/python; Poppler 26.10.0; versões exatas no recibo dependencias-qa.json',reproducao=['Conferir SHA256 de todos os arquivos pelo mapa.','Descomprimir caches gzip e comparar sha256_fonte dos registros HTTP.','Renderizar PDFs preservados com pdftoppm -png -scale-to 3000; comparar os trechos e escopo de ato nos relatórios com HTML integral e PNG. Não tratar atos da mesma página como parte da lei.','Quatro SAPL: PYTHONPATH absoluto central e snapshots de reexecutar_sapl_recentes_pdf.py --manifesto cópia pública/am-publicacao-20261021-001.json --saida caminho_novo; conferir 4/4, fonte/camada/CommonMark/identidade/imagens.'],limite_replay='Cotejo das amostras é humano visual documentado; nenhum algoritmo certifica sozinho igualdade PDF/HTML. Capturadores são prova de método, não devem ser reexecutados em rede para reproduzir auditoria já congelada.')
p=pub/'pacote-auditoria.json';p.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');files.add(str(p));mapping={f:sha(f) for f in sorted(files)};(control/'paths.txt').write_text('\n'.join(mapping)+'\n');(control/'hashes.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(total=len(files),bytes=sum(Path(f).stat().st_size for f in files),manifesto=str(p),sha256=sha(p),paths=str(control/'paths.txt'),hashes=str(control/'hashes.json'),headers_omitidos=len(omitted))))
