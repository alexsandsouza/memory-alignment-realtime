# Artigo e reprodução da análise

O artigo atualizado está em DOCX editável e PDF. Inclui os dados de Linux nativo e a nova simulação, preservando a campanha WSL2 como comparação histórica em hardware diferente.

## Estrutura do pacote

- final/: artigo, figuras de simulação, tabelas e código.
- entrega/: análise estatística dos CSVs, fatores e figura dos benchmarks.
- analysis_input/: arquivos brutos recebidos, código C, logs e ambiente.

## Reprodução

Use Python 3 com pandas, matplotlib e python-docx. A partir da raiz extraída:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pandas matplotlib python-docx
python3 entrega/analisar_resultados.py
python3 final/codigo/executar_simulacao.py
python3 final/codigo/gerar_artigo.py
```

O primeiro script recalcula as estatísticas a partir dos dados brutos. O segundo importa a versão simulador3 fornecida, passa os oito fatores explicitamente, executa os testes e produz as tabelas. O terceiro gera o DOCX. Não executa os benchmarks C novamente. Para gerar o PDF, exporte o DOCX no Word ou LibreOffice.

Os fatores medidos não são WCET; p é fração hipotética do tempo-base. A tolerância da busca de p crítico é 0,002 (0,2 ponto percentual). O simulador usa tick de 0,01 ms e horizonte de um hiperperíodo. O CSV simulacao.csv distingue a utilização modelada e a efetiva após quantização.

O resumo de simulação usa oito cenários: mediana e razão agregada de p99 para cada largura e benchmark. A cadeia de 4 bytes e a de 8 bytes têm fatores próximos, mas os tempos absolutos refletem sessões diferentes. O código original foi preservado; a integração está no script executar_simulacao.py.

Os testes originais e 36 comparações independentes para RM, DM e EDF passaram. As novas simulações foram executadas no ambiente de análise, usando tempos medidos pelo autor no seu computador. Não são execuções reais das tarefas periódicas naquele notebook.
