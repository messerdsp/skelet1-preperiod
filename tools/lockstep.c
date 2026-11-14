// Lockstep raw simulation for Skelet #1 (1RB1RD_1LC0RC_1RA1LD_0RE0LB_---1RC).
// A runs from a checkpoint; B is A advanced by P steps. For each step i in [0, N) compares the
// transition (state, symbol read) of A at time t_c+i with B at time t_c+P+i, and reports the
// last i where they differ. Tape cell value 2 = sentinel (region assumed never visited): abort.
// usage: lockstep <tapefile> <P> <N>
//   tapefile: line 1 "<head_index> <state 0-4>", line 2: tape over {0,1,!}
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

static const int W[5][2] = {{1,1},{1,0},{1,1},{0,0},{-1,1}};
static const int M[5][2] = {{1,1},{-1,1},{1,-1},{1,-1},{0,1}};   // +1 = R, -1 = L
static const int S[5][2] = {{1,3},{2,2},{0,3},{4,1},{-1,2}};

typedef struct { uint8_t *tape; int64_t len, head; int state; } Sim;

static inline int step(Sim *s) {
    uint8_t sym = s->tape[s->head];
    if (sym == 2) { fprintf(stderr, "sentinel reached\n"); exit(3); }
    int st = s->state;
    if (S[st][sym] < 0) { fprintf(stderr, "HALT\n"); exit(4); }
    s->tape[s->head] = W[st][sym];
    s->state = S[st][sym];
    s->head += M[st][sym];
    if (s->head < 0 || s->head >= s->len) { fprintf(stderr, "tape bound\n"); exit(5); }
    return st * 2 + sym;
}

int main(int argc, char **argv) {
    if (argc < 4) { fprintf(stderr, "usage\n"); return 1; }
    FILE *f = fopen(argv[1], "r");
    long long head0; int st0;
    if (fscanf(f, "%lld %d\n", &head0, &st0) != 2) return 2;
    fseek(f, 0, SEEK_END); long sz = ftell(f); fseek(f, 0, SEEK_SET);
    char *buf = malloc(sz + 1); size_t rd = fread(buf, 1, sz, f); buf[rd] = 0; fclose(f);
    char *t = strchr(buf, '\n') + 1;
    int64_t n = 0; while (t[n] == '0' || t[n] == '1' || t[n] == '!') n++;
    int64_t PAD = 64LL << 20;
    int64_t len = n + 2 * PAD;
    int64_t P = atoll(argv[2]), N = atoll(argv[3]);
    Sim a, b;
    a.tape = calloc(len, 1); a.len = len; a.head = PAD + head0; a.state = st0;
    for (int64_t i = 0; i < n; i++) a.tape[PAD + i] = t[i] == '!' ? 2 : t[i] - '0';
    b = a; b.tape = malloc(len); memcpy(b.tape, a.tape, len);
    for (int64_t i = 0; i < P; i++) step(&b);
    int64_t last = -1, first = -1, cnt = 0;
    for (int64_t i = 0; i < N; i++) {
        int ra = step(&a), rb = step(&b);
        if (ra != rb) { last = i; if (first < 0) first = i; cnt++; }
    }
    printf("first_mismatch %lld last_mismatch %lld count %lld head_shift %lld stateA %d stateB %d\n",
           (long long)first, (long long)last, (long long)cnt, (long long)(b.head - a.head), a.state, b.state);
    return 0;
}
