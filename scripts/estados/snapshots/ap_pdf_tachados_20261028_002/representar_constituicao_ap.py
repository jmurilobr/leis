"""Proposta de marcação histórica, vinculada a um PDF e baseline AP específicos."""
import bisect,collections,hashlib,json,re,string
from markdown_it import MarkdownIt
from lxml import html
SHA=lambda b:hashlib.sha256(b).hexdigest()
PDF_SHA='653e0e3fd73f516ae936d7f27b8cbb09f1d7d91e70bc11f578b203ceda6e3777'
PREIMAGEM_SHA='0c7bca53a8d275515f4e1b00fe4dabefe36135fb491f0b314d860ecc25fce96f'
MODO='md-compilacao-pdf-com-historico-tachado-ap-v1'
PARSER=MarkdownIt('commonmark',{'html':True})

def arvore(body):return html.fromstring('<div>'+PARSER.render(body)+'</div>')
def visivel(body):return arvore(body).text_content()

def marcar(body,selected):
    if '<del' in body or '</del' in body:raise ValueError('baseline já contém del')
    selected=set(selected)
    if any(i<0 or i>=len(body) or body[i].isspace() for i in selected):raise ValueError('offset de caractere inválido')
    expanded=set(selected)
    for i in selected:
        if i and body[i-1]=='\\' and body[i] in string.punctuation:expanded.add(i-1)
    for m in re.finditer(r'\*\*[^*\n]+\*\*',body):
        visible={i for i in range(m.start()+2,m.end()-2) if not body[i].isspace()}
        if visible and visible<=selected:expanded.update(range(m.start(),m.end()))
    runs=[]
    for i in sorted(expanded):
        if runs and '\n' not in body[runs[-1][1]:i] and all(c.isspace() for c in body[runs[-1][1]:i]):runs[-1][1]=i+1
        else:runs.append([i,i+1])
    chunks=[];previous=0
    for left,right in runs:chunks.extend([body[previous:left],'<del>',body[left:right],'</del>']);previous=right
    chunks.append(body[previous:]);new=''.join(chunks)
    if new.replace('<del>','').replace('</del>','')!=body:raise ValueError('texto original alterado')
    old_text=visivel(body);tree=arvore(new)
    if tree.text_content()!=old_text:raise ValueError('renderização alterou caracteres/espaços')
    actual=''.join(ch for node in tree.iter('del') for ch in node.text_content() if not ch.isspace())
    expected=''.join(body[i] for i in sorted(selected))
    if actual!=expected:raise ValueError('escopo de del difere dos caracteres físicos selecionados')
    if any(list(node.iterancestors('del')) for node in tree.iter('del')):raise ValueError('del aninhado inesperado')
    return new,runs

def selecionar(preimagem,proof,receipt):
    if SHA(preimagem)!=PREIMAGEM_SHA or receipt['sha256_preimagem']!=PREIMAGEM_SHA or receipt['sha256_pdf']!=PDF_SHA:raise ValueError('fonte/baseline fora do perfil AP fixado')
    if len(proof)!=271 or receipt['totais'].get('retangulos_intersectantes')!=1508 or receipt['totais'].get('intersecoes_com_contexto_nao_resolvido',0):raise ValueError('inventário incompleto/ambíguo')
    body=preimagem.split(b'\n---\n',1)[1].decode();selected=set();source_map={};profiles=collections.Counter();pages=set()
    for page in proof:
        if page['rotacao']!=0:raise ValueError('página rotacionada fora do perfil')
        for rect in page['retangulos_intersectantes']:
            color=rect['cor'];height=round(rect['caixa'][3]-rect['caixa'][1],3)
            if color not in [0,0.0,[0.0,0.0,1.0]] or rect['tag'] not in ['P','Span'] or height not in [.36,.48,.6]:raise ValueError('perfil gráfico não revisado')
            if not rect['todos_glifos_nao_brancos_mapeados']:raise ValueError('glifo sem reconciliação literal')
            for glyph in rect['glifos']:
                if glyph['texto'].isspace():continue
                if glyph['matriz'][1]!=0 or glyph['matriz'][2]!=0:raise ValueError('matriz oblíqua fora do perfil')
                if not glyph.get('comparacao_literal'):raise ValueError('glifo sem prova literal')
                for ch in glyph['MD_caracteres']:
                    at=ch['MD_corpo_offset_unicode'];key=(page['pagina'],glyph['id'],ch['indice_no_glifo'])
                    if body[at]!=ch['caractere']:raise ValueError('caractere diverge da preimagem')
                    if key in source_map and source_map[key]!=at:raise ValueError('um caractere da fonte mapeado a dois destinos')
                    source_map[key]=at;selected.add(at)
                pages.add(page['pagina']);profiles[(str(color),rect['tag'],height,glyph['fonte'],round(glyph['tamanho'],3))]+=1
    markers=list(re.finditer(r'(?m)^EMENDAS CONSTITUCIONAIS[ \t]*$',body))
    if len(markers)!=1:raise ValueError('limite dos apêndices não único')
    boundary=markers[0].start()
    if any(i>=boundary for i in selected) or max(pages)!=144:raise ValueError('marcações fora do corpo principal comprovado')
    return body,selected,source_map,profiles,boundary

def material_nao_tachado(body,modo):
    if modo!=MODO:raise ValueError('modo de representação desconhecido')
    markers=list(re.finditer(r'(?m)^EMENDAS CONSTITUCIONAIS[ \t]*$',body))
    if len(markers)!=1:raise ValueError('limite histórico ausente/ambíguo')
    main=body[:markers[0].start()];tree=arvore(main)
    for node in list(tree.iter('del')):node.drop_tree()
    return tree.text_content()

def extrair_documento(blob):
    head,body=blob.split(b'\n---\n',1);meta={}
    for line in head.decode().splitlines()[1:]:
        if ': ' not in line:continue
        key,value=line.split(': ',1)
        try:meta[key]=json.loads(value)
        except json.JSONDecodeError:meta[key]=value
    if meta.get('representacao_corpo')!=MODO or meta.get('sha256_fonte')!=PDF_SHA:raise ValueError('modo/fonte fora do perfil explícito')
    if meta.get('sha256_corpo')!=SHA(body):raise ValueError('corpo alterado depois da proposta')
    text=body.decode();markers=list(re.finditer(r'(?m)^EMENDAS CONSTITUCIONAIS[ \t]*$',text))
    if len(markers)!=1:raise ValueError('limite de apêndices inválido')
    if SHA(text[markers[0].start():].encode())!=meta['partes_documento']['sha256_apendices']:raise ValueError('apêndices alterados')
    return material_nao_tachado(text,MODO)

def propor(preimagem,proof,receipt,capture,arquivo_local):
    body,selected,source_map,profiles,boundary=selecionar(preimagem,proof,receipt)
    annotated,runs=marcar(body,selected)
    old_appendix=body[boundary:];new_boundary=annotated.index('EMENDAS CONSTITUCIONAIS',boundary)
    if annotated[new_boundary:]!=old_appendix:raise ValueError('apêndices foram alterados')
    if capture.get('http')!=200 or capture.get('sha256_fonte')!=PDF_SHA or capture.get('igual_cache_preexistente') is not True:raise ValueError('recaptura não comprova bytes da fonte')
    stamp=capture['capturado_em']
    if not stamp.startswith('2026-10-28T') or not stamp.endswith('-03:00'):raise ValueError('captura real não corresponde ao recibo')
    header=preimagem.split(b'\n---\n',1)[0].decode();lines=header.splitlines();newlines=[]
    for line in lines:
        if line.startswith('versao_texto:'):line='versao_texto: '+json.dumps('Compilação oficial de 2025 até EC 71/2025; histórico tachado preservado, vigência posterior não certificada',ensure_ascii=False)
        if line.startswith('baixado_em:'):line='baixado_em: "2026-10-28"'
        newlines.append(line)
        if line.startswith('fonte:'):newlines.append('arquivo: '+json.dumps(capture['url_final'],ensure_ascii=False))
    extras=dict(representacao_corpo=MODO,sha256_fonte=PDF_SHA,sha256_corpo=SHA(annotated.encode()),arquivo_local=arquivo_local,edicao='Compilação oficial de 2025 atualizada até EC 71, de 17/06/2025. Textos riscados no PDF são preservados como histórico em del e excluídos pelo extrator explícito de material não tachado. Notas não riscadas ficam. Apêndices das 71 emendas permanecem integrais como documentação histórica; não são atos novos nem afirmação de vigência de suas redações. Nenhuma revogação integral ou vigência global em 2026 foi inferida.',captura_anterior_registrada='2026-10-13, data do coletor original; horário/recibo HTTP original indisponível',captura_pdf_comprovada_em=stamp,partes_documento=dict(compilacao_paginas=[1,146],apendices_historicos_paginas=[147,271],limite_apendices='EMENDAS CONSTITUCIONAIS',sha256_apendices=SHA(old_appendix.encode())))
    newlines.extend(k+': '+json.dumps(v,ensure_ascii=False) for k,v in extras.items());blob=('\n'.join(newlines)+'\n---\n'+annotated).encode()
    history=[];source_pairs=sorted((at,page) for (page,glyph,sub),at in source_map.items());source_offsets=[at for at,page in source_pairs]
    anchors=list(re.finditer(r'\*\*Art[.]?\s*\d+[^*]*\*\*',body,re.I));anchor_offsets=[m.start() for m in anchors]
    for left,right in runs:
        lo=bisect.bisect_left(source_offsets,left);hi=bisect.bisect_left(source_offsets,right);source_pages=sorted({page for at,page in source_pairs[lo:hi]})
        anchor_index=bisect.bisect_right(anchor_offsets,left)-1;anchor=anchors[anchor_index][0] if anchor_index>=0 else None
        history.append(dict(inicio_unicode=left,fim_unicode=right,paginas_pdf=source_pages,ancora_textual_anterior=anchor,markdown_historico=body[left:right],contexto_antes=body[max(0,left-120):left],contexto_depois=body[right:right+160]))
    return blob,dict(total_caracteres_nao_brancos_tachados=len(selected),total_glifos_codepoints_fonte=len(source_map),total_segmentos=len(runs),historico=history,perfis=[dict(cor=k[0],tag=k[1],altura=k[2],fonte=k[3],tamanho=k[4],caracteres=n) for k,n in profiles.items()],apendices_byte_identicos=True,sha256_apendices=SHA(old_appendix.encode()),texto_visivel_total_identico=True,preimagem_reconstituida_removendo_somente_del=True,material_nao_tachado=material_nao_tachado(annotated,MODO),limite='A extração não tachada reproduz o material da compilação fornecida, sem certificar vigência atual. Histórico e apêndices não são descartados. Zero normas novas.')
