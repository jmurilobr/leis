"""Replay histórico offline; nenhuma consulta HTTP ou escrita canônica."""
from pathlib import Path
import gzip,hashlib,json,sys
B=Path(__file__).resolve().parent;R=B.parents[3];sys.path.insert(0,str(B/'tentativa28/codigo'))
from converter_constituicao import converter,documento
sha=lambda raw:hashlib.sha256(raw).hexdigest()
meta=json.loads((R/'fonte/constituicao-compilado.json').read_bytes());raw20=(R/'fonte/constituicao-compilado.htm').read_bytes();assert sha(raw20)==meta['sha256']=='74144e44562b0f5985fb518cbb98b802536d459ed7838a8c381d544b0ea2af86'
raw27=gzip.decompress((B/'constituicao-compilado-20261027.htm.gz').read_bytes());receipt27=json.loads(gzip.decompress((B/'constituicao-consulta-20261027.json.gz').read_bytes()));assert sha(raw27)==receipt27['sha256']=='79c0e37327bd73faa58a690514cb8878ff3206c08e4fcf27f622e9d631151d99';assert len(raw27)==receipt27['bytes']==1507134
body20=converter(raw20.decode(meta['encoding']));body27=converter(raw27.decode(meta['encoding']));assert body20==body27 and len(body20)==693160 and sha(body20.encode())=='b9c9a2996ebb8a3e17bcd6423d060526f6324903bc3c4d4d94abfdb96172c818';assert (R/'constituicao.md').read_text()==documento(raw20,meta)
failed=json.loads((B/'tentativa28/recibo-http.json').read_bytes());assert failed['HTTP_status']==0 and failed['curl_exit']==56 and failed['corpo_recebido'] is None and failed['consultas_HTTP_solicitadas']==1 and failed['retries_configurados']==0;assert (B/'tentativa28/headers.http.txt').read_bytes()==b''
print(json.dumps({'corpos20_27_identicos':True,'sha256_corpo':sha(body20.encode()),'caracteres':len(body20),'canonico_reproduz_snapshot20':True,'raw27_reconstruido':False,'novo_HTML28_recebido':False,'HTTP_executado_no_replay':0,'escritas_canonicas':0,'vigencia_atual_certificada':False},ensure_ascii=False))
