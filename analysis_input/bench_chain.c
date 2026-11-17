// bench_chain.c - latencia de acessos alinhados x desalinhados (cadeia de leituras dependentes)
//
// Cada linha de cache guarda, no deslocamento 'off', o indice da PROXIMA linha da cadeia.
// A leitura seguinte so pode comecar depois que a anterior termina; assim o custo extra
// de um acesso que cruza a linha nao fica escondido pelo paralelismo do processador.
// Sem comportamento indefinido: leitura e escrita via memcpy de tamanho fixo.
//
// Compilar (4 bytes, padrao):  gcc -O2 -std=c11 -Wall -Wextra -o bench_chain_4 bench_chain.c
// 8 bytes:                      gcc -O2 -std=c11 -Wall -Wextra -DACCESS_BYTES=8 -o bench_chain_8 bench_chain.c
// Executar:                     taskset -c 2 ./bench_chain_4 > cadeia4_run1.csv
//
// Previsao: cruza a linha quando offset >= LINE - ACCESS_BYTES + 1 (4 B -> 61; 8 B -> 57).
// Coluna ns_por_acesso = ns por salto da cadeia (mesmo formato do bench_align).
#define _GNU_SOURCE
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifndef ACCESS_BYTES
#define ACCESS_BYTES 4
#endif
#if ACCESS_BYTES == 4
typedef uint32_t word_t;
#elif ACCESS_BYTES == 8
typedef uint64_t word_t;
#else
#error "ACCESS_BYTES deve ser 4 ou 8"
#endif

#define LINE      64
#define NLINES    256           /* 16 KiB: cabe na L1 de dados (mede latencia de L1) */
#define INNER     50            /* percursos completos da cadeia por amostra */
#define WARMUP    20
#define REPS      1000

static inline void barrier(void) { __asm__ volatile("" ::: "memory"); }

static inline uint64_t now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}

static uint64_t rng = 88172645463325252ull;
static uint64_t xorshift(void) {
    rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17;
    return rng;
}

/* Percorre 'hops' saltos a partir de 'start'; cada salto depende do valor lido no anterior. */
static size_t chase(const unsigned char *buf, size_t off, size_t start, size_t hops) {
    size_t idx = start;
    for (size_t h = 0; h < hops; h++) {
        word_t v;
        memcpy(&v, buf + idx * LINE + off, sizeof v);
        idx = (size_t)v;
    }
    return idx;
}

/* Grava a cadeia (permutacao de ciclo unico, algoritmo de Sattolo) no deslocamento 'off'. */
static int build_chain(unsigned char *buf, size_t off, const size_t *perm) {
    for (size_t i = 0; i < NLINES; i++) {
        word_t next = (word_t)perm[i];
        memcpy(buf + i * LINE + off, &next, sizeof next);
    }
    /* verificacao: o ciclo deve visitar todas as linhas e voltar ao inicio */
    size_t idx = 0, n = 0;
    do {
        word_t v;
        memcpy(&v, buf + idx * LINE + off, sizeof v);
        idx = (size_t)v; n++;
    } while (idx != 0 && n <= NLINES);
    return n == NLINES;
}

int main(void) {
    size_t size = (size_t)NLINES * LINE + LINE;
    unsigned char *buf = aligned_alloc(LINE, (size + LINE - 1) / LINE * LINE);
    if (!buf) { perror("aligned_alloc"); return 1; }
    memset(buf, 0, size);

    /* permutacao de ciclo unico: next[i] */
    size_t perm[NLINES], tmp[NLINES];
    for (size_t i = 0; i < NLINES; i++) tmp[i] = i;
    for (size_t i = NLINES - 1; i > 0; i--) {         /* Sattolo */
        size_t j = (size_t)(xorshift() % i);
        size_t t = tmp[i]; tmp[i] = tmp[j]; tmp[j] = t;
    }
    for (size_t i = 0; i < NLINES; i++) perm[tmp[i]] = tmp[(i + 1) % NLINES];

    /* ordem aleatoria dos deslocamentos */
    size_t order[LINE];
    for (size_t i = 0; i < LINE; i++) order[i] = i;
    for (size_t i = LINE - 1; i > 0; i--) {
        size_t j = (size_t)(xorshift() % (i + 1));
        size_t t = order[i]; order[i] = order[j]; order[j] = t;
    }

    volatile size_t sink = 0;
    printf("offset,rep,ns_por_acesso\n");
    for (size_t k = 0; k < LINE; k++) {
        size_t off = order[k];
        if (!build_chain(buf, off, perm)) { fprintf(stderr, "cadeia invalida\n"); return 2; }
        size_t idx = 0;
        for (int w = 0; w < WARMUP; w++) idx = chase(buf, off, idx, NLINES);
        for (int r = 0; r < REPS; r++) {
            barrier();
            uint64_t t0 = now_ns();
            for (int n = 0; n < INNER; n++) { idx = chase(buf, off, idx, NLINES); barrier(); }
            uint64_t t1 = now_ns();
            sink += idx;
            printf("%zu,%d,%.4f\n", off, r, (double)(t1 - t0) / ((double)INNER * NLINES));
        }
    }
    fprintf(stderr, "ACCESS_BYTES=%d ok (sink=%zu)\n", ACCESS_BYTES, (size_t)sink);
    free(buf);
    return 0;
}
