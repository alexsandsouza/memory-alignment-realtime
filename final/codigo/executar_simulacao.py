from pathlib import Path
import importlib.util,sys,json,math,time
import pandas as pd
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('sim',ROOT/'codigo/simulador3_original.py');s=importlib.util.module_from_spec(spec);sys.modules['sim']=s;spec.loader.exec_module(s)
base=s.simular;cache={}
def cached(ts,pol,p=0.,k=1.):
 C,T,D=s._ticks(ts,p,k);key=(tuple(C),tuple(T),tuple(D),pol)
 if key not in cache:cache[key]=base(ts,pol,p,k)
 return cache[key]
s.simular=cached
s.validar()
# Independent per-tick reference for event-driven RM/DM/EDF; deadline counted at H.
def reference(ts,pol,p,k):
 C,T,D=s._ticks(ts,p,k);H=math.lcm(*T);jobs=[];finished=[]
 rank={i:r for r,i in enumerate(sorted(range(len(ts)),key=lambda i:((T if pol=='RM' else D)[i],i)))}
 for t in range(H):
  for i in range(len(ts)):
   if t%T[i]==0:jobs.append([i,t,t+D[i],C[i]])
  if not jobs:continue
  j=min(jobs,key=(lambda j:(j[2],j[1],j[0])) if pol=='EDF' else (lambda j:(rank[j[0]],j[1])))
  j[3]-=1
  if j[3]==0:finished.append((j[0],t+1-j[1],t+1>j[2]));jobs.remove(j)
 response=[0]*len(ts)
 for i,r,late in finished:response[i]=max(response[i],r)
 for i,rel,dl,rem in jobs:response[i]=max(response[i],H-rel)
 return sum(x[2] for x in finished)+len(jobs),[r/s.SCALE for r in response]
checks=0
for ts in s.CONJUNTOS.values():
 for pol in ['RM','DM','EDF']:
  for p in [0,.25,1]:
   a=base(ts,pol,p,1.9989447766443897);b=reference(ts,pol,p,1.9989447766443897)
   assert (a['perdidos'],a['resp_max'])==b
   checks+=1
print('Referencia independente OK:',checks,flush=True)
f=pd.read_csv(ROOT.parent/'entrega/fatores_custo.csv');ks={}
for _,r in f.iterrows():
 typ='vazao' if r.cenario=='Independentes' else 'latencia'
 ks[f'{typ} {int(r.bytes)}B']=r.k
 ks[f'{typ} {int(r.bytes)}B p99']=r.k_p99
(ROOT/'tabelas/fatores_usados.json').write_text(json.dumps(ks,indent=2))
# Main grid, full precision k. Discrete costs and effective utilization explicitly saved.
frames=[]
for name,k in ks.items():
 print('Simulando',name,k,flush=True)
 df=s.varrer(ks={name:k})
 eff=[]
 for _,r in df.iterrows():
  C,T,D=s._ticks(s.CONJUNTOS[r.conjunto],r.p,k);eff.append(sum(c/t for c,t in zip(C,T)))
 df['U_efetiva_ticks']=eff;frames.append(df)
df=pd.concat(frames,ignore_index=True);df.to_csv(ROOT/'tabelas/simulacao.csv',index=False)
print('Calculando limiares',flush=True)
crit=s.tabela_p_critico(ks=ks);crit.to_csv(ROOT/'tabelas/p_critico.csv',index=False)
resp=s.tabela_resposta(ks={k:v for k,v in ks.items() if 'p99' not in k});resp.to_csv(ROOT/'tabelas/respostas.csv',index=False)
s.grafico(df,arquivo=str(ROOT/'figuras/perdas_4bytes.png'),cenarios=['vazao 4B','latencia 4B'])
s.grafico_resposta(resp,p=.25,cenario='latencia 4B',arquivo=str(ROOT/'figuras/respostas_latencia4.png'))
(ROOT/'tabelas/validacao.json').write_text(json.dumps({'validacao_original':'OK','comparacoes_referencia_tick':checks,'resultado':'OK','tick_ms':.01,'tolerancia_bisseccao_p':.002,'valores_k':'precisao integral do CSV, sem arredondar para tres casas','cenarios':len(ks),'linhas_grade':len(df),'cache_estados':len(cache)},indent=2))
print(crit.to_string(index=False),flush=True)
