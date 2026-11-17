// bench_align.c - acessos alinhados x desalinhados (sem comportamento indefinido)
//
// Compilar (leitura de 4 bytes, padrao):
//   gcc -O2 -std=c11 -Wall -Wextra -o bench_align_4 bench_align.c
// Leitura de 8 bytes (reproduz a primeira coleta):
//   gcc -O2 -std=c11 -Wall -Wextra -DACCESS_BYTES=8 -o bench_align_8 bench_align.c
// Executar fixando um nucleo:
//   taskset -c 2 ./bench_align_4 > dados4_run1.csv
//
// Previsao: o acesso cruza a linha de cache quando offset + ACCESS_BYTES > LINE,
// ou seja, offset >= LINE - ACCESS_BYTES + 1  (4 bytes -> 61; 8 bytes -> 57).
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

#define LINE      64            /* tamanho de linha de cache assumido (conferir com getconf) */
#define NLINES    256           /* 16 KiB: cabe na L1 de dados */
#define INNER     200           /* passadas por amostra */
#define WARMUP    50
#define REPS      1000          /* amostras por deslocamento */

static inline void barrier(void) { __asm__ volatile("" ::: "memory"); }

static inline uint64_t now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}

/* Uma passada: 1 leitura de ACCESS_BYTES por linha, no deslocamento 'off' dentro da linha.
   memcpy de tamanho fixo evita conversao de ponteiros (sem UB); o compilador gera uma carga. */
static uint64_t pass(const unsigned char *buf, size_t off) {
    uint64_t sum = 0;
    for (size_t i = 0; i < NLINES; i++) {
        word_t v;
        memcpy(&v, buf + i * LINE + off, sizeof v);
        sum += v;
    }
    return sum;
}

/* Ordem aleatoria (fixa pela semente) dos deslocamentos: evita que deriva termica/frequencia
   pareca efeito do alinhamento. */
static uint64_t rng = 88172645463325252ull;
static uint64_t xorshift(void) {
    rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17;
    return rng;
}

int main(void) {
    size_t size = (size_t)NLINES * LINE + LINE;   /* folga para off + ACCESS_BYTES na ultima linha */
    unsigned char *buf = aligned_alloc(LINE, (size + LINE - 1) / LINE * LINE);
    if (!buf) { perror("aligned_alloc"); return 1; }
    for (size_t i = 0; i < size; i++) buf[i] = (unsigned char)(i * 31u + 7u);

    size_t order[LINE];
    for (size_t i = 0; i < LINE; i++) order[i] = i;
    for (size_t i = LINE - 1; i > 0; i--) {       /* Fisher-Yates */
        size_t j = (size_t)(xorshift() % (i + 1));
        size_t t = order[i]; order[i] = order[j]; order[j] = t;
    }

    volatile uint64_t sink = 0;
    printf("offset,rep,ns_por_acesso\n");
    for (size_t k = 0; k < LINE; k++) {
        size_t off = order[k];
        for (int w = 0; w < WARMUP; w++) { sink += pass(buf, off); }
        for (int r = 0; r < REPS; r++) {
            uint64_t acc = 0;
            barrier();
            uint64_t t0 = now_ns();
            for (int n = 0; n < INNER; n++) { acc += pass(buf, off); barrier(); }
            uint64_t t1 = now_ns();
            sink += acc;
            printf("%zu,%d,%.4f\n", off, r, (double)(t1 - t0) / ((double)INNER * NLINES));
        }
    }
    fprintf(stderr, "ACCESS_BYTES=%d checksum=%llu\n", ACCESS_BYTES, (unsigned long long)sink);
    free(buf);
    return 0;
}
