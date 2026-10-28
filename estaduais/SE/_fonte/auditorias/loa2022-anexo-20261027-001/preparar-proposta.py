import json,hashlib,gzip,re,shutil,datetime,sys
from pathlib import Path
sys.path[:0]=['scripts/estados/snapshots/se_loa8963_20261027_001']
from comum import decodificar
from html2md import convert
SHA=lambda b:hashlib.sha256(b).hexdigest()
base=Path('estaduais/SE/_fonte/auditorias/loa8963-privado-20261027-001');base.mkdir(exist_ok=False)
sources=Path('estaduais/SE/_fonte/auditorias/loa2022-anexo-20261027-001');pdfcapture=json.load(open(sources/'captura.json'))
c=next(r for r in json.load(open('scripts/estados/manifestos/se-textos-html-20261027-005.json'))['capturas'] if r['item']['id']=='10142');it=c['item']
source=decodificar(gzip.decompress(Path(c['cache']).read_bytes()));body=convert(re.sub(r'<img\b[^>]*>','',source,flags=re.I));PDF=(sources/'anexo-oficial.pdf').read_bytes();assert SHA(PDF)==pdfcapture['sha256_fonte']
path='estaduais/SE/leis-ordinarias/2022/l-8963-2022-id10142.md';asset='estaduais/SE/anexos/2022/l-8963-2022-id10142.pdf';link='../../anexos/2022/l-8963-2022-id10142.pdf'
private=base/'candidatos'/path;private.parent.mkdir(parents=True,exist_ok=True);privatePDF=base/'candidatos'/asset;privatePDF.parent.mkdir(parents=True,exist_ok=True);privatePDF.write_bytes(PDF)
title='Lei Ordinária nº8963, de2022-01-13'.replace('nº8963','nº 8963').replace('de2022','de 2022')
note='Epígrafe, fecho, cartão e capa do PDF dos anexos identificam a Lei8.963 de13/01/2022. O rodapé editorial do HTML informa D.O.E. de07/01/2022, referência anterior ainda não cotejada com edição DOE. Datas e referência editorial foram preservadas, sem escolher outra data de publicação. A URL do anexo contém8819; o conteúdo integral identifica8.963/2022.'
# Nota objetiva da divergência editorial, sem correção por suposição.
note=note.replace('Lei8.963','Lei 8.963').replace('de13/','de 13/').replace('de07/','de 07/').replace('contém8819','contém 8819').replace('identifica8.963','identifica 8.963')
meta=dict(titulo=title,uf='SE',tipo=it['tipo'],numero=it['numero'],data=it['data'],ementa=it['ementa'],situacao=it['situacao'],revogada=None,versao_texto='Articulado HTML integral fornecido pela ALESE e anexosI/II em PDF oficial integral local; edição DOE não certificada',representacao_anexos='pdf-oficial-integral-local-v1',anexos_integrais=[dict(arquivo=asset,sha256=SHA(PDF),bytes=len(PDF),paginas=522)],publicacao='D.O.E de07.01.2022 (referência editorial literal divergente; ver observacao_edicao)',observacao_edicao=note,fonte=it['fonte'],arquivo=c['url'],baixado_em=c['capturado_em'][:10])
extra='\n\n## Anexos integrais\n\n[Anexos I e II — PDF oficial integral, 522 páginas]('+link+')\n'
md='---\n'+''.join(k+': '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in meta.items())+'---\n# '+title+'\n\n'+body+extra;private.write_text(md,encoding='utf-8',newline='\n')
images=[r for r in json.load(open('scripts/estados/manifestos/se-visuais-html-20261027-005.json'))['capturas'] if r['id']=='10142'];assert len(images)==1
snapshot=Path('scripts/estados/snapshots/se_loa8963_20261027_001');code={str(p):SHA(p.read_bytes()) for p in snapshot.glob('*.py')}
manifest=Path('scripts/estados/manifestos/se-LOA8963-proposta-individual-20261027-001.json')
m=dict(preparado_em=datetime.datetime.now().astimezone().isoformat(),normas_novas=1,promovidas=0,sem_promocao=True,proposta_individual=True,sem_excecao_global=True,documento=dict(path=path,privado=str(private),sha256_md=SHA(private.read_bytes()),sha256_corpo_HTML=SHA(body.encode()),captura=c),anexo=dict(path=asset,privado=str(privatePDF),sha256=SHA(PDF),bytes=len(PDF),paginas=522),captura_PDF=pdfcapture,imagens=images,codigo=code,observacao_edicao=note,acrescimo_apresentacao=extra,link_relativo_anexo=link,prova_escopo=str(sources/'prova-escopo-integral-522.json'),representacao='PDF original integral como anexo local, sem transcrição nem supressão de qualquer objeto/vetor/gráfico/tabela/imagem. HTML principal preservado integralmente; somente apresentação adicional do link relativo ao anexo.',nota_preliminar_PDF='Inventário antigo não recursivo de operadores não comprova ausência de curvas: foi superado pelo inventário recursivo v2. Curvas permanecem no PDF completo; não dependemos de interpretá-las para preservação.',comando_replay=f'PYTHONPATH="$PWD/scripts/bin/qa-20261027/python" /Users/joaodavisn/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 {snapshot}/reexecutar_loa8963.py --manifesto {manifest} --saida CAMINHO_NOVO.json')
manifest.open('x').write(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
paths=set(code)|{str(manifest),str(private),str(privatePDF),str(sources/'captura.json'),pdfcapture['cache'],c['cache'],it['indice']['cache'],images[0]['arquivo'],str(sources/'prova-escopo-integral-522.json'),str(sources/'inventario-operadores-PDF-recursivo-v2.json'),str(sources/'texto-layout-integral.txt'),str(sources/'preparar-proposta.py')}
for n in [1,2,3,4,5,438,517,522]:paths.add(str(sources/f'pagina-{n}.png'))
assert all(not Path(p).is_absolute() and '..' not in Path(p).parts for p in paths)
(base/'dependencias-iniciais.json').write_text(json.dumps(sorted(paths),ensure_ascii=False,indent=2)+'\n');print(manifest,SHA(manifest.read_bytes()),len(paths))
