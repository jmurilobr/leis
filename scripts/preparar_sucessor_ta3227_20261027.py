"""Exclui somente Buritis 8/1971 do agregado imutável 3.228; sem promoção."""
from pathlib import Path
import argparse,hashlib,json
R=Path(__file__).resolve().parent.parent
BASE=Path('municipais/_indice/_recuperacao_20261027')
SOURCE=BASE/'agregado3228-final/entrega-final.json'
SOURCE_SHA='b943946e069070e2d72ea8d367a9179f04592b3502e2b17c0c381f3341994f5e'
TARGET='municipais/MG/buritis/leis-ordinarias/1971/leis-ordinarias-8-1971-sapl-787.md'
TARGET_SHA='407f89d8c476b79487840a744769d63589d08d3968039c8ae8b9756446f470ba'
def sha(p):return hashlib.sha256((R/p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--saida',type=Path,required=True);a=ap.parse_args();assert sha(SOURCE)==SOURCE_SHA and sha(Path(TARGET))==TARGET_SHA
 m=json.loads((R/SOURCE).read_text());names=(R/m['lista_normas']).read_text().splitlines();assert len(names)==3228 and names.count(TARGET)==1
 rows=json.loads((R/m['mapeamento_fontes']).read_text());assert len(rows)==3228 and len([r for r in rows if r['path']==TARGET and r['sha256']==TARGET_SHA])==1
 records={}
 for r in m['arquivos']:
  p=Path(r['arquivo']);assert sha(p)==r['sha256'] and (R/p).stat().st_size==r['bytes']
  if str(p)!=TARGET:records[str(p)]=r
 a.saida.mkdir(parents=True,exist_ok=False)
 def add(p):records[str(p)]=dict(arquivo=str(p),sha256=sha(p),bytes=(R/p).stat().st_size)
 def dump(p,x):(R/p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');add(p)
 selected=[p for p in names if p!=TARGET];lista=a.saida/'normas.paths.txt';(R/lista).write_text('\n'.join(selected)+'\n');add(lista)
 mapping=a.saida/'mapeamento-fontes.json';dump(mapping,[r for r in rows if r['path']!=TARGET])
 dump(a.saida/'exclusao-individual.json',dict(path=TARGET,sha256_preimagem=TARGET_SHA,manifesto_original=str(SOURCE),sha256_manifesto_original=SOURCE_SHA,motivo='Fecho ativo possui os tachados literais Sebastião Alves e Secretário, seguidos de Secretário Substituto. A versão anterior omitia os dois trechos e os qualificava como históricos sem rótulo literal da fonte. ROOT decidiu manter fora da publicação até reparo explícito.',exclusoes=1,restantes=3227,inferencia_juridica=False,canonicos_alterados=0))
 add(SOURCE);add(Path(__file__).resolve().relative_to(R))
 listing=a.saida/'artefatos.paths.txt';(R/listing).write_text('\n'.join(sorted(records))+'\n');add(listing)
 m.update(normas=3227,lista_normas=str(lista),mapeamento_fontes=str(mapping),arquivos=list(records.values()),bytes=sum(r['bytes'] for r in records.values()),origem3228=dict(manifesto=str(SOURCE),sha256=SOURCE_SHA),exclusao=str(a.saida/'exclusao-individual.json'),limite='Sucessor de seleção: exclui somente um SHA de Buritis; preserva todos os demais caminhos/bytes e o pacote 3.228. Nenhum reparo foi promovido. Canonical Buritis excluído dos artefatos do sucessor, permanecendo provas nos controles anteriores.')
 receipt=a.saida/'entrega-final.json';(R/receipt).write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(manifesto=str(receipt),sha256=sha(receipt),normas=3227,arquivos=len(records))))
if __name__=='__main__':main()
