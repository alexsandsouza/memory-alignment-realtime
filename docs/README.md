# Site demonstrativo do projeto

Site estático, sem dependências externas em tempo de execução. Todo o conteúdo é servido pela pasta `docs/`.

## Publicação no GitHub Pages

No repositório, abra Settings → Pages. Em Build and deployment, escolha Deploy from a branch, branch `main` e pasta `/docs`, e salve. O arquivo `.nojekyll` desativa o processamento Jekyll.

A atualização do conteúdo de `docs/` na branch selecionada será publicada pelo GitHub Pages após a ativação.

## Interações

- Ilustração exata dos bytes de uma leitura que cruza a linha de 64 bytes.
- Gráfico de medianas por offset, com escolha de 4/8 bytes e leituras independentes/dependentes.
- Consulta às simulações já executadas por conjunto, fator e fração p. O site não roda um escalonador no navegador nem interpola o número de perdas.
- Artigo em PDF e DOCX, links para dados e cópia da referência.

## Dados

`assets/data.json` preserva as medianas agrupadas por offset, os fatores medidos e as 1.408 linhas da grade de simulação. As classes são diferentes das medianas de cada offset isolado. Atualize este arquivo e as cópias do artigo ao realizar uma nova campanha.

Os resultados nativos foram obtidos no notebook do autor. Não são benchmarks executados no navegador do visitante. A utilização apresentada no painel inclui o arredondamento ao tick de 0,01 ms. A fração p é hipotética.

## Autoria

Alexsand Farias de Souza e Wesley Vitorino Teixeira. PPGEE/UFAM. Disciplina de Sistemas de Tempo Real, Prof. Dr. Lucas Cordeiro.
