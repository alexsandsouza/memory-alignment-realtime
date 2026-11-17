from pathlib import Path
import csv, math, statistics as st, hashlib, json
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
SRC=ROOT.parent/'analysis_input'
def quant(v):
 s=sorted(v);p=(len(s)-1)*.99;a=math.floor(p);b=math.ceil(p);return s[a]+(s[b]-s[a])*(p-a)
rows=[];overview=[];allgroups={};total=0
for kind,prefix in [('Independentes','dados'),('Dependentes','cadeia')]:
 for b in (4,8):
  pooled=defaultdict(list); runks=[]; pq=defaultdict(list)
  for run in range(1,6):
   name=SRC/f'{prefix}{b}_run{run}.csv';groups=defaultdict(list);seen=set()
   with name.open() as f:
    reader=csv.DictReader(f)
    assert reader.fieldnames==['offset','rep','ns_por_acesso']
    for r in reader:
     o=int(r['offset']);rep=int(r['rep']);v=float(r['ns_por_acesso'])
     assert 0<=o<64 and 0<=rep<1000 and (o,rep) not in seen and math.isfinite(v) and v>0
     seen.add((o,rep));groups[o].append(v);pooled[o].append(v)
   assert len(seen)==64000;total+=len(seen)
   for o,v in groups.items():
    q=quant(v);pq[o].append(q)
    rows.append([kind,b,run,o,len(v),st.median(v),q,max(v)])
   no=[v for o,vs in groups.items() if o<65-b for v in vs];yes=[v for o,vs in groups.items() if o>=65-b for v in vs]
   runks.append(st.median(yes)/st.median(no))
  no=[v for o,vs in pooled.items() if o<65-b for v in vs];yes=[v for o,vs in pooled.items() if o>=65-b for v in vs]
  n=st.median(no);y=st.median(yes)
  pn=st.median([v for o,vs in pq.items() if o<65-b for v in vs]);py=st.median([v for o,vs in pq.items() if o>=65-b for v in vs])
  overview.append([kind,b,n,y,y/n,min(runks),max(runks),pn,py,py/pn,max(no),max(yes)])
  allgroups[kind,b]=pooled
with (ROOT/'estatisticas_completas.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['cenario','bytes','rodada','offset','n','mediana_ns','p99_ns','maximo_ns']);w.writerows(rows)
with (ROOT/'fatores_custo.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['cenario','bytes','mediana_nao_cruza','mediana_cruza','k','k_min_rodadas','k_max_rodadas','mediana_p99_nao_cruza','mediana_p99_cruza','k_p99','max_nao_cruza','max_cruza']);w.writerows(overview)
fig,axes=plt.subplots(2,2,figsize=(12,8))
for ax,((kind,b),groups) in zip(axes.flat,allgroups.items()):
 for run in range(1,6):
  rr={r[3]:r[5] for r in rows if r[0]==kind and r[1]==b and r[2]==run}
  ax.plot(range(64),[rr[o] for o in range(64)],alpha=.3,lw=.8)
 ax.plot(range(64),[st.median(groups[o]) for o in range(64)],color='#064b77',lw=2,label='Mediana agrupada')
 ax.axvline(65-b,color='#cf5b25',ls='--',label='Primeiro cruzamento')
 ax.set(title=f'{kind}, {b} bytes',xlabel='Deslocamento (bytes)',ylabel='ns/acesso (média por lote)');ax.grid(alpha=.2);ax.legend(fontsize=8)
fig.tight_layout();fig.savefig(ROOT/'medianas_deslocamento.png',dpi=180);fig.savefig(ROOT/'medianas_deslocamento.pdf');plt.close(fig)
lines=['# Resultados em Linux nativo - complemento ao artigo','', 'Alexsand Farias de Souza e Wesley Vitorino Teixeira | PPGEE/UFAM | Disciplina de Sistemas de Tempo Real, Prof. Dr. Lucas Cordeiro','', '## Integridade e método','',f'Foram validados 20 CSVs, totalizando {total:,} amostras. Cada arquivo contém exatamente os 64.000 pares únicos (offset, rep) esperados: 64 deslocamentos e 1.000 repetições. Todos os tempos são positivos e finitos. Os dados brutos foram preservados.','', 'A análise foi refeita a partir dos CSVs. Para manter comparabilidade com a Tabela III do artigo, a mediana de cada grupo usa todas as amostras dos deslocamentos que não cruzam ou cruzam a linha. k é a razão entre essas medianas. A faixa de k usa cinco razões calculadas separadamente por rodada. O p99 é calculado com interpolação linear por rodada e deslocamento, seguido da mediana desses percentis em cada grupo. A razão destes agregados é k p99; não corresponde ao p99 de todas as amostras agrupadas.','', '## Plataforma e protocolo','', 'Ubuntu 26.04 LTS, kernel 7.0.0-42-generic PREEMPT_DYNAMIC, Intel Core i5-8265U, quatro núcleos e oito processadores lógicos, L1d de 32 KiB por núcleo, linha de cache de 64 bytes, GCC 15.2.0. O diagnóstico retornou none para virtualização. O registro de ambiente documenta powersave apenas para CPU 0. A execução fixada na CPU lógica 2 está documentada nos comandos e capturas fornecidos, mas o governor da CPU 2 e a atividade do irmão SMT não foram registrados.','', 'Compilação informada: gcc -O2 -std=c11 -Wall -Wextra, com ACCESS_BYTES=8 para as variantes de oito bytes. Cada lote independente contém 51.200 leituras; cada lote dependente, 12.800 saltos. Os deslocamentos são embaralhados com semente fixa, repetindo a ordem entre rodadas. As coletas atravessam duas sessões em 16 e 17/11/2026; o diagnóstico de ambiente foi registrado em 16/11. Não se presume controle de frequência na segunda sessão.','', '## Resultados agrupados','', '| Cenário | Bytes | Não cruza (ns) | Cruza (ns) | k | Faixa de k entre rodadas | k p99 |','|---|---:|---:|---:|---:|---:|---:|']
for r in overview:lines.append(f'| {r[0]} | {r[1]} | {r[2]:.4f} | {r[3]:.4f} | {r[4]:.4f} | {r[5]:.4f} a {r[6]:.4f} | {r[9]:.4f} |')
lines+=['','![Medianas por deslocamento](medianas_deslocamento.png)','','As linhas finas representam as cinco medianas por rodada; a linha destacada representa a mediana das 5.000 amostras por deslocamento. O traço vertical indica 61 para quatro bytes e 57 para oito bytes.','','## Texto proposto para resultados e discussão','', 'Nas leituras dependentes, o cruzamento da linha de cache apresentou aumento consistente nos limiares previstos. A comparação pareada entre as medianas dos offsets 60 e 61 indicou aumento de 82,24% a 99,95% em quatro bytes; entre os offsets 56 e 57, de 90,67% a 105,13% em oito bytes. Esses percentuais locais não devem ser confundidos com os fatores agrupados da tabela, que utilizam todos os deslocamentos de cada classe.','', 'Nas leituras independentes de quatro bytes, a mudança entre os offsets 60 e 61 também foi consistente, porém de menor magnitude. Nas de oito bytes, não houve aumento consistente nessa fronteira. Portanto, a observação no Linux nativo não sustenta uma afirmação universal de penalidade para toda carga que cruza a linha. A dependência entre endereços e o código de máquina constituem condições relevantes de interpretação.','', 'A inspeção dos trechos enviados mostrou cargas escalares preservadas. Na variante independente de quatro bytes, carga e soma são instruções separadas; na de oito bytes, a soma usa operando de memória. Nas cadeias, o resultado carregado é reutilizado na formação do endereço seguinte. A ausência de chamadas a memcpy, isoladamente, não seria suficiente para essa validação. Os arquivos de assembly anexados cobrem somente os benchmarks independentes; a análise das cadeias se apoia nos trechos enviados na conversa.','', '## Comparação com a versão WSL2 do artigo','', 'O artigo original usa Intel Core i5-12450H sob WSL2, enquanto a reprodução nativa usa Intel Core i5-8265U. Trata-se de reprodução em outra plataforma, não de experimento controlado sobre virtualização. Não se pode atribuir diferenças de tempo ao WSL2 ou ao Linux nativo isoladamente. A coleta original independente de oito bytes usou ordem crescente; a nova usa ordem embaralhada fixa. A cadeia de oito bytes também amplia o conjunto experimental original.','', '## Limitações e alterações necessárias no artigo','', '- Os valores são médias por acesso dentro de lotes, incluindo cálculo de endereço, acumulação e controle de laço; não são latências isoladas de instruções nem WCET garantido.','- O buffer cabe na capacidade da L1, mas sem contadores de hardware não se confirma atendimento de todas as leituras na L1.','- Máximos e p99 podem refletir interferências, frequência e outros fatores; a origem de cada extremo não foi medida. Não atribuir causalmente os picos ao sistema operacional.','- Ordem fixa entre rodadas, ausência de frequência controlada e sessões separadas limitam inferência causal e comparação absoluta entre larguras.','- PREEMPT_DYNAMIC não comprova PREEMPT_RT. Afinidade em CPU lógica não isola núcleo, interrupções ou irmão SMT.','- Atualizar resumo, plataforma, protocolo, Tabela III, figura de deslocamentos, discussão e conclusão. Preservar os resultados WSL2 como campanha distinta. A conclusão atual de que o custo aparece somente ao cruzar a linha deve ser delimitada por cenário e plataforma.','- Não apresentar vazão e cadeia como limites matemáticos inferior e superior para programas arbitrários.','','## Escalonabilidade: etapa ainda pendente','', 'O modelo original C_i(p,k)=C_i[1+p(k-1)] pode ser mantido como hipótese de sensibilidade, com p definido como fração do tempo-base afetada. Os fatores desta campanha devem alimentar uma nova execução validada do simulador para os conjuntos A, B, C e D e políticas RM, DM, EDF e LLF. As tabelas de perdas e tempos de resposta da versão WSL2 não são resultados nativos e não foram recalculadas neste complemento.','', 'Para concluir essa etapa, é necessário o código atual do simulador e suas regras de horizonte, contagem de deadlines e desempate. O arquivo não veio neste pacote. Não extrapolar o dobro de tempo por salto para o dobro do tempo de toda tarefa.','','## Reprodutibilidade','', 'O pacote inclui estatísticas por rodada e deslocamento, fatores agrupados, figura PNG/PDF, script de análise e manifesto SHA-256 dos arquivos recebidos. O script procura os dados em ../analysis_input. Dependência gráfica: matplotlib. Nenhum benchmark foi executado no ambiente de análise; todas as medições foram realizadas no computador do autor.']
(ROOT/'Resultados_Linux_Nativo.md').write_text('\n'.join(lines),encoding='utf-8')
(ROOT/'manifesto_sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SRC.iterdir())},indent=2))
print('TOTAL',total)
for r in overview:print(r)
