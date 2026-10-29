import re,hashlib,html5lib,tinycss2,cssselect2
from identidade_decreto import extrair_epigrafe_decreto
sha=lambda b:hashlib.sha256(b).hexdigest()
special = re.compile('symbol|wingdings?|webdings?|dingbats?', re.I)
props = {'font-family', 'font', 'display', 'visibility', 'opacity', 'color', 'font-size', 'text-decoration', 'text-decoration-line', 'mso-hide'}

def declarations(content):
    out = []
    for d in tinycss2.parse_declaration_list(content, skip_comments=True, skip_whitespace=True):
        if d.type == 'declaration' and d.lower_name in props:
            out.append({'name': d.lower_name, 'value': tinycss2.serialize(d.value).strip(), 'important': bool(d.important)})
    return out

def danger(d):
    name = d['name']
    v = d['value'].lower()
    return bool(name in {'font', 'font-family'} and special.search(v) or (name in {'text-decoration', 'text-decoration-line'} and 'line-through' in v) or (name == 'display' and v == 'none') or (name == 'visibility' and v in {'hidden', 'collapse'}) or (name == 'opacity' and re.fullmatch('0+(?:\\.0+)?', v)) or (name == 'color' and ('transparent' in v or re.search('rgba\\([^)]*,\\s*0(?:\\.0*)?\\s*\\)', v))) or (name == 'font-size' and re.fullmatch('0+(?:\\.0+)?(?:px|pt|em|rem|%)?', v)) or (name == 'mso-hide' and v == 'all'))

def text_of(el):
    return ''.join(el.itertext()).strip()

def node_signature(el):
    return {'tag': el.tag, 'id': el.get('id'), 'class': el.get('class'), 'style': el.get('style'), 'face': el.get('face')}

def analyze(doc):
    tree = html5lib.parse(doc['source'], treebuilder='etree', namespaceHTMLElements=False)
    wrapper = cssselect2.ElementWrapper.from_html_root(tree)
    elements = list(wrapper.iter_subtree())
    body = next((e for e in elements if e.etree_element.tag == 'body'))
    parents = {e.etree_element: e.parent.etree_element if e.parent else None for e in elements}
    normroots = [e.etree_element for e in elements if 'texto-dou' in e.classes] if doc['lote'] == 'DOU' else [body.etree_element]
    if not normroots:
        normroots = [body.etree_element]
    normset = set()
    for root in normroots:
        normset.update(root.iter())
    for e in elements:
        if e.etree_element.tag == 'h1' and extrair_epigrafe_decreto(text_of(e.etree_element)):
            normset.update(e.etree_element.iter())
    admin_labels = [x['marcador'] for x in (doc['normalizacao'] or {}).get('paragrafos', [])]

    def scope(el, text):
        if any((text.strip() == s for s in admin_labels)):
            return 'administrativo_comprovado'
        return 'normativo' if el in normset else 'fora_da_area_normativa'
    matcher = cssselect2.Matcher()
    rules = []
    unsupported = []
    fontfaces = []
    order = 0

    def parse_rules(nodes, conditional=None):
        nonlocal order
        for rule in nodes:
            if rule.type == 'qualified-rule':
                decl = declarations(rule.content)
                if not decl:
                    continue
                selector = tinycss2.serialize(rule.prelude).strip()
                item = {'selector': selector, 'declarations': decl, 'conditional': conditional, 'matches_normative': 0, 'matches_other': 0, 'dangerous': any((danger(d) for d in decl))}
                rules.append(item)
                order += 1
                item['order'] = order
                try:
                    for compiled in cssselect2.compile_selector_list(selector):
                        matcher.add_selector(compiled, item)
                except Exception as exc:
                    if item['dangerous']:
                        unsupported.append({'selector': selector, 'declarations': decl, 'conditional': conditional, 'erro': str(exc)})
            elif rule.type == 'at-rule':
                name = rule.lower_at_keyword
                if name == 'font-face':
                    decl = declarations(rule.content or [])
                    fontfaces.extend((d for d in decl if d['name'] == 'font-family' and special.search(d['value'])))
                elif rule.content is not None and name in {'media', 'supports', 'layer', 'document'}:
                    parse_rules(tinycss2.parse_rule_list(rule.content, skip_comments=True, skip_whitespace=True), (conditional + ' / ' if conditional else '') + '@' + name + ' ' + tinycss2.serialize(rule.prelude))
    for e in elements:
        if e.etree_element.tag == 'style':
            parse_rules(tinycss2.parse_stylesheet(e.etree_element.text or '', skip_comments=True, skip_whitespace=True))
    styles = {}
    events = []
    conditional_matches = []
    inline_interesting = []
    pseudo = []
    for e in elements:
        el = e.etree_element
        parent = e.parent.etree_element if e.parent else None
        inherit = styles.get(parent, {})
        applied = {}

        def put(d, rank, origin):
            name = d['name']
            name = 'font-family' if name == 'font' else name
            if name not in applied or rank >= applied[name]['rank']:
                applied[name] = {'value': d['value'], 'rank': rank, 'origin': origin, 'property_original': d['name']}
        if el.get('face'):
            put({'name': 'font-family', 'value': el.get('face')}, (False, 0, 0, 0, 0, -1), {'presentational_face': el.get('face')})
        for specificity, matchorder, pseudoname, item in matcher.match(e):
            item['matches_normative' if el in normset else 'matches_other'] += 1
            if item['conditional'] or pseudoname:
                if item['dangerous'] and el in normset:
                    (pseudo if pseudoname else conditional_matches).append({'selector': item['selector'], 'pseudo': pseudoname, 'conditional': item['conditional'], 'declarations': item['declarations'], 'node': node_signature(el), 'texto_contextual': text_of(el)[:250]})
                continue
            for d in item['declarations']:
                put(d, (d['important'], 0, *specificity, item['order']), {'selector': item['selector'], 'declaration': d})
        for d in declarations(el.get('style', '')):
            put(d, (d['important'], 1, 0, 0, 0, 0), {'inline_style': el.get('style'), 'declaration': d})
            if danger(d):
                inline_interesting.append({'node': node_signature(el), 'declaration': d, 'escopo': scope(el, text_of(el)), 'texto_contextual': text_of(el)[:300]})
        computed = {}
        for name in ['font-family', 'font-size', 'color', 'visibility']:
            if name in applied:
                x = applied[name]
                computed[name] = inherit.get(name) if x['value'].lower() in {'inherit', 'unset'} else x
            else:
                computed[name] = inherit.get(name)
        for name in ['display', 'opacity', 'text-decoration', 'text-decoration-line', 'mso-hide']:
            computed[name] = applied.get(name)
        computed['ancestor_hidden'] = list(inherit.get('ancestor_hidden', []))
        computed['ancestor_strike'] = list(inherit.get('ancestor_strike', []))
        computed['s_del_ancestors'] = list(inherit.get('s_del_ancestors', []))
        if el.tag in {'s', 'del', 'strike'}:
            computed['s_del_ancestors'].append(node_signature(el))
        for name in ['display', 'opacity']:
            x = computed.get(name)
            if x and danger({'name': name, 'value': x['value']}):
                computed['ancestor_hidden'].append({'property': name, **x})
        if 'hidden' in el.attrib:
            computed['ancestor_hidden'].append({'property': 'hidden', 'value': el.get('hidden'), 'origin': node_signature(el)})
        for name in ['text-decoration', 'text-decoration-line']:
            x = computed.get(name)
            if x and 'line-through' in x['value'].lower():
                computed['ancestor_strike'].append({'property': name, **x})
        styles[el] = computed
        segments = [el.text or ''] + [child.tail or '' for child in el]
        if el.tag in {'script', 'style', 'head', 'title'}:
            continue
        for text in segments:
            if not text.strip():
                continue
            font = computed.get('font-family')
            hidden = list(computed['ancestor_hidden'])
            strike = list(computed['ancestor_strike'])
            tags = computed['s_del_ancestors']
            for name in ['visibility', 'color', 'font-size']:
                x = computed.get(name)
                if x and danger({'name': name, 'value': x['value']}):
                    hidden.append({'property': name, **x})
            fs = bool(font and special.search(font['value']))
            mso = computed.get('mso-hide')
            if not (fs or hidden or strike or tags or (mso and danger({'name': 'mso-hide', 'value': mso['value']}))):
                continue
            events.append({'escopo': scope(el, text), 'texto_literal': text, 'codepoints': ['U+%04X' % ord(c) for c in text.strip()[:24]], 'fonte_especial_aplicada_css': font if fs else None, 'ocultacao_css': hidden, 'tachado_css': strike, 'tags_s_del_strike': tags, 'mso_hide_nao_padronizado': mso, 'node': node_signature(el)})
    unused = [{'selector': r['selector'], 'declarations': r['declarations'], 'conditional': r['conditional'], 'matches_normative': r['matches_normative'], 'matches_other': r['matches_other']} for r in rules if r['dangerous'] and (not r['matches_normative'])]
    external = [el.etree_element.get('href') for el in elements if el.etree_element.tag == 'link' and 'stylesheet' in (el.etree_element.get('rel') or '').lower()]
    return {'path': doc['path'], 'lote': doc['lote'], 'sha256_candidato': doc['sha256_candidato'], 'sha256_HTML_primario': sha(doc['source_raw']), 'fonte_HTML': doc['source_url'], 'font_face_declarados_sem_provar_uso': fontfaces, 'regras_perigosas_sem_match_normativo': unused, 'seletores_nao_resolvidos': unsupported, 'regras_condicionais_com_match': conditional_matches, 'pseudo_elementos_com_match': pseudo, 'inline_interessantes': inline_interesting, 'eventos_texto_efetivo_DOM': events, 'stylesheets_externas_nao_consultadas': external}
