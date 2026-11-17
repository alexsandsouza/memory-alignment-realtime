# simulador_rt.py - RM, DM, EDF e LLF com custos inflados por acessos desalinhados
#
# Modelo de custo (hipotese de trabalho, a declarar no relatorio):
#     C_i(p, k) = C_i * (1 + p * (k - 1))
#   C_i : tempo de execucao com acessos alinhados (ms)
#   p   : fracao do tempo da tarefa gasta em acessos que cruzam a linha de cache
#   k   : fator de lentidao por acesso que cruza (medido: ~1,21 vazao; ~2,00 latencia)
#
# Simulacao em tempo discreto (SCALE ticks por ms), preemptiva, 1 processador, liberacao
# sincrona em t=0, horizonte = hiperperiodo, D <= T. Jobs atrasados continuam executando.
# Custos inflados sao arredondados PARA CIMA ao tick (conservador; erro < 1/SCALE ms).
from dataclasses import dataclass
from math import ceil, gcd
from functools import reduce

SCALE = 100            # ticks por ms
POLITICAS = ["RM", "DM", "EDF", "LLF"]

@dataclass(frozen=True)
class Tarefa:
    nome: str
    C: float   # ms
    T: float   # ms
    D: float   # ms (D <= T)

def _lcm(a, b): return a * b // gcd(a, b)

def inflar(C, p, k): return C * (1.0 + p * (k - 1.0))

def _ticks(tarefas, p, k):
    C = [ceil(inflar(t.C, p, k) * SCALE - 1e-9) for t in tarefas]
    T = [round(t.T * SCALE) for t in tarefas]
    D = [round(t.D * SCALE) for t in tarefas]
    return C, T, D

def utilizacao(tarefas, p=0.0, k=1.0):
    return sum(inflar(t.C, p, k) / t.T for t in tarefas)

def simular(tarefas, politica, p=0.0, k=1.0):
    """Retorna dict com perdidos, total, resp_max (ms, por tarefa), preempcoes, incompletos."""
    n = len(tarefas)
    C, T, D = _ticks(tarefas, p, k)
    H = reduce(_lcm, T)
    if politica == "RM":   ordem = sorted(range(n), key=lambda i: (T[i], i))
    elif politica == "DM": ordem = sorted(range(n), key=lambda i: (D[i], i))
    else:                  ordem = list(range(n))
    rank = [0] * n
    for r, i in enumerate(ordem): rank[i] = r

    prox = [0] * n                 # proxima liberacao de cada tarefa
    pronto = []                    # jobs: [tarefa, liberacao, deadline_abs, restante]
    atual = None
    t = 0; perdidos = 0; total = 0; preempcoes = 0
    resp_max = [0] * n
    perd_t = [0] * n

    while t < H:
        for i in range(n):
            if prox[i] == t:
                pronto.append([i, t, t + D[i], C[i]])
                prox[i] += T[i]; total += 1
        if not pronto:
            atual = None
            t = min(min(prox), H); continue
        if politica in ("RM", "DM"):
            job = min(pronto, key=lambda j: (rank[j[0]], j[1]))
        elif politica == "EDF":
            job = min(pronto, key=lambda j: (j[2], j[1], j[0]))
        elif politica == "LLF":
            job = min(pronto, key=lambda j: (j[2] - t - j[3], 0 if j is atual else 1, j[2], j[1], j[0]))
        else:
            raise ValueError(politica)
        if atual is not None and job is not atual and atual in pronto:
            preempcoes += 1
        atual = job
        passo = 1 if politica == "LLF" else min(job[3], min(prox) - t, H - t)
        passo = max(1, min(passo, job[3]))
        job[3] -= passo; t += passo
        if job[3] == 0:
            pronto.remove(job); atual = None
            i = job[0]
            resp_max[i] = max(resp_max[i], t - job[1])
            if t > job[2]:
                perdidos += 1; perd_t[i] += 1
    incompletos = len(pronto)       # todos com deadline <= H -> perdidos
    inc_t = [0] * n
    for job in pronto:
        resp_max[job[0]] = max(resp_max[job[0]], H - job[1])
        perd_t[job[0]] += 1; inc_t[job[0]] += 1
    perdidos += incompletos
    return {"perdidos": perdidos, "total": total, "incompletos": incompletos,
            "resp_max": [r / SCALE for r in resp_max], "preempcoes": preempcoes,
            "perdidos_tarefa": perd_t, "incompletos_tarefa": inc_t,
            "hiperperiodo": H / SCALE}

def rta(tarefas, politica, p=0.0, k=1.0):
    """Analise de tempo de resposta exata para RM/DM (valida o simulador). Retorna ms ou None."""
    C, T, D = _ticks(tarefas, p, k)
    n = len(tarefas)
    chave = T if politica == "RM" else D
    ordem = sorted(range(n), key=lambda i: (chave[i], i))
    R = [None] * n
    for pos, i in enumerate(ordem):
        hp = ordem[:pos]
        r = C[i]
        while True:
            novo = C[i] + sum(ceil(r / T[j]) * C[j] for j in hp)
            if novo == r: break
            r = novo
            if r > D[i]: break
        R[i] = r / SCALE if r <= D[i] else None
    return R

def p_critico(tarefas, politica, k, tol=0.002):
    """Menor p em [0,1] com alguma perda de deadline (bisseccao; escalonabilidade e
    monotona em C para estas politicas em 1 processador). None se nao ha perda ate p=1."""
    if simular(tarefas, politica, 0.0, k)["perdidos"] > 0: return 0.0
    if simular(tarefas, politica, 1.0, k)["perdidos"] == 0: return None
    lo, hi = 0.0, 1.0
    while hi - lo > tol:
        mid = (lo + hi) / 2
        if simular(tarefas, politica, mid, k)["perdidos"] > 0: hi = mid
        else: lo = mid
    return hi


# ---------------------------------------------------------------------------
# Conjuntos de tarefas (C, T, D em ms; todos escalonaveis por RM, DM, EDF e LLF com p = 0)
# ---------------------------------------------------------------------------
CONJUNTOS = {
    "A - harmonico (D=T)": [Tarefa("t1", 2, 10, 10), Tarefa("t2", 4, 20, 20),
                            Tarefa("t3", 8, 40, 40), Tarefa("t4", 8, 80, 80)],
    "B - nao harmonico (D=T)": [Tarefa("t1", 2, 10, 10), Tarefa("t2", 3, 14, 14),
                                Tarefa("t3", 5, 35, 35), Tarefa("t4", 8, 50, 50)],
    "C - prazos restritos (D<T)": [Tarefa("t1", 4, 10, 10), Tarefa("t2", 2, 20, 16),
                                   Tarefa("t3", 4, 30, 15), Tarefa("t4", 1, 40, 24)],
    "D - carga alta (D=T)": [Tarefa("t1", 3, 10, 10), Tarefa("t2", 4, 15, 15),
                             Tarefa("t3", 5, 35, 35), Tarefa("t4", 9, 60, 60)],
}

# Fatores k por acesso que cruza a linha (razao cruza / nao cruza, 4 bytes). Valores padrao =
# os medidos no WSL2 (i5-12450H); usar_dados(pasta) os recalcula a partir dos CSVs brutos.
K_MEDIANA = {"vazao": 1.214, "latencia": 1.999}
K_P99     = {"vazao p99": 1.146, "latencia p99": 1.915}
GRADE_P   = [round(0.1 * i, 1) for i in range(11)]


def k_dos_dados(pasta="."):
    """Calcula k a partir dos CSVs brutos. Retorna (dict de k por cenario, DataFrame resumo).
    k_mediana = mediana(cruza) / mediana(nao cruza), sobre todas as amostras.
    k_p99     = mediana do p99 por (rodada, offset) no grupo cruza / no grupo nao cruza.
    Tambem informa o intervalo de k entre as rodadas."""
    import pandas as pd, glob, os
    coletas = [("vazao", "dados4_run*.csv", 4, True), ("latencia", "cadeia4_run*.csv", 4, True),
               ("vazao 8 bytes (informativo)", ["dados8_run*.csv", "dados_run*.csv"], 8, False)]
    ks, linhas = {}, []
    for nome, padrao, acc, usar in coletas:
        pads = [padrao] if isinstance(padrao, str) else padrao
        arqs = sorted({f for p in pads for f in glob.glob(os.path.join(pasta, p))})
        if not arqs: continue
        lim = 64 - acc + 1
        d = pd.concat([pd.read_csv(f).assign(run=os.path.basename(f)) for f in arqs])
        d["cruza"] = d["offset"] >= lim
        med = d.groupby("cruza").ns_por_acesso.median()
        kr = d.groupby(["run", "cruza"]).ns_por_acesso.median().unstack()
        kr = kr[True] / kr[False]
        q = d.groupby(["run", "offset"]).ns_por_acesso.quantile(.99).reset_index()
        q["cruza"] = q["offset"] >= lim
        mq = q.groupby("cruza").ns_por_acesso.median()
        qr = q.groupby(["run", "cruza"]).ns_por_acesso.median().unstack()
        qr = qr[True] / qr[False]
        km, kq = med[True] / med[False], mq[True] / mq[False]
        linhas.append({"coleta": nome, "acesso_bytes": acc, "limiar_offset": lim, "rodadas": len(arqs),
                       "mediana_nao_cruza_ns": round(med[False], 4), "mediana_cruza_ns": round(med[True], 4),
                       "k_mediana": round(km, 4), "k_mediana_min_rodada": round(kr.min(), 4),
                       "k_mediana_max_rodada": round(kr.max(), 4),
                       "p99_nao_cruza_ns": round(mq[False], 4), "p99_cruza_ns": round(mq[True], 4),
                       "k_p99": round(kq, 4), "k_p99_min_rodada": round(qr.min(), 4),
                       "k_p99_max_rodada": round(qr.max(), 4)})
        if usar:
            ks[nome] = float(round(km, 3)); ks[nome + " p99"] = float(round(kq, 3))
    return ks, pd.DataFrame(linhas)


def usar_dados(pasta="."):
    """Atualiza K_MEDIANA e K_P99 com os k calculados dos CSVs. Se nao houver CSVs, mantem os padroes."""
    ks, resumo = k_dos_dados(pasta)
    if {"vazao", "latencia", "vazao p99", "latencia p99"} <= set(ks):
        K_MEDIANA.update({"vazao": ks["vazao"], "latencia": ks["latencia"]})
        K_P99.update({"vazao p99": ks["vazao p99"], "latencia p99": ks["latencia p99"]})
        print("k atualizados a partir dos dados:", {**K_MEDIANA, **K_P99})
    else:
        print("CSVs nao encontrados em", pasta, "- usando k padrao:", {**K_MEDIANA, **K_P99})
    return resumo


def varrer(conjuntos=CONJUNTOS, ks=None, ps=GRADE_P, politicas=POLITICAS):
    import pandas as pd
    ks = ks or {**K_MEDIANA, **K_P99}
    linhas = []
    for cn, ts in conjuntos.items():
        for kn, k in ks.items():
            for p in ps:
                U = utilizacao(ts, p, k)
                for pol in politicas:
                    r = simular(ts, pol, p, k)
                    linhas.append({
                        "conjunto": cn, "cenario": kn, "k": k, "p": p, "politica": pol,
                        "U_inflada": round(U, 4), "jobs": r["total"], "perdidos": r["perdidos"],
                        "perda_pct": round(100 * r["perdidos"] / r["total"], 2),
                        "resp_max_sobre_D": round(max(r["resp_max"][i] / ts[i].D for i in range(len(ts))), 3),
                        "preempcoes": r["preempcoes"]})
    return pd.DataFrame(linhas)


def tabela_p_critico(conjuntos=CONJUNTOS, ks=None):
    """p minimo (em %) em que surge a primeira perda de deadline; '-' = sem perda ate p=100%."""
    import pandas as pd
    ks = ks or {**K_MEDIANA, **K_P99}
    linhas = []
    for cn, ts in conjuntos.items():
        for pol in POLITICAS:
            lin = {"conjunto": cn, "politica": pol, "U_base": round(utilizacao(ts), 3)}
            for kn, k in ks.items():
                pc = p_critico(ts, pol, k)
                lin[kn] = "-" if pc is None else round(100 * pc, 1)
            linhas.append(lin)
    return pd.DataFrame(linhas)


def grafico(df, arquivo="perdas_vs_p.png", cenarios=None):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    existentes = set(df["cenario"])
    cenarios = cenarios or [c for c in K_MEDIANA if c in existentes]
    faltam = [c for c in cenarios if c not in existentes]
    if not cenarios or faltam:
        raise ValueError(f"o df nao tem os cenarios {faltam or list(K_MEDIANA)}; cenarios no df: "
                         f"{sorted(existentes)}. Gere o df de novo: df = sim.varrer()")
    conj = list(df["conjunto"].unique())
    fig, axs = plt.subplots(len(conj), len(cenarios), figsize=(5.2 * len(cenarios), 2.8 * len(conj)),
                            sharex=True, squeeze=False)
    estilo = {"RM": ("o", "-"), "DM": ("s", "--"), "EDF": ("^", "-"), "LLF": ("x", ":")}
    for i, cn in enumerate(conj):
        for j, kn in enumerate(cenarios):
            ax = axs[i][j]
            for pol in POLITICAS:
                g = df[(df.conjunto == cn) & (df.cenario == kn) & (df.politica == pol)].sort_values("p")
                m, ls = estilo[pol]
                ax.plot(100 * g["p"], g["perda_pct"], marker=m, linestyle=ls, markersize=4, label=pol)
            topo = max(df[(df.conjunto == cn) & (df.cenario == kn)]["perda_pct"].max() * 1.08, 1.0)
            ax.set_ylim(-0.03 * topo, topo)
            kv = df[df.cenario == kn]["k"].iloc[0]
            ax.set_title(f"{cn} | {kn} (k={kv:.3f})", fontsize=8)
            ax.grid(alpha=0.3)
            if j == 0: ax.set_ylabel("jobs perdidos (%)")
            if i == len(conj) - 1: ax.set_xlabel("p: fracao do tempo em acessos que cruzam a linha (%)")
    axs[0][0].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(arquivo, dpi=150); plt.close(fig)
    return arquivo


def tabela_resposta(conjuntos=CONJUNTOS, ks=None, ps=(0.0, 0.25, 0.5, 1.0)):
    """Tempo de resposta maximo por tarefa, comparado ao deadline.
    resp_ge=True: ha job da tarefa que nao terminou ate o fim do hiperperiodo; o valor e entao
    um limite inferior (>= R)."""
    import pandas as pd
    ks = ks or K_MEDIANA
    linhas = []
    for cn, ts in conjuntos.items():
        for kn, k in ks.items():
            for p in ps:
                for pol in POLITICAS:
                    r = simular(ts, pol, p, k)
                    for i, t in enumerate(ts):
                        R = r["resp_max"][i]
                        linhas.append({
                            "conjunto": cn, "cenario": kn, "p": p, "politica": pol, "tarefa": t.nome,
                            "k": k, "C_inflado_ms": round(inflar(t.C, p, k), 3), "D_ms": t.D,
                            "R_max_ms": round(R, 2), "R_sobre_D": round(R / t.D, 3),
                            "jobs_perdidos": r["perdidos_tarefa"][i], "resp_ge": r["incompletos_tarefa"][i] > 0})
    return pd.DataFrame(linhas)


def tarefa_critica(conjuntos=CONJUNTOS, ks=None):
    """Para cada politica: p critico e quais tarefas perdem deadline logo apos esse ponto."""
    import pandas as pd
    ks = ks or K_MEDIANA
    linhas = []
    for cn, ts in conjuntos.items():
        for kn, k in ks.items():
            for pol in POLITICAS:
                pc = p_critico(ts, pol, k)
                if pc is None:
                    linhas.append({"conjunto": cn, "cenario": kn, "politica": pol,
                                   "p_critico_pct": "-", "tarefas_que_perdem": "nenhuma ate p=100%"})
                    continue
                r = simular(ts, pol, min(1.0, pc + 0.002), k)
                falham = [ts[i].nome for i, c in enumerate(r["perdidos_tarefa"]) if c > 0]
                linhas.append({"conjunto": cn, "cenario": kn, "politica": pol,
                               "p_critico_pct": round(100 * pc, 1), "tarefas_que_perdem": ", ".join(falham)})
    return pd.DataFrame(linhas)


def grafico_resposta(df, p=0.25, cenario="latencia", arquivo="resposta_por_tarefa.png", teto=3.0):
    """Barras de R_max/D por tarefa e politica; a linha tracejada (=1) e o deadline."""
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    d = df[(df.p == p) & (df.cenario == cenario)]
    if d.empty:
        raise ValueError(f"nao ha dados para p={p} e cenario '{cenario}'; cenarios no df: "
                         f"{sorted(set(df['cenario']))}, p: {sorted(set(df['p']))}. "
                         "Gere de novo: resp = sim.tabela_resposta()")
    conj = list(d["conjunto"].unique())
    fig, axs = plt.subplots(2, 2, figsize=(10, 6.5), squeeze=False)
    cores = {"RM": "#1f77b4", "DM": "#ff7f0e", "EDF": "#2ca02c", "LLF": "#d62728"}
    for ax, cn in zip(axs.ravel(), conj):
        g = d[d.conjunto == cn]
        tarefas = list(g["tarefa"].unique()); x = np.arange(len(tarefas)); w = 0.2
        for j, pol in enumerate(POLITICAS):
            v = [g[(g.politica == pol) & (g.tarefa == t)]["R_sobre_D"].iloc[0] for t in tarefas]
            ax.bar(x + (j - 1.5) * w, np.minimum(v, teto), w, label=pol, color=cores[pol])
            for xi, vi in zip(x, v):
                if vi > teto: ax.text(xi + (j - 1.5) * w, teto, "^", ha="center", va="bottom", fontsize=7)
        ax.axhline(1.0, color="k", linestyle="--", linewidth=1)
        ax.set_xticks(x); ax.set_xticklabels(tarefas); ax.set_ylim(0, teto * 1.08)
        ax.set_title(cn, fontsize=9); ax.grid(axis="y", alpha=0.3)
        ax.set_ylabel("R máx / D")
    axs[0][0].legend(fontsize=7, ncol=4)
    fig.suptitle(f"Tempo de resposta máximo / deadline | p = {int(100*p)}% | {cenario} (k={d['k'].iloc[0]:.3f})  (^ = acima de {teto:g})", fontsize=10)
    fig.tight_layout(); fig.savefig(arquivo, dpi=150); plt.close(fig)
    return arquivo


# ---------------------------------------------------------------------------
# Cenarios exploratorios da coleta estendida (escrita, L2/L3/DRAM): k com faixa p10-p90
# ---------------------------------------------------------------------------
_NOME_K = {"R_vazao": "leitura em vazao", "W_vazao": "escrita em vazao",
           "R_cadeia": "leitura em cadeia", "RMW_cadeia": "leitura-escrita em cadeia"}
_NOME_T = {16: "L1", 512: "L2", 4096: "L3", 131072: "DRAM"}


def k_ext_resumo(pasta=".", salvar="k_ext_resumo.csv"):
    """Gera o resumo de k a partir dos CSVs brutos ext4_run*.csv e ext8_run*.csv da pasta.
    Usa os 8 cenarios equivalentes (todos menos vetor_bytes) x rodadas como replicas; k = mediana(cruza)/mediana(alinhado)
    em cada (cenario, rodada). Retorna o DataFrame e, se 'salvar', grava o CSV (na pasta indicada)."""
    import pandas as pd, glob, os
    linhas = []
    for acc in (4, 8):
        arqs = sorted(glob.glob(os.path.join(pasta, f"ext{acc}_run*.csv")))
        if not arqs: continue
        d = pd.concat([pd.read_csv(f).assign(run=int(os.path.basename(f).split("run")[1].split(".")[0])) for f in arqs])
        med = d.groupby(["kernel", "buf_kib", "cenario", "run", "classe"]).ns_por_acesso.median().unstack("classe")
        med["k_cruza"] = med["cruza"] / med["alinhado"]
        med["k_dentro"] = med["dentro"] / med["alinhado"]
        med["delta_ns"] = med["cruza"] - med["alinhado"]
        eq = med[[c != "vetor_bytes" for c in med.index.get_level_values("cenario")]]
        g = eq.groupby(level=["kernel", "buf_kib"])
        linhas.append(pd.DataFrame({
            "acesso_bytes": acc, "replicas": g.size(),
            "k_cruza_mediana": g.k_cruza.median(),
            "k_cruza_p10": g.k_cruza.quantile(.10), "k_cruza_p90": g.k_cruza.quantile(.90),
            "k_dentro_mediana": g.k_dentro.median(),
            "delta_ns_mediana": g.delta_ns.median()}).reset_index())
    if not linhas:
        raise FileNotFoundError(f"nao ha ext4_run*.csv nem ext8_run*.csv em '{os.path.abspath(pasta)}'. "
                                "Coloque os CSVs da coleta estendida nessa pasta (ou passe pasta='caminho').")
    res = pd.concat(linhas)
    if salvar: res.to_csv(os.path.join(pasta, salvar), index=False)
    return res


def cenarios_ext(csv="k_ext_resumo.csv", acesso=4, k_min=1.05, pasta="."):
    """Retorna {nome: (k_p10, k_mediana, k_p90)} dos cenarios da coleta estendida.
    Le 'csv' (dentro de 'pasta'); se ele nao existir, gera a partir dos ext*_run*.csv da pasta (k_ext_resumo).
    Descarta cenarios com k mediano < k_min (sem efeito mensuravel)."""
    import pandas as pd, os
    caminho = csv if os.path.isabs(csv) else os.path.join(pasta, csv)
    r = pd.read_csv(caminho) if os.path.exists(caminho) else k_ext_resumo(pasta, salvar=os.path.basename(csv))
    r = r[r.acesso_bytes == acesso]
    out = {}
    for _, x in r.iterrows():
        if x.k_cruza_mediana < k_min: continue
        out[f"{_NOME_K[x.kernel]} {_NOME_T[int(x.buf_kib)]}"] = (
            round(max(float(x.k_cruza_p10), 1.0), 3), round(float(x.k_cruza_mediana), 3), round(float(x.k_cruza_p90), 3))
    return out


def p_critico_faixa(ks, conjuntos=CONJUNTOS, politicas=POLITICAS, tol=0.005):
    """p critico (%) para k pessimista (p90), k mediano e k otimista (p10) de cada cenario.
    k maior => p critico menor. '-' = sem perda ate p = 100%."""
    import pandas as pd
    f = lambda v: "-" if v is None else round(100 * v, 1)
    linhas = []
    for cn, ts in conjuntos.items():
        for nome, (klo, kmid, khi) in ks.items():
            for pol in politicas:
                linhas.append({"conjunto": cn, "cenario": nome, "politica": pol,
                               "k_p10": klo, "k_mediana": kmid, "k_p90": khi,
                               "p_crit_pessimista": f(p_critico(ts, pol, khi, tol)),
                               "p_crit_mediana": f(p_critico(ts, pol, kmid, tol)),
                               "p_crit_otimista": f(p_critico(ts, pol, klo, tol))})
    return pd.DataFrame(linhas)


def validar():
    """Testes de sanidade do simulador."""
    # 1) exemplo classico: RM e DM perdem deadline, EDF e LLF nao
    ts = [Tarefa("a", 2, 5, 5), Tarefa("b", 4, 7, 7)]
    assert simular(ts, "RM")["perdidos"] > 0 and simular(ts, "DM")["perdidos"] > 0
    assert simular(ts, "EDF")["perdidos"] == 0 and simular(ts, "LLF")["perdidos"] == 0
    # 2) tempo de resposta maximo simulado == analise exata (RTA) para RM e DM
    for cn, ts in CONJUNTOS.items():
        for pol in ("RM", "DM"):
            for p, k in ((0.0, 1.0), (0.05, 2.0), (0.1, 1.22)):
                R = rta(ts, pol, p, k)
                s = simular(ts, pol, p, k)
                if all(r is not None for r in R):
                    assert s["perdidos"] == 0 and R == s["resp_max"], (cn, pol, p, k, R, s["resp_max"])
                else:
                    assert s["perdidos"] > 0, (cn, pol, p, k)
    # 3) EDF/LLF com D=T: sem perdas se U<=1 e com perdas se U>1 (folga de 1% por arredondamento)
    for cn, ts in CONJUNTOS.items():
        if any(t.D != t.T for t in ts): continue
        for k in (1.22, 2.0):
            for p in GRADE_P:
                U = utilizacao(ts, p, k)
                for pol in ("EDF", "LLF"):
                    perd = simular(ts, pol, p, k)["perdidos"]
                    if U <= 0.99: assert perd == 0, (cn, pol, p, k, U)
                    if U >= 1.01: assert perd > 0, (cn, pol, p, k, U)
    print("validacao OK")


if __name__ == "__main__":
    import sys
    validar()
    resumo = usar_dados(".")
    resumo.to_csv("fatores_k.csv", index=False)
    print(resumo.T.to_string(header=False))
    df = varrer()
    df.to_csv("resultados_simulacao.csv", index=False)
    tab = tabela_p_critico()
    tab.to_csv("p_critico.csv", index=False)
    print(tab.to_string(index=False))
    print("grafico:", grafico(df))
    resp = tabela_resposta(); resp.to_csv("resposta_por_tarefa.csv", index=False)
    crit = tarefa_critica();  crit.to_csv("tarefa_critica.csv", index=False)
    print(crit.to_string(index=False))
    print("grafico:", grafico_resposta(resp, p=0.25), grafico_resposta(resp, p=0.5, cenario="vazao", arquivo="resposta_por_tarefa_vazao.png"))
    import glob
    if glob.glob("ext4_run*.csv") or glob.glob("k_ext_resumo.csv"):
        ext = p_critico_faixa(cenarios_ext("k_ext_resumo.csv"))
        ext.to_csv("p_critico_ext.csv", index=False)
        print("p_critico_ext.csv:", len(ext), "linhas")
