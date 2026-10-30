# Lotação do semiaberto na 4ª RAJ

Painel com a ocupação diária das unidades prisionais paulistas, a partir dos números publicados pela Secretaria da Administração Penitenciária (SAP-SP) na página [Unidades Prisionais](https://www1.sap.sp.gov.br/sp/unidades-prisionais/unidades-prisionais.html). O foco é o semiaberto da 4ª Região Administrativa Judiciária, mas a coleta cobre todas as unidades do Estado. O painel inclui um gerador de manifestação, que monta a peça com os números do dia. O gerador foi feito só para a 4ª RAJ: responde à decisão padrão do DEECRIM de Campinas e usa a lista de unidades que ela indica; não serve para outras regiões sem ser refeito.

Painel independente. Não é publicação oficial da SAP nem da Defensoria Pública.

## Como funciona

- **Coleta.** Todo dia, às 20h23 e às 10h23 (Brasília), o GitHub Actions baixa o arquivo `pop-pri.js` da SAP e lê a capacidade e a população de cada pavilhão listado em `data/catalogo.json`. Quando a SAP publica uma data nova, a coleta acrescenta uma linha por pavilhão em `data/historico.json` e guarda o arquivo original do dia em `data/bruto/`. Se a data não mudou, nada é alterado.
- **Publicação.** O site (`index.html`, `assets/`, `data/`) é publicado pelo GitHub Pages a cada coleta e a cada alteração no repositório.
- **Privacidade.** O que se digita no gerador de manifestação fica no navegador de quem usa; nada é enviado.

## Arquivos

| Caminho | Conteúdo |
|---|---|
| `data/catalogo.json` | Um registro por pavilhão: unidade, cidade, coordenadoria, regime, sexo, se é da 4ª RAJ e o nome das variáveis da SAP |
| `data/historico.json` | Capacidade (`c`) e população (`p`) de cada pavilhão (`i`) em cada data (`d`) |
| `data/bruto/` | Arquivo `pop-pri.js` publicado pela SAP em cada data registrada |
| `data/rede_2023.json` | Situação do semiaberto da 4ª RAJ em 27/10/2023, para comparação |
| `coleta/atualizar.py` | Script da coleta |

## Avisos

- Se a coleta falhar (site da SAP fora do ar ou formato alterado), o GitHub avisa por e-mail o dono do repositório.
- Se a SAP criar unidade ou pavilhão novo, o resumo da coleta avisa, e o catálogo precisa ser atualizado.
