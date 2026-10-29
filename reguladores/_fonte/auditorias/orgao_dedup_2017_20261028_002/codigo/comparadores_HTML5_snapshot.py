BLOCK = {'address', 'article', 'aside', 'blockquote', 'br', 'caption', 'dd', 'div', 'dl', 'dt', 'fieldset', 'figcaption', 'figure', 'footer', 'form', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'header', 'hr', 'li', 'main', 'nav', 'ol', 'p', 'pre', 'section', 'table', 'tbody', 'td', 'tfoot', 'th', 'thead', 'tr', 'ul'}
SKIP = {'head', 'script', 'style', 'title'}

def tag(el):
    return el.tag.rsplit('}', 1)[-1].lower() if isinstance(el.tag, str) else ''

def visible(el):
    parts = []

    def walk(n):
        t = tag(n)
        if not t or t in SKIP:
            return
        if t in BLOCK:
            parts.append(' ')
        if n.text:
            parts.append(n.text)
        for child in n:
            walk(child)
            if child.tail:
                parts.append(child.tail)
        if t in BLOCK:
            parts.append(' ')
    walk(el)
    return ' '.join(''.join(parts).replace('\ufeff', '').split())

def ancestor(n, parents, wanted):
    n = parents.get(n)
    while n is not None:
        if tag(n) in wanted:
            return n
        n = parents.get(n)
    return None

def matrices(tree):
    parents = {child: parent for parent in tree.iter() for child in parent}
    out = []
    for ti, table in enumerate(tree.iter('table')):
        rows = [n for n in table.iter('tr') if ancestor(n, parents, {'table'}) is table]
        grid = {}
        records = []
        for y, row in enumerate(rows):
            x = 0
            cells = []
            for ci, cell in enumerate([n for n in row if tag(n) in {'td', 'th'}]):
                while (y, x) in grid:
                    x += 1
                rs_raw = cell.attrib.get('rowspan')
                cs_raw = cell.attrib.get('colspan')
                rs = int(rs_raw or '1')
                cs = int(cs_raw or '1')
                assert rs > 0 and cs > 0
                rec = {'tag': tag(cell), 'rowspan_literal': rs_raw, 'colspan_literal': cs_raw, 'rowspan': rs, 'colspan': cs, 'texto': visible(cell), 'linha': y, 'coluna': x}
                cells.append(rec)
                for yy in range(y, y + rs):
                    for xx in range(x, x + cs):
                        assert (yy, xx) not in grid
                        grid[yy, xx] = {'origem': [y, x], 'texto': rec['texto'], 'tag': rec['tag']}
                x += cs
            records.append({'grupo_HTML5': tag(parents[row]), 'celulas': cells})
        h = max((y for y, x in grid), default=-1) + 1
        w = max((x for y, x in grid), default=-1) + 1
        out.append({'tabela': ti, 'linhas': records, 'ocupacao_por_spans': [[grid.get((y, x)) for x in range(w)] for y in range(h)]})
    return out

def alpha(n):
    out = ''
    while n > 0:
        n, j = divmod(n - 1, 26)
        out = chr(65 + j) + out
    return out

def roman(n):
    out = ''
    for value, s in [(1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'), (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'), (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]:
        q, n = divmod(n, value)
        out += s * q
    return out

def lists(tree):
    parents = {child: parent for parent in tree.iter() for child in parent}
    tables = list(tree.iter('table'))
    out = []
    for node in tree.iter():
        if tag(node) not in {'ol', 'ul'}:
            continue
        kind = tag(node)
        typ = node.attrib.get('type')
        start = node.attrib.get('start')
        count = int(start or '1') if kind == 'ol' else None
        items = []
        for li in [n for n in node if tag(n) == 'li']:
            value = li.attrib.get('value')
            num = int(value) if value is not None else count
            marker = None
            if kind == 'ol':
                marker = alpha(num) if typ in ['A', 'a'] and num > 0 else roman(num) if typ in ['I', 'i'] and 0 < num < 4000 else str(num)
                if typ in ['a', 'i']:
                    marker = marker.lower()
                count = num + 1
            items.append({'value_literal': value, 'contador_HTML': num, 'marcador_intrinseco_sem_CSS': marker, 'texto': visible(li)})
        cell = ancestor(node, parents, {'td', 'th'})
        table = ancestor(node, parents, {'table'})
        out.append({'tag': kind, 'type_literal': typ, 'start_literal': start, 'tabela_ancestral': tables.index(table) if table is not None else None, 'celula_ancestral_texto': visible(cell) if cell is not None else None, 'itens': items})
    return out
