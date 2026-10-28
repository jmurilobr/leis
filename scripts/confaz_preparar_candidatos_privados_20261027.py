"""Prepara candidatos compactados e mapas privados; nunca escreve canônicos."""
import argparse
import datetime as dt
from email.utils import parsedate_to_datetime
import gzip
import hashlib
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from confaz_auditar_piloto_privado_v2_20261027 import html5lib,representar,campo
from auditar import validar


def sha(b):return hashlib.sha256(b).hexdigest()


def dia_captura(proof,root_day):
    if proof.get('capturado_em_cliente'):
        value=dt.datetime.fromisoformat(proof['capturado_em_cliente'])
        if value.tzinfo is None:raise ValueError('Captura nova sem fuso explícito')
        return value.astimezone(ZoneInfo('America/Recife')).date().isoformat(),'timestamp original do cliente com fuso, convertido para America/Recife'
    if proof.get('origem_sondagem'):
        http=parsedate_to_datetime(proof['captura_http_date']).astimezone(ZoneInfo('America/Recife')).date().isoformat()
        if http!=root_day:raise ValueError('Dia declarado da sondagem ROOT diverge do HTTP Date; exige conciliação')
        return root_day,'dia original da sondagem ROOT informado explicitamente e corroborado por HTTP Date; horário do cliente não fornecido e não inventado'
    raise ValueError('Origem temporal da captura não comprovada')


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--qa',type=Path,required=True);ap.add_argument('--head',type=Path,required=True);ap.add_argument('--data-sondagem-root',required=True);ap.add_argument('--saida',type=Path,required=True);a=ap.parse_args()
    dt.date.fromisoformat(a.data_sondagem_root);a.saida.mkdir(parents=True,exist_ok=False)
    qa=json.loads((a.qa/'resumo.json').read_text());head=json.loads((a.head/'confronto-head.json').read_text());by_number={r['numero']:r for r in head['resultados']};rows=[];ns='{http://www.w3.org/1999/xhtml}'
    for r in qa['resultados']:
        number=r['numero_indice'];match=by_number[number]
        if r['estado']=='retido' or match['estado']!='candidato_privado_sem_alias_HEAD':continue
        proof=r['fonte'];source=(ROOT/proof['arquivo']).read_bytes();assert sha(source)==proof['sha256']
        fragment=campo(source.decode());native=representar(fragment)
        assert sha(native.encode())==r['sha256_representacao']
        doc=html5lib.parseFragment(fragment,treebuilder='etree');p=next(doc.iter(ns+'p'));title=' '.join(''.join(p.itertext()).split())
        date,temporal=dia_captura(proof,a.data_sondagem_root);identity=r['identidade']
        target=f'reguladores/confaz/convenios/{identity["ano"]}/convenio-icms-{number}-{identity["ano"]}.md'
        meta=dict(titulo=title,orgao='Conselho Nacional de Política Fazendária (CONFAZ)',tipo='Convênio ICMS',numero=str(number),
            data=identity['data'],revogada=None,versao_texto='Texto e notas oficiais do portal CONFAZ conforme a captura; sem certificação de vigência.',
            fonte=proof['url'],sha256_html_fonte=proof['sha256'],sha256_texto=sha(native.encode()),baixado_em=date,
            representacao_corpo='html-nativo-confaz-piloto-v1',observacao_captura=temporal,
            observacao_efeitos='Condições de ratificação e produção de efeitos preservadas literalmente. Nenhuma data de vigência calculada.',
            publicacao_fonte=' | '.join(r.get('notas_publicacao_ratificacao_literais',[])))
        text='---\n'+''.join(k+': '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in meta.items())+'---\n# '+title+'\n\n'+native+'\n'
        errors,warnings=validar(text,target,dt.date.today());assert not errors,(target,errors)
        raw=text.encode();txt=a.saida/f'{number}.candidato.txt';gz=a.saida/f'{number}.candidato.md.gz';txt.write_bytes(raw);gz.write_bytes(gzip.compress(raw,mtime=0))
        existing=ROOT/target
        rows.append(dict(numero=number,ano=identity['ano'],path_canonico_proposto=target,candidato=str(txt),candidato_gzip=str(gz),
            sha256_md=sha(raw),sha256_gzip=sha(gz.read_bytes()),bytes_md=len(raw),estado='candidato privado; sem promoção',
            alvo_preexistente=existing.exists(),sha256_alvo_preexistente=sha(existing.read_bytes()) if existing.exists() else None,
            fonte=proof,controle_qa=str(a.qa/str(number)/'controle.json'),sha256_controle_qa=sha((a.qa/str(number)/'controle.json').read_bytes()),
            commit_confronto=head['commit'],avisos_formato=warnings,metadata=meta))
    result=dict(candidatos=len(rows),resultados=rows,confronto_HEAD=str(a.head/'confronto-head.json'),sha256_confronto=sha((a.head/'confronto-head.json').read_bytes()),
        promocao_automatica=False,limite='Somente candidatos privados. ROOT deve revalidar HEAD/reservas e ausência/preimagem do alvo antes de promover. Histórico não entra nesta seleção; não há afirmação de vigência.')
    (a.saida/'mapa-candidatos.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(candidatos=len(rows),alvos_preexistentes=sum(r['alvo_preexistente'] for r in rows))))


if __name__=='__main__':main()
