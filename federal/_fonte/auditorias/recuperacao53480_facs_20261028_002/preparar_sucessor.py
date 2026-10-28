from pathlib import Path
import hashlib,json,datetime,subprocess
R=Path.cwd(); D=Path(__file__).resolve().parent; O=R/'federal/_fonte/auditorias/recuperacao53480_facs_20261027_001'
def info(p):
 b=p.read_bytes(); return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
m=json.loads((O/'candidato53480.json').read_text()); old=(O/'dec-53480-1964-01-23-clbr-integral.md').read_text()
assert hashlib.sha256(old.encode()).hexdigest()==m['candidato']['sha256']
note='Edição fac-símile integral da CLBR de 1964, volume II, páginas 81–90 e nove folhas de mapas. A identidade 53.480, de 23/01/1964, é corroborada pelo índice da mesma edição, que remete esta ementa à página 81, pelos metadados e índice do Senado e pela publicação original da Câmara. A leitura anterior que afirmava categoricamente 53.490 no cabeçalho da página 81 foi retirada após revisão do scan original incorporado ao PDF; não se certifica divergência numérica nesse cabeçalho. O índice registra outro decreto 53.490 separadamente na página 100; não foi criado alias. O índice informa publicação em 30/01/1964 e retificação em 06/02/1964; esta reprodução corresponde à edição CLBR, sem certificar o conteúdo daquela retificação. A transcrição anterior do Normas foi arquivada integralmente. O artigo 7º desta edição contém 1.095 (mil e noventa e cinco), enquanto a transcrição anterior contém 1.095 mil (mil e noventa e cinco); não se mesclaram os corpos.'
new=old.replace(m['nota_editorial'],note); assert new!=old
assert new.split('\n---\n',1)[1]==old.split('\n---\n',1)[1]
c=D/'dec-53480-1964-01-23-clbr-integral.md'; c.write_text(new)
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(); pre=subprocess.check_output(['git','show',head+':'+m['path_canonico']]); assert hashlib.sha256(pre).hexdigest()==m['preimagem']['sha256']
(D/'preimagem_HEAD.md').write_bytes(pre)
for a in m['ativos_em_ordem_de_leitura']: assert info(R/a['path'])['sha256']==a['sha256']
m['candidato_anterior']=m['candidato']; m['candidato']=info(c);m['nota_editorial']=note;m['head_preimagem']=head;m['preimagem']=info(D/'preimagem_HEAD.md')
m['preparado_em']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3))).isoformat()
m['correcao_editorial']='Sucessor apenas da nota editorial; corpo fac-símile e 20 ativos idênticos. Afirmação categórica antiga de 53.490 invalidada, sem atribuir causa à fonte. A nova revisão visual é compatível com 53.480; a identificação não depende dessa leitura isolada.'
m['provas_novas']=[info(D/'scan_original-000.png'),info(D/'cabecalho_direto600.png')]
m['extracao_original']={'comando':'pdfimages -f 135 -l 135 -png PDF scan_original','pagina_pdf':135,'objeto':523,'largura':1206,'altura':1669,'ppi':200,'codificacao':'JBIG2, cinza, 1 bit, interpolação não','limite':'Extração mecânica do scan integral, sem edição de pixels. Renders em 300 ou 600 dpi não acrescentam resolução à fonte de 200 ppi.'}
(D/'candidato53480.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
files=sorted(p for p in D.iterdir() if p.is_file() and not p.name.startswith('entrega-'))
(D/'entrega-paths.txt').write_text(''.join(str(p.relative_to(R))+'\n' for p in files))
(D/'entrega-hashes.json').write_text(json.dumps([info(p) for p in files]+[info(D/'entrega-paths.txt')],ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'head':head,'candidato':info(c),'arquivos':len(files),'ativos_inalterados':20},ensure_ascii=False))
