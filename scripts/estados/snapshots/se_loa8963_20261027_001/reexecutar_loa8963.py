"""Replay individual da LOA com anexo PDF local intacto; não promove nem altera gates."""
import argparse,gzip,hashlib,json,re,subprocess
from pathlib import Path
from lxml import html
from auditar_spl_html_recente import auditar,identidade_html,comparar
from comum import decodificar
from html2md import convert
from qualificar_loa8963 import conferir_pdf
SHA=lambda b:hashlib.sha256(b).hexdigest()

def conferir(m):
 r=m['documento'];c=r['captura'];it=c['item'];assert (it['id'],it['numero'],it['data'])==('10142','8963','2022-01-13')
 # A restrição cronológica geral permanece ativa e deve reter exatamente o rodapé
 # conhecido. A proposta individual preserva a dúvida em observação explícita.
 try:auditar(c,m['imagens'])
 except ValueError as e:
  if 'dúvida cronológica: rodapé DOE anterior' not in str(e):raise
 else:raise ValueError('gate cronológico mudou; revisar edição individual')
 source=decodificar(gzip.decompress(Path(c['cache']).read_bytes()));body=convert(re.sub(r'<img\b[^>]*>','',source,flags=re.I));identity=identidade_html(source,it);proof=comparar(source,body)
 a=m['anexo'];pdf=Path(a['privado']).read_bytes();capture=m['captura_PDF'];z=Path(capture['cache']).read_bytes()
 assert SHA(z)==capture['sha256_cache'] and gzip.decompress(z)==pdf and SHA(pdf)==a['sha256']==capture['sha256_fonte']
 hrefs=html.fromstring(source).xpath('//a/@href')
 assert capture['href_literal'] in hrefs
 assert capture['url']==capture['url_final']==capture['href_literal'].replace('http://','https://',1)
 text=subprocess.check_output(['/opt/homebrew/bin/pdftotext','-layout',str(Path(a['privado'])),'-']).decode('utf-8',errors='strict')
 pdfproof=conferir_pdf(pdf,text)
 blob=Path(r['privado']).read_bytes();assert SHA(blob)==r['sha256_md'];header,rest=blob.decode().split('\n---\n',1)
 meta={k:json.loads(v) for ln in header.splitlines()[1:] if ': ' in ln for k,v in [ln.split(': ',1)]}
 assert meta['representacao_anexos']=='pdf-oficial-integral-local-v1' and meta['revogada'] is None
 assert all(meta[k]==it[k] for k in ['tipo','numero','data'])
 assert meta['observacao_edicao']==m['observacao_edicao'] and meta['anexos_integrais']==[dict(arquivo=a['path'],sha256=a['sha256'],bytes=3831792,paginas=522)]
 expected='# '+meta['titulo']+'\n\n'+body+m['acrescimo_apresentacao']
 assert rest==expected and SHA(body.encode())==r['sha256_corpo_HTML']
 # O anexo é local e inclui todos os bytes/objetos; não se apresenta a extração
 # diagnóstica como substituta das tabelas ou dos elementos vetoriais.
 assert r['path'].rsplit('/',1)[0]+'/'+m['link_relativo_anexo']
 from posixpath import normpath
 assert normpath(r['path'].rsplit('/',1)[0]+'/'+m['link_relativo_anexo'])==a['path']
 return dict(total=1,falhas=0,identidade=identity,QA_HTML=proof,PDF=pdfproof,fonte_primaria_preservada_integral=True,sem_transcricao_PDF=True,cronologia_editorial='Dúvida literal preservada em observacao_edicao; data não alterada; edição DOE não certificada.',limite='Proposta individual, sem exceção global de integralidade e sem promoção.')

def main():
 p=argparse.ArgumentParser();p.add_argument('--manifesto',required=True);p.add_argument('--saida',required=True);a=p.parse_args();m=json.load(open(a.manifesto));q=conferir(m);Path(a.saida).open('x').write(json.dumps(q,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(total=1,falhas=0,paginas=522)))
if __name__=='__main__':main()
