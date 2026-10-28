"""Consolida mapa de publicação V7, replay e CSS, sem alterar os pacotes ou Git."""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
import promover_reparos_ta47_20261028 as q

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for k in ['manifesto','replay','css','saida']:ap.add_argument('--'+k,type=Path,required=True)
 ap.add_argument('--sha256',required=True);a=ap.parse_args();a.manifesto=a.manifesto.resolve();a.replay=a.replay.resolve();a.css=a.css.resolve();out=a.saida.resolve()
 if not out.is_relative_to(q.BASE):raise ValueError('Saída fora do controle privado')
 m=q.verificar_manifesto(a.manifesto,a.sha256);replay=json.loads(a.replay.read_text());css=json.loads(a.css.read_text());n=m['normas']
 if not replay['apto_para_publicacao'] or replay['normas']!=n or replay['replay_aprovados']!=n or replay['problemas']:raise ValueError('Replay não está integralmente aprovado')
 s=css['resumo']
 if s['normas']!=n or any(s[k] for k in ['fontes_especiais_ativas','ocultacao_ativa','mso_hide_ativo','condicionais_ou_seletores_pendentes']):raise ValueError('CSS requer revisão')
 if any(not label['rotulo_literal_revogado'] for r in css['registros'] for label in r['dispositivos_ativos_classe_revogado']):raise ValueError('Classe revogado exige contexto')
 names=q.safe(m['lista_normas']).read_text().splitlines();mapping=json.loads(q.safe(m['mapeamento_fontes']).read_text());mapped={r['path']:r for r in mapping};css_paths={r['path']:r for r in css['registros']}
 if set(names)!=set(mapped) or set(names)!=set(css_paths):raise ValueError('Seleções não correspondem')
 files={r['arquivo']:r for r in m['arquivos']};out.mkdir(exist_ok=False)
 def add(p):r=q.info(p);files[r['arquivo']]=r
 def save(name,value):p=out/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');add(p)
 for p in [a.manifesto,a.replay,a.css,Path(__file__).resolve()]:add(p)
 exports=json.loads(q.safe(m['exportacao_isolada']).read_text())
 if exports['normas']!=n or exports['canonicos_alterados']!=0:raise ValueError('Exportação não comprovada')
 for r in exports['arquivos']:
  if q.sha(q.safe(r['path']).read_bytes())!=r['sha256'] or q.sha(q.safe(r['exportado']).read_bytes())!=r['sha256']:raise ValueError('Exportação isolada diverge')
 for p in names:
  r=mapped[p];c=css_paths[p]
  if c['sha256_candidato']!=r['sha256'] or c['sha256_HTML_primario']!=r['fonte']['sha256']:raise ValueError('CSS fonte/candidato difere')
 save('controle-final.json',dict(normas=n,replays=n,CSS=s,exportacoes_isoladas=n,canonicos_alterados=0,colisoes=0,limite='Qualificação da edição pública capturada; não certifica vigência integral. CSS externo e JavaScript não executados.'))
 save('normas-hashes.json',[dict(arquivo=p,sha256=mapped[p]['sha256'],bytes=q.safe(p).stat().st_size) for p in names])
 whitespace=[]
 for p in names:
  raw=q.safe(p).read_bytes();whitespace.append(dict(path=p,hardbreaks=sum(x.endswith(b'  ') for x in raw.splitlines()),EOF_hex=raw[-16:].hex(),CRLF=raw.count(b'\r\n'),U0002=raw.count(b'\x02')))
 save('whitespace.json',whitespace)
 note=out/'INSTRUCOES_ROOT.txt';note.write_text('Pacote de normas novas em rotas criadas exclusivamente; nenhum canônico preexistente foi substituído.\nRepetir V3: Python bundled -I scripts/verificar_entrega_ta_sem_promocoes_v3_privado_20261027.py --manifesto MANIFESTO_DE_ORIGEM --replay --saida NOVA_SAIDA.json\nAntes de publicar, repetir dedup contra HEAD por OID e reservas qualificadas; manter identificação do commit e SHA de cada reserva. O baseline deste pacote já reconciliou 4.734 anteriores em HEAD e 47 candidatos por SHA futuro.\nStaging exclusivamente ROOT: git --literal-pathspecs -c core.autocrlf=false add -f --pathspec-from-file=ESTE_DIRETORIO/stage.paths.z --pathspec-file-nul\nConferir blobs indexados contra arquivos deste manifesto e SHA externo do próprio manifesto. Não formatar hardbreaks/EOF, não normalizar controles ou Unicode e não usar git apply --whitespace=fix.\nTachados no corpo selecionado são preservados pelo perfil V7, sem inferência de revogação. CSS estático interno/inline, fontes especiais, ocultação e contextos foram examinados; folhas externas não consultadas. Fonte complicada ou ausente permanece retida.\nExportados .txt são cópias isoladas byte-identical para conferência, não outras normas a contar. Metadados usam a captura original com dia America/Recife quando há offset.\n');add(note)
 stage=sorted(set(files)|{str((out/p).relative_to(ROOT)) for p in ['stage.paths.z','stage.paths.txt','manifesto.json']})
 (out/'stage.paths.z').write_bytes(b'\0'.join(p.encode() for p in stage)+b'\0');add(out/'stage.paths.z');(out/'stage.paths.txt').write_text('\n'.join(stage)+'\n');add(out/'stage.paths.txt')
 result=dict(normas=n,lista_normas=m['lista_normas'],mapeamento_fontes=m['mapeamento_fontes'],manifesto_origem=q.info(a.manifesto),replay=q.info(a.replay),CSS=q.info(a.css),baseline=m['baseline'],confronto=m['confronto'],arquivos=sorted(files.values(),key=lambda r:r['arquivo']),paths_stage=len(stage),limite='Mapa exato privado sem staging ou promoção; preservar o pacote original.')
 p=out/'manifesto.json';p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(manifesto=q.info(p),normas=n,artefatos=len(files),paths_stage=len(stage),bytes=sum(r['bytes'] for r in files.values()))))
if __name__=='__main__':main()
