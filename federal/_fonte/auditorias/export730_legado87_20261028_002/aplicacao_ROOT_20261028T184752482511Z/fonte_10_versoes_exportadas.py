"""Resolução explícita de caminhos lógicos; nunca usa global divergente."""
from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parent;ROOT=B.parents[3].resolve()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def mapa():return json.loads((B/'mapa_versoes.json').read_bytes())
def arquivo_logico(logical):
 p=Path(logical);assert not p.is_absolute()and'..'not in p.parts;key=p.as_posix();m=mapa();row=m['versoes_logicas'].get(key)
 if row:
  target=ROOT/row['path_exportado'];assert target.resolve()==target and target.resolve().is_relative_to(ROOT);assert sha(target.read_bytes())==row['sha256_original_esperado'];return target
 assert not key.startswith('scripts/'),'Código lógico sem export declarado'
 target=ROOT/p;assert target.resolve()==target and target.resolve().is_relative_to(ROOT);return target
def validar_export():
 m=mapa()
 for logical,row in m['versoes_logicas'].items():assert sha(arquivo_logico(logical).read_bytes())==row['sha256_original_esperado']
 for row in m['auxiliares']:assert sha((ROOT/row['path_exportado']).read_bytes())==row['sha256']
 for logical,digest in m['originais'].items():assert sha((B/('original_'+Path(logical).name)).read_bytes())==digest
 return m
