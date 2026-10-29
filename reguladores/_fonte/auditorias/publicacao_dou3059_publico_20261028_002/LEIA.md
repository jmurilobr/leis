# Complemento portátil da seleção DOU 3.059

O envelope original permanece intacto. Execute `python3 -I reguladores/_fonte/auditorias/publicacao_dou3059_publico_20261028_002/verificar_publico.py`: confere SHA de todos os 3.182 artefatos e das cinco cópias públicas. As origens privadas são identificadores históricos; não são abertas. A correspondência completa está vinculada ao SHA do envelope e ao registro de cópias.

O replay real congelado foi executado por `replay_sem_privados.py`, que bloqueia open/io.open em qualquer caminho da raiz privada `_fonte` ou de `municipais` e bloqueia escrita em arquivos. Os pipes inteiros do subprocesso GFM são permitidos. Os cinco testes do bloqueio passaram. `replay-sem-privados-v2.log` reproduziu 3.059/3.059 com os dois motores e todos os gates originais, sem acessar essas raízes. As dependências Python de QA e Node devem estar instaladas no clone conforme o fluxo original; nenhuma biblioteca foi copiada neste complemento.

O primeiro log também é preservado: o wrapper inicial rejeitou o pipe FD 4 no subprocesso GFM, depois dos gates CommonMark, por uma restrição de instrumentação excessiva. Isso foi corrigido exclusivamente no wrapper novo antes deste congelamento. Nenhuma norma, fonte, comparador, exceção contextual ou código do replay original mudou.

Inclua os artefatos do manifesto e o próprio manifesto como controles adicionais ao mapa original. Não execute o antigo verificar.py num clone sem origens privadas; use verificar_publico.py. O replay original usa brutos MD/HTML dos gzips primários, bases de metadados reguladores/federal congeladas e helpers publicados. Não precisa de normas municipais ou caches individuais de fontes. Nenhum canônico, índice Git ou código global foi alterado.
