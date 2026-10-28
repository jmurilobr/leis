"""Variante privada: somente as duas aspas cuja fonte incorporada contradiz ToUnicode."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from preparar_reparo_alvorada4238_v2 import preparar as original, conferir_replay, BASE
from pypdf import PdfReader

def sha(data):return hashlib.sha256(data).hexdigest()

def cmap4(raw):
    u16=lambda p:struct.unpack_from('>H',raw,p)[0]
    u32=lambda p:struct.unpack_from('>I',raw,p)[0]
    tables={raw[p:p+4]:(u32(p+8),u32(p+12)) for p in range(12,12+16*u16(4),16)}
    base=tables[b'cmap'][0];results=[]
    for i in range(u16(base+2)):
        p=base+4+8*i;platform,encoding=u16(p),u16(p+2);sub=base+u32(p+4)
        if u16(sub)!=4 or platform not in (0,3):continue
        count=u16(sub+6)//2;ends=sub+14;starts=ends+2*count+2;deltas=starts+2*count;ranges=deltas+2*count;mapping={}
        for cp in (0x2013,0x2014,0x2015,0x2016,0x201C,0x201D):
            gid=0
            for n in range(count):
                if u16(starts+2*n)<=cp<=u16(ends+2*n):
                    delta=u16(deltas+2*n);offset=u16(ranges+2*n)
                    gid=(cp+delta)&65535 if not offset else u16(ranges+2*n+offset+2*(cp-u16(starts+2*n)))
                    if offset and gid:gid=(gid+delta)&65535
                    break
            mapping['U+%04X'%cp]=gid
        results.append(dict(platform=platform,encoding=encoding,mapeamento=mapping))
    return results

def preparar():
    old,native,proof=original();reader=PdfReader(BASE/'fonte-edicao-4260.pdf');page=reader.pages[28];font=page['/Resources']['/Font']['/F2'].get_object();desc=font['/DescendantFonts'][0].get_object()
    if str(font['/Encoding'])!='/Identity-H' or str(desc['/CIDToGIDMap'])!='/Identity':raise ValueError('Mapeamento CID/GID inesperado')
    unicode_map=font['/ToUnicode'].get_object().get_data()
    if not re.search(rb'<00B1>\s*<00B4>\s*<2013>',unicode_map):raise ValueError('ToUnicode divergente')
    raw=desc['/FontDescriptor']['/FontFile2'].get_object().get_data();maps=cmap4(raw)
    if not maps or any(m['mapeamento']['U+201C']!=179 or m['mapeamento']['U+201D']!=180 or m['mapeamento']['U+2015'] or m['mapeamento']['U+2016'] for m in maps):raise ValueError('Fonte nao comprova as aspas')
    events=[];current_font=None;matrix=None
    for args,op in page.get_contents().operations:
        if op==b'Tf':current_font=str(args[0])
        elif op==b'Tm':matrix=[float(x) for x in args]
        elif op in (b'Tj',b'TJ') and current_font=='/F2':
            for value in ([args[0]] if op==b'Tj' else args[0]):
                if not hasattr(value,'original_bytes'):continue
                data=value.original_bytes
                if data in (b'\x00\xb3',b'\x00\xb4') and matrix and abs(matrix[4]-88.704)<0.001:
                    events.append(dict(cid=int.from_bytes(data,'big'),matriz=matrix,hex=data.hex()))
    if [e['cid'] for e in events]!=[179,180] or abs(events[0]['matriz'][5]-250.85)>0.001 or abs(events[1]['matriz'][5]-240.53)>0.001:raise ValueError('Operadores nao correspondem a ementa propria')
    cut=old.split('\n---\n',1)[1].lstrip('\n').split('\n\n',1)[1];assert cut.endswith('\n');body=cut[:-1]
    if body.count('\u2015')!=1 or body.count('\u2016')!=1 or native.count('\u2015')!=1 or native.count('\u2016')!=1:raise ValueError('Mais sinais do que o caso autorizado')
    newbody=body.replace('\u2015','\u201c').replace('\u2016','\u201d');newnative=native.replace('\u2015','\u201c').replace('\u2016','\u201d');conferir_replay(newbody,newnative)
    prefix=old[:-len(cut)];prefix,count=re.subn(r'(?m)^sha256_texto: "[0-9a-f]{64}"$', 'sha256_texto: '+json.dumps(sha(newbody.encode())),prefix)
    if count!=1:raise ValueError('Hash do corpo ausente/ambiguo')
    candidate=prefix+newbody+'\n';changes=[dict(posicao=i,antes='U+%04X'%ord(a),depois='U+%04X'%ord(b)) for i,(a,b) in enumerate(zip(body,newbody)) if a!=b]
    if len(changes)!=2:raise ValueError('Alteracoes alem dos dois sinais')
    result=dict(sha256_original=sha(old.encode()),sha256_candidato=sha(candidate.encode()),sha256_pdf=proof['sha256_pdf'],sha256_fontfile2=sha(raw),sha256_tounicode=sha(unicode_map),fonte_recurso='/F2',cid_to_gid='/Identity',cmap_fonte=maps,operadores=events,alteracoes_corpo=changes,demais_grafias_inalteradas=True,replay_commonmark=True,limite='Variante isolada de dois sinais, comprovados pelo glyph e cmap da fonte incorporada. Preserva a transcricao textual anterior como evidencia e nao altera canonico.')
    return candidate,newnative,result

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--saida',type=Path,required=True);a=ap.parse_args();candidate,native,proof=preparar();a.saida.mkdir(exist_ok=False);(a.saida/'candidato.md').write_text(candidate);(a.saida/'nativo-glifos.txt').write_text(native);(a.saida/'prova.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(sha256_candidato=proof['sha256_candidato'],alteracoes=len(proof['alteracoes_corpo']))))
if __name__=='__main__':main()
