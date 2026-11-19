// Run Skelet #1 raw from tape A; report every step i at which the configuration equals target B
// (same state, same head offset from the rightmost 1, and identical cells over B's whole non-sentinel window).
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
static const int W[5][2] = {{1,1},{1,0},{1,1},{0,0},{-1,1}};
static const int M[5][2] = {{1,1},{-1,1},{1,-1},{1,-1},{0,1}};
static const int S[5][2] = {{1,3},{2,2},{0,3},{4,1},{-1,2}};
static uint8_t *load(const char *fn, int64_t pad, int64_t *len, int64_t *head, int *st, int64_t *n_out) {
    FILE *f = fopen(fn, "r"); long long h; int s;
    if (fscanf(f, "%lld %d\n", &h, &s) != 2) exit(2);
    long pos = ftell(f); fseek(f, 0, SEEK_END); long sz = ftell(f); fseek(f, pos, SEEK_SET);
    char *buf = malloc(sz + 1); size_t rd = fread(buf, 1, sz - pos, f); buf[rd] = 0; fclose(f);
    int64_t n = 0; while (buf[n] == '0' || buf[n] == '1' || buf[n] == '!') n++;
    *len = n + 2 * pad; uint8_t *t = calloc(*len, 1);
    for (int64_t i = 0; i < n; i++) t[pad + i] = buf[i] == '!' ? 2 : buf[i] - '0';
    free(buf); *head = pad + h; *st = s; *n_out = n; return t;
}
int main(int argc, char **argv) {
    int64_t N = atoll(argv[3]);
    int64_t la, ha, na, lb, hb, nb; int sa, sb;
    uint8_t *a = load(argv[1], 64LL << 20, &la, &ha, &sa, &na);
    uint8_t *b = load(argv[2], 0, &lb, &hb, &sb, &nb);
    int64_t rb = lb - 1; while (b[rb] != 1) rb--;
    int64_t lo = 0; while (b[lo] == 2) lo++;
    int64_t off_b = rb - hb, win = rb - lo + 1;
    int64_t ra = la - 1; while (a[ra] != 1) ra--;
    int64_t hits = 0;
    for (int64_t i = 0; i <= N; i++) {
        if (sa == sb && ra - ha == off_b) {
            if (memcmp(a + ra - win + 1, b + lo, win) == 0) {
                printf("MATCH step_offset %lld\n", (long long)i); fflush(stdout); if (++hits >= 3) break;
            }
        }
        if (i == N) break;
        uint8_t sym = a[ha];
        if (sym == 2) { fprintf(stderr, "sentinel at %lld\n", (long long)i); return 3; }
        int ns = S[sa][sym]; if (ns < 0) { fprintf(stderr, "halt\n"); return 4; }
        uint8_t w = W[sa][sym]; a[ha] = w;
        if (w == 1 && ha > ra) ra = ha;
        else if (w == 0 && ha == ra) { while (a[ra] != 1) ra--; }
        ha += M[sa][sym]; sa = ns;
    }
    printf("done hits %lld\n", (long long)hits);
    return 0;
}
