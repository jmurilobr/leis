"""Reconhece token identifica sem substituir epígrafe por título cadastrado."""
import html,re
from html.parser import HTMLParser

class Epigrafes(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.parts=None;self.items=[]
    def handle_starttag(self,tag,attrs):
        if tag=='p':
            if self.parts is not None:raise ValueError('epígrafe p não fechada')
            if 'identifica' in re.split(r'[\t\n\f\r ]+', (dict(attrs).get('class') or '').strip('\t\n\f\r ')):self.parts=[]
    def handle_endtag(self,tag):
        if tag=='p' and self.parts is not None:self.items.append(''.join(self.parts).strip());self.parts=None
    def handle_data(self,data):
        if self.parts is not None:self.parts.append(data)

def epigrafe_tokens(source,fragmento,inicio_fragmento,fallback):
    p=Epigrafes();p.feed(fragmento);p.close()
    if p.parts is not None:raise ValueError('epígrafe própria não fechada')
    if not p.items:return fallback(source,fragmento,inicio_fragmento)
    if len(p.items)!=1:raise ValueError('epígrafes próprias múltiplas: '+str(len(p.items)))
    return p.items[0],'p com token identifica na lista de classes do campo texto-dou'
