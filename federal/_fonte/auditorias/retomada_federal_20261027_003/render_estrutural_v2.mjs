import fs from 'node:fs';
import {marked} from '/Users/joaodavisn/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/marked/lib/marked.esm.js';
const input=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const result=input.map(r=>{const listas=[];function walk(ts){for(const t of ts){if(t.type==='list'){if(t.ordered)listas.push({start:t.start,items:t.items.map(i=>({marker:i.raw.match(/^\s*(\d+)([.)])(?:\s+|$)/)?.slice(1),text:i.text}))});for(const i of t.items)walk(i.tokens);}else if(t.tokens)walk(t.tokens);}}walk(marked.lexer(r.markdown,{gfm:true,pedantic:false,breaks:false}));return {...r,html:marked.parse(r.markdown,{gfm:true,pedantic:false,breaks:false}),listas_ordenadas:listas};});
fs.writeFileSync(process.argv[3],JSON.stringify({motor:'marked',versao:'17.0.5',opcoes:{gfm:true,pedantic:false,breaks:false},registros:result}));
