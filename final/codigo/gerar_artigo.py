from pathlib import Path
from docx import Document
from docx.shared import Inches,Pt,RGBColor,Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import pandas as pd
ROOT=Path(__file__).resolve().parent.parent
D=Document();sec=D.sections[0];sec.page_width=Cm(21);sec.page_height=Cm(29.7);sec.top_margin=Cm(1.6);sec.bottom_margin=Cm(1.6);sec.left_margin=Cm(1.8);sec.right_margin=Cm(1.8)
normal=D.styles['Normal'];normal.font.name='Arial';normal.font.size=Pt(10);normal.paragraph_format.space_after=Pt(6);normal.paragraph_format.line_spacing=1.08
for name in ['Heading 1','Heading 2']:
 s=D.styles[name];s.font.name='Arial';s.font.color.rgb=RGBColor.from_string('17324D');s.font.size=Pt(13 if name=='Heading 1' else 11);s.paragraph_format.space_before=Pt(9);s.paragraph_format.space_after=Pt(6)

for sty in D.styles:
 for border in list(sty.element.iter(qn('w:pBdr'))):border.getparent().remove(border)
D.styles['Title'].font.name='Arial';D.styles['Title'].font.size=Pt(19)
footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
D.core_properties.author='Alexsand Farias de Souza; Wesley Vitorino Teixeira';D.core_properties.title='Impacto dos Acessos Desalinhados à Memória no Tempo de Execução e na Escalonabilidade de Sistemas de Tempo Real'
def p(t):D.add_paragraph(t)
def h(t):D.add_heading(t,1)
def sub(t):D.add_heading(t,2)
def page():D.add_page_break()
def table(head,rows,widths=None):
 t=D.add_table(rows=1,cols=len(head));t.style='Light Shading Accent 1'
 for c,v in zip(t.rows[0].cells,head):c.text=str(v)
 pr=t.rows[0]._tr.get_or_add_trPr();repeat=OxmlElement('w:tblHeader');pr.append(repeat)
 for row in rows:
  for c,v in zip(t.add_row().cells,row):c.text=str(v)
 for row in t.rows:
  for c in row.cells:
   for para in c.paragraphs:
    para.paragraph_format.space_after=Pt(3);para.paragraph_format.space_before=Pt(3)
    for r in para.runs:r.font.size=Pt(8)
 return t
def fig(path,caption,width=6.6):
 D.add_picture(str(path),width=Inches(width));q=D.add_paragraph(caption);q.style='Caption';q.paragraph_format.space_after=Pt(5)
 for r in q.runs:r.font.size=Pt(8)
# 1
D.add_heading('Impacto dos Acessos Desalinhados à Memória no Tempo de Execução e na Escalonabilidade de Sistemas de Tempo Real',0)
q=D.add_paragraph('Alexsand Farias de Souza e Wesley Vitorino Teixeira');q.alignment=1
q=D.add_paragraph('Programa de Pós-Graduação em Engenharia Elétrica (PPGEE)\nUniversidade Federal do Amazonas (UFAM), Manaus, Brasil\nalexsand.farias@ufam.edu.br | wesley.vitorino@ufam.edu.br');q.alignment=1
q=D.add_paragraph('Sistemas de Tempo Real | Prof. Dr. Lucas Cordeiro');q.alignment=1
h('Resumo')
p('Este artigo investiga o custo de leituras desalinhadas e seus efeitos sobre a escalonabilidade de tarefas periódicas. A campanha inicial em Intel Core i5-12450H sob WSL2 é complementada por uma reprodução em Intel Core i5-8265U com Linux nativo. Dois benchmarks em C utilizam leituras independentes e cadeias de leituras dependentes, com larguras de 4 e 8 bytes. A campanha nativa reúne 20 coletas e 1.280.000 amostras. Comparando todos os deslocamentos com e sem cruzamento de linha de cache, o fator mediano de custo é 1,0526 em leituras independentes de 4 bytes e 0,9974 em 8 bytes; nas cadeias, os fatores são 1,9989 e 1,9992, respectivamente. Os fatores alimentam um modelo de sensibilidade e simulações de RM, DM, EDF e LLF. Com os fatores nativos de leituras independentes, nenhum dos quatro conjuntos sintéticos perde prazos até p = 100%. Nas cadeias, as primeiras perdas ocorrem entre aproximadamente 7% e 43%. Os resultados são observações e projeções de um modelo, não garantias de WCET. A comparação entre campanhas não isola o efeito da virtualização, pois processador e protocolo também diferem.')
p('Palavras-chave: acessos desalinhados; linha de cache; tempo de execução; escalonabilidade; RM; DM; EDF; LLF; WCET.')
h('I. Introdução e objetivos')
p('Em sistemas de tempo real, o atendimento dos prazos depende tanto da correção funcional quanto da previsibilidade do tempo de execução [1]. A hierarquia de memória pode contribuir de modo relevante para esse tempo [2]. Um acesso é desalinhado em relação a um tipo quando seu endereço não é múltiplo do alinhamento natural correspondente. Isso é diferente de cruzar a fronteira de uma linha de cache: um acesso desalinhado pode permanecer inteiramente dentro da linha.')
p('A questão investigada é como o custo observado dessas leituras altera, sob um modelo explícito, a utilização, os tempos de resposta e as perdas de prazo de tarefas periódicas. Os objetivos são implementar benchmarks sem acesso tipado desalinhado, caracterizar as plataformas, comparar distribuições e máximos, simular quatro políticas e discutir o alcance das conclusões. A reprodução nativa amplia a evidência experimental e acrescenta a cadeia dependente de 8 bytes.')
#2
page();h('II. Trabalhos relacionados')
p('A literatura considerada na versão inicial organiza-se em quatro eixos. Trabalhos sobre pWCET e análise probabilística baseada em medições discutem quais garantias podem ser extraídas de observações [3], [4]; a análise exata exige hipóteses e métodos próprios [5]. No eixo microarquitetural, há estudos sobre modelagem do processador, caches de dados e instruções e interferência em caches compartilhados [2], [6]-[10].')
p('A contenção em memória compartilhada e a caracterização dos acessos são tratadas por modelos de interferência, mecanismos de isolamento e extração de perfis [11]-[14]. Outros estudos abordam latência em aplicações de fluxo, alocação de memória orientada a WCET e exploração dinâmica de comportamentos temporais [15]-[17]. Este trabalho concentra-se em um microbenchmark controlado e em projeções de escalonamento; não substitui os métodos de garantia temporal desses estudos.')
h('III. Plataformas e campanhas experimentais')
table(['Item','Campanha inicial (WSL2)','Reprodução nativa'],[
['Processador','Intel Core i5-12450H','Intel Core i5-8265U'],['Topologia apresentada','12 CPUs virtuais, segundo o artigo inicial','4 núcleos, 8 CPUs lógicas'],['Sistema/kernel','WSL2; Linux 6.6.114.1','Ubuntu 26.04 LTS; 7.0.0-42-generic'],['Linha de cache','64 bytes','64 bytes'],['Cache L1d','48 KiB, conforme artigo inicial','32 KiB por núcleo'],['Compilador','GCC 15.2.0','GCC 15.2.0'],['Otimização','-O2 -std=c11 -Wall -Wextra','Mesmas opções'],['Frequência','Governor não disponível no registro WSL2','powersave registrado na CPU 0'],['Data','31/10/2026, conforme artigo inicial','16 e 17/11/2026']])
p('Tabela I. Caracterização das duas campanhas. As informações WSL2 são provenientes do artigo inicial; os arquivos brutos recebidos nesta reprodução correspondem somente ao Linux nativo.')
p('O diagnóstico nativo retornou none para detecção de virtualização e mostrou afinidade disponível nas CPUs lógicas 0 a 7. Os comandos de coleta fixaram a execução na CPU lógica 2. Isso não isola o núcleo físico de interrupções, de tarefas do sistema ou da outra thread SMT. Não há registro do governor da CPU 2, nem evidência de frequência fixa. PREEMPT_DYNAMIC identifica a configuração apresentada pelo kernel, mas não comprova uso de PREEMPT_RT.')
p('O processador mudou entre as campanhas. Portanto, os tempos absolutos não constituem um teste A/B de WSL2 versus Linux nativo. A cadeia nativa de 8 bytes foi executada na sessão de 17/11; as demais coletas foram apresentadas na sessão anterior. Sem telemetria de frequência e temperatura, diferenças absolutas entre larguras não podem ser atribuídas apenas à largura do acesso.')
#3
page();h('IV. Metodologia')
sub('A. Benchmarks e protocolo de medição')
p('Os programas alocam 256 linhas de 64 bytes, mais 64 bytes de folga, com alinhamento de 64 bytes. A área nominal de 16 KiB cabe na capacidade de L1d da plataforma. Isso não demonstra, por si só, que cada leitura seja atendida pela L1. As cargas de 4 ou 8 bytes são efetuadas por memcpy de tamanho fixo, evitando conversões para ponteiros de tipos com alinhamento incompatível. A folga mantém dentro da alocação os acessos ao final da última linha.')
p('No benchmark independente, cada amostra agrega 200 passadas de 256 leituras, após 50 passadas de aquecimento. Na cadeia, cada posição guarda o índice seguinte de um ciclo que visita as 256 posições; cada amostra agrega 50 percursos, após 20 percursos de aquecimento. O endereço seguinte depende do valor carregado anteriormente. O tempo é obtido com CLOCK_MONOTONIC_RAW e dividido, respectivamente, por 51.200 e 12.800 acessos. Inclui controle de laço, cálculo de endereço e, na variante independente, acumulação.')
p('Cada combinação de benchmark e largura possui cinco rodadas de 1.000 amostras por deslocamento, de 0 a 63. Foram validados os 64.000 pares únicos (offset, repetição) em cada CSV, sem valores não finitos ou não positivos. Os deslocamentos usam ordem embaralhada de semente fixa; a sequência se repete entre rodadas. A campanha inicial independente de 8 bytes, segundo o artigo original, usava ordem crescente.')
sub('B. Critério de cruzamento e estatísticas')
p('Para largura s e deslocamento o, o acesso cruza a linha se o + s > 64. Os primeiros offsets que cruzam são 61 para 4 bytes e 57 para 8 bytes. Calcula-se k = mediana(cruza) / mediana(não cruza), agrupando todas as amostras de cada classe. A faixa entre rodadas usa cinco razões calculadas separadamente. O indicador de cauda calcula p99 por par rodada-offset e toma a mediana desses percentis dentro de cada classe; k p99 é a razão entre esses agregados.')
sub('C. Modelo de custo e tarefas sintéticas')
p('O modelo de sensibilidade é C_i(p,k) = C_i × [1 + p × (k - 1)]. C_i representa o custo-base da tarefa, p a fração desse tempo-base atribuída aos acessos afetados e k o fator empírico. p não foi medido em programas reais. O modelo não afirma que dobrar o tempo por salto dobre o tempo da tarefa inteira.')
table(['Conjunto','Tarefas (C, T, D), em ms','U-base','H'],[
['A: harmônico','(2,10,10); (4,20,20); (8,40,40); (8,80,80)','0,7000','80 ms'],['B: não harmônico','(2,10,10); (3,14,14); (5,35,35); (8,50,50)','0,7171','350 ms'],['C: prazos restritos','(4,10,10); (2,20,16); (4,30,15); (1,40,24)','0,6583','120 ms'],['D: carga alta','(3,10,10); (4,15,15); (5,35,35); (9,60,60)','0,8595','420 ms']])
p('Tabela II. Quatro conjuntos utilizados tanto na versão inicial quanto na reprodução da simulação.')
#4
page();h('V. Resultados experimentais no Linux nativo')
f=pd.read_csv(ROOT.parent/'entrega/fatores_custo.csv')
table(['Cenário','B','Não cruza\nns','Cruza\nns','k','Faixa k\npor rodada','k p99'],[[r.cenario,int(r.bytes),f'{r.mediana_nao_cruza:.4f}',f'{r.mediana_cruza:.4f}',f'{r.k:.4f}',f'{r.k_min_rodadas:.4f}-{r.k_max_rodadas:.4f}',f'{r.k_p99:.4f}'] for _,r in f.iterrows()])
p('Tabela III. Medianas agrupadas, fatores de custo e faixa entre as cinco rodadas. Os valores representam ns por acesso normalizados por lote.')
fig(ROOT.parent/'entrega/medianas_deslocamento.png','Figura 1. Medianas por deslocamento. Linhas finas: medianas por rodada; linha destacada: mediana agrupada. Linhas tracejadas: primeiro cruzamento previsto.',6.4)
p('Nas cadeias, os fatores agrupados se aproximam de 2 nas duas larguras. A comparação local de offsets 60→61, em 4 bytes, cresce de 82,24% a 99,95% nas cinco rodadas; para 56→57, em 8 bytes, cresce de 90,67% a 105,13%. Esses percentuais locais não são os fatores agrupados da Tabela III.')
p('Nas leituras independentes de 4 bytes, o efeito agrupado é de aproximadamente 5,26%. Em 8 bytes, k = 0,9974 e a faixa entre rodadas inclui valores abaixo e acima de 1; não há penalidade consistente demonstrada nesse cenário. Isso não constitui evidência de ganho causal ao cruzar a linha.')
#5
page();h('VI. Inspeção do executável e interpretação')
p('Os trechos de assembly inspecionados confirmam cargas escalares no intervalo medido. No independente de 4 bytes, a carga mov (%rax),%edi é seguida de soma; na versão de 8 bytes, add (%rax),%rsi combina soma com operando de memória. Em ambos, o ponteiro avança 64 bytes e o contador externo preserva as 200 passadas entre as chamadas ao relógio. As instruções vetoriais de inicialização ocorrem fora do intervalo medido.')
p('Na cadeia, o índice carregado em ebx ou rbx é reutilizado na formação do próximo endereço, com multiplicação por 64, soma da base e do offset. O contador interno executa 256 saltos e o externo 50 percursos. O sink final pode ser zero porque um percurso completo retorna ao início; esse valor não provaria, isoladamente, a execução das cargas. A inspeção do laço fornece a evidência complementar.')
p('O contraste entre acessos independentes e dependentes é compatível com maior exposição do atraso de cruzamento quando há dependência de endereço. Entretanto, diferenças absolutas entre 4 e 8 bytes também envolvem instruções geradas e sessões distintas. Não se atribui causalmente toda diferença à largura ou a um único mecanismo microarquitetural sem contadores adicionais.')
table(['Cenário','B','Máximo não cruza','Máximo cruza'],[[r.cenario,int(r.bytes),f'{r.max_nao_cruza:.4f}',f'{r.max_cruza:.4f}'] for _,r in f.iterrows()])
p('Tabela IV. Máximos observados, em ns/acesso normalizado por lote. Na cadeia de 4 bytes, o máximo de 241,6436 ocorre na classe sem cruzamento. A origem desses extremos não foi identificada pelas medições disponíveis.')
sub('Comparação com a campanha inicial')
p('No WSL2, o artigo inicial relata k = 1,214 para independentes de 4 bytes, 1,200 para independentes de 8 bytes e 1,999 para a cadeia de 4 bytes. Na reprodução nativa, o efeito das cadeias permanece próximo de 2, mas o efeito independente é menor em 4 bytes e não consistente em 8 bytes. Essa diferença amplia a conclusão: o desalinhamento não impõe uma penalidade universal; importa a relação com a linha, a dependência entre acessos e a plataforma.')
p('A campanha inicial é mantida como evidência histórica distinta, e não como controle experimental direto. O buffer cabe na L1d em capacidade, porém não se dispõe de contadores de misses, ciclos ou frequência. Os máximos não são atribuídos automaticamente a WSL2, Linux ou interrupções específicas.')
#6
page();h('VII. Simulação de escalonabilidade')
p('O núcleo de escalonamento é idêntico nos dois scripts recebidos. A versão simulador3 amplia a descoberta dos CSVs de 8 bytes e acrescenta funções exploratórias para coletas estendidas; esses cenários estendidos não foram executados porque não há dados correspondentes nesta campanha. Os fatores nativos foram fornecidos explicitamente, sem recorrer aos padrões WSL2 embutidos e sem arredondamento prévio para três casas.')
p('O simulador considera um processador, preempção, liberações síncronas em t = 0, D ≤ T e horizonte de um hiperperíodo. Custos são arredondados para cima em ticks de 0,01 ms. RM prioriza menor período; DM, menor prazo relativo; EDF, menor prazo absoluto; LLF, menor folga, preservando o job atual nos empates de folga. Jobs atrasados continuam executando. Jobs incompletos ao final são contados como perdas, pois seus deadlines são menores ou iguais ao horizonte. Não há custo de troca de contexto.')
p('Passaram os testes originais: exemplo que distingue RM/DM de EDF/LLF, comparação com RTA nos casos escalonáveis e checagens de utilização com D = T. Adicionalmente, 36 casos de RM, DM e EDF foram comparados com uma implementação independente passo a passo, com concordância nas perdas e respostas máximas. A análise reúne 1.408 combinações da grade: quatro conjuntos, oito fatores (mediana e p99 em quatro cenários), onze valores de p e quatro políticas.')
crit=pd.read_csv(ROOT/'tabelas/p_critico.csv',keep_default_na=False)
rows=[]
for _,r in crit.iterrows():
 rows.append([r.conjunto[0],r.politica,'-',r['latencia 4B'],r['latencia 8B'],r['latencia 4B p99'],r['latencia 8B p99']])
table(['Conj.','Política','Vazão\n4/8 B','Cadeia\n4 B','Cadeia\n8 B','Cadeia\n4 B p99','Cadeia\n8 B p99'],rows)
p('Tabela V. p crítico em %: primeira perda detectada por bisseção no horizonte simulado. Traço: nenhuma perda até 100%. Tolerância da bisseção: 0,002 em p (0,2 ponto percentual); valores apresentados com uma casa decimal não implicam resolução de 0,1 ponto percentual.')
p('Todos os fatores independentes, inclusive os de p99, mantiveram os quatro conjuntos sem perdas até p = 100%. Nas cadeias por mediana, os limiares apresentados coincidem nas duas larguras: RM perde a partir de cerca de 7% no conjunto C, e as quatro políticas atingem cerca de 43% no conjunto A. No conjunto C, DM suporta mais aumento de custo que RM, enquanto EDF e LLF suportam mais que as prioridades fixas no horizonte avaliado.')
#7
page();h('VIII. Perdas de prazo e sobrecarga')
fig(ROOT/'figuras/perdas_4bytes.png','Figura 2. Percentual de jobs que perdem prazo no horizonte de um hiperperíodo. Fatores nativos de 4 bytes; grade de p em passos de 10 pontos percentuais.',6.3)
p('A utilização modelada é U(p,k) = Σ C_i(p,k)/T_i; a utilização efetivamente simulada inclui o arredondamento dos custos ao tick. Para D = T, a fronteira ideal U = 1 fornece uma referência para interpretar EDF e LLF; a grade temporal e a tolerância da busca explicam pequenas diferenças numéricas. Para D < T, utilização inferior a 1 não basta para assegurar os prazos.')
p('Em sobrecarga, a porcentagem de jobs perdidos depende da política e da regra de continuar executando jobs atrasados. No conjunto D, com cadeia de 4 bytes e p = 50%, a utilização efetiva é 1,2893; RM e DM perdem 21,35% dos jobs, EDF 89,89% e LLF 91,01%. Esses percentuais caracterizam este horizonte e esta política de backlog, não uma superioridade geral de RM em sobrecarga.')
#8
page();h('IX. Tempos de resposta')
resp=pd.read_csv(ROOT/'tabelas/respostas.csv')
fig(ROOT/'figuras/respostas_latencia4.png','Figura 3. Maior resposta observada dividida pelo deadline, com p = 25% e fator da cadeia de 4 bytes. Barras truncadas acima de 3 são marcadas com ^; tarefas incompletas têm apenas limites inferiores de resposta.',6.4)
p('No conjunto C, com p = 25%, a utilização efetiva é aproximadamente 0,823. RM perde o prazo de t3, cuja resposta máxima é 17,50 ms para D = 15 ms; DM perde o prazo de t2, com 17,50 ms para D = 16 ms. EDF e LLF não perdem prazos nesse cenário. A escolha da política altera qual tarefa é afetada primeiro.')
selected=resp[(resp.cenario=='latencia 4B')&(resp.p==.25)&resp.conjunto.str.startswith('C')]
rr=[]
for t in ['t1','t2','t3','t4']:
 g=selected[selected.tarefa==t];rr.append([t,g.iloc[0].D_ms]+[f'{g[g.politica==pol].iloc[0].R_max_ms:.2f}' for pol in ['RM','DM','EDF','LLF']])
table(['Tarefa','D (ms)','RM','DM','EDF','LLF'],rr)
p('Tabela VI. Respostas máximas simuladas no conjunto C, cadeia de 4 bytes e p = 25%, em ms. Todas essas tarefas concluíram seus jobs dentro do horizonte, ainda que alguns tenham ultrapassado o prazo.')
p('No conjunto D com os mesmos p e k, a utilização efetiva é aproximadamente 1,074. RM e DM protegem t1 a t3 e acumulam atraso em t4; o valor 237,50 ms para t4 é limite inferior porque há jobs incompletos. EDF e LLF espalham atrasos, e as respostas indicadas no CSV com resp_ge=True também são limites inferiores, não valores finais exatos.')
p('LLF pode introduzir muitas preempções. No conjunto D, cadeia de 4 bytes e p = 50%, foram contadas 15.499 preempções em LLF, contra 39 em RM/DM e zero em EDF. Como trocas de contexto não têm custo, a simulação não estima o impacto real dessa atividade sobre o processador.')
#9
page();h('X. Discussão e ameaças à validade')
sub('A. Validade experimental')
p('A campanha mede um conjunto restrito de leituras em um notebook. Escritas, acesso atômico, buffers maiores, pressão de cache e travessia de páginas de 4 KiB não são avaliados. Cabe distinguir cruzamento de linha de desalinhamento natural: a classe sem cruzamento reúne endereços naturalmente alinhados e desalinhados contidos na linha.')
p('As cinco rodadas não eliminam dependência temporal ou perturbações recorrentes. O embaralhamento com semente fixa repete a posição temporal de cada offset, dificultando separar efeito de endereço de perturbações em momentos específicos. Frequência, temperatura, SMT, interrupções e governor da CPU de execução não foram controlados ou registrados continuamente. Não se atribui causa específica aos outliers.')
p('Os fatores de custo são razões de estatísticas empíricas. O k p99 é uma razão entre medianas de percentis por deslocamento, não um limite probabilístico de custo nem pWCET. O maior tempo observado também não é um limite superior garantido. As amostras contêm médias por lote e não tempos individuais de cada acesso.')
sub('B. Validade da projeção sobre tarefas')
p('p é uma variável de sensibilidade, não uma fração medida em tarefas reais. As duas formas de acesso são cenários distintos, e não limites inferior e superior matematicamente garantidos para programas arbitrários. Um fator menor que 1, como na leitura independente de 8 bytes, foi preservado numericamente na simulação, sem interpretá-lo como otimização comprovada.')
p('Os conjuntos são sintéticos; o escalonador usa um processador e um hiperperíodo, sem custo de preempção. A quantização de 0,01 ms afeta a utilização efetiva e os limiares. A bisseção retorna uma aproximação da primeira perda no modelo; a tabela não certifica um sistema real. Os testes de validação reduzem risco de erro de implementação, mas não eliminam as limitações das hipóteses.')
h('XI. Conclusão')
p('A reprodução nativa confirmou que o cruzamento de linha pode tornar as cadeias dependentes aproximadamente duas vezes mais lentas por salto, nas duas larguras investigadas. Nas leituras independentes, o efeito foi menor em 4 bytes e não consistente em 8 bytes. Portanto, o custo observado depende da estrutura de dependências, do código gerado e da plataforma, e não apenas do desalinhamento natural.')
p('No modelo de sensibilidade, os fatores independentes nativos não causaram perdas nos quatro conjuntos até p = 100%; os fatores das cadeias levaram às primeiras perdas entre cerca de 7% e 43%. A ordem dos prazos e a política de escalonamento influenciaram as margens e as tarefas afetadas. O Linux nativo amplia a evidência da versão WSL2, porém não isola o efeito da virtualização. Como continuidade, propõem-se sementes distintas, controle e registro de frequência, comparação no mesmo hardware, medição de p em programas reais e inclusão de custos de preempção.')
# refs
page();h('Referências')
refs=[
'[1] J. Engblom, A. Ermedahl, M. Sjödin, J. Gustafsson e H. Hansson. Worst-case execution-time analysis for embedded real-time systems. International Journal on Software Tools for Technology Transfer, 4(4), 437-455, 2003.',
'[2] J. Segarra, R. Gran Tejero e V. Viñals. A generic framework to integrate data caches in the WCET analysis of real-time systems. Journal of Systems Architecture, 120, 102304, 2021.',
'[3] S. Bozhko, F. Marković, G. von der Brüggen e B. B. Brandenburg. What really is pWCET? A rigorous axiomatic proposal. IEEE RTSS, 2023. DOI: 10.1109/RTSS59052.2023.00012.',
'[4] T. N. C. Andrade, G. Lima e V. M. C. Lima. Drawing lines for measurement-based probabilistic timing analysis. IEEE RTSS, 2024. DOI: 10.1109/RTSS62706.2024.00029.',
'[5] D. Arnström, D. Broman e D. Axehill. Exact worst-case execution-time analysis for implicit model predictive control. arXiv:2304.11576, 2023.',
'[6] M. Li, K. Xiao, Y. Zhou e D. Huang. WCET analysis based on micro-architecture modeling for embedded system security. Applied Sciences, 14(16), 7277, 2024. DOI: 10.3390/app14167277.',
'[7] V. Touzeau e J. Reineke. Leveraging LLVM’s ScalarEvolution for symbolic data cache analysis. IEEE RTSS, 2023.',
'[8] A. Pedro-Zapater, J. Segarra, R. Gran Tejero, V. Viñals e C. Rodríguez. Reducing the WCET and analysis time of systems with simple lockable instruction caches. PLoS ONE, 15(3), e0229980, 2020. DOI: 10.1371/journal.pone.0229980.',
'[9] W. Zhang, M. Lv, W. Chang e L. Ju. Precise and scalable shared cache contention analysis for WCET estimation. ACM/IEEE DAC, 2022. DOI: 10.1145/3489517.3530613.',
'[10] S. Zhao et al. Tight cache contention analysis for WCET estimation on multicore systems. IEEE RTSS, 2025. DOI: 10.1109/RTSS66672.2025.00046.',
'[11] D. Dasari, V. Nelis e B. Akesson. A framework for memory contention analysis in multi-core platforms. Real-Time Systems, 52(3), 272-322, 2016. DOI: 10.1007/s11241-015-9229-9.',
'[12] G. Farina, G. Gala, M. Cinque e G. Fohler. Enabling memory access isolation in real-time cloud systems using Intel’s detection/regulation capabilities. Journal of Systems Architecture, 137, 102848, 2023.',
'[13] H. Chabot, I. Puaut, T. Carle e H. Cassé. Marmot: Extraction of fine-grain memory access profiles for real-time software. RTNS, 2024. DOI: 10.1145/3696355.3696360.',
'[14] T. Degioanni e I. Puaut. StAMP: Static analysis of memory access profiles for real-time tasks. WCET, 2022. DOI: 10.4230/OASIcs.WCET.2022.1.',
'[15] A. M. Abotaleb e M. Hassan. The case for HW/SW harmony in real-time systems: Tightening memory latency of streaming applications. ACM Transactions on Embedded Computing Systems, 24(5s), art. 151, 2025. DOI: 10.1145/3762647.',
'[16] S. Jadhav e H. Falk. Approximating WCET and energy consumption for fast multi-objective memory allocation. RTNS, 2022. DOI: 10.1145/3534879.3534889.',
'[17] A. Berger, S. Schuster, P. Wagemann e P. Ulbrich. Dynamic fuzzing-based whole-system timing analysis. IEEE RTSS, 2025. DOI: 10.1109/RTSS66672.2025.00041.'
]
for ref in refs:
 q=D.add_paragraph(ref);q.paragraph_format.space_after=Pt(5)
 for r in q.runs:r.font.size=Pt(8.5)
# Disable splitting rows and add alt text for figures.
for t in D.tables:
 for row in t.rows:
  pr=row._tr.get_or_add_trPr();el=OxmlElement('w:cantSplit');pr.append(el)
for i,sh in enumerate(D.inline_shapes):sh._inline.docPr.set('descr',f'Figura científica {i+1}: resultados de desempenho e escalonamento descritos na legenda.')
D.save(ROOT/'Artigo_Linux_Nativo_Atualizado.docx')
print(ROOT/'Artigo_Linux_Nativo_Atualizado.docx')
