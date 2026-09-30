#!/usr/bin/env python3
"""Generate the ML-KEM test vectors used by libmlkem-lbmk.

Contains a straightforward (slow, not constant time) Python implementation of
FIPS 203 ML-KEM. Only the Python standard library is needed.

For each parameter set, it produces NCASES deterministic test cases:
- keygen_seed: d || z (64 bytes), input of ML-KEM.KeyGen_internal
- encaps_seed: m (32 bytes), input of ML-KEM.Encaps_internal
- SHA-256 digests of the resulting encapsulation key, decapsulation key and ciphertext
- the shared secret
- the shared secret for the implicit rejection case: the ciphertext with bit 0
  of its first byte flipped, the expected output is J(z || c')

The seeds are derived from a fixed string so the output is reproducible.
SampleNTT (generation of the matrix A) consumes 3 SHAKE128 blocks for most
polynomials but sometimes needs a 4th one (about 0.7% of the polynomials): the
last NSLOW cases are selected to hit that slower path, so that the worst case
of key generation, encapsulation and decapsulation is benchmarked.

Before generating anything, the implementation is checked against the ML-KEM
known answer tests of wolfSSL (wolfcrypt/test/test.c, mlkem*_kat).
"""
import argparse
import hashlib
import os

Q = 3329
N = 256

PARAMS = {
    512: {'k': 2, 'eta1': 3, 'eta2': 2, 'du': 10, 'dv': 4},
    768: {'k': 3, 'eta1': 2, 'eta2': 2, 'du': 10, 'dv': 4},
    1024: {'k': 4, 'eta1': 2, 'eta2': 2, 'du': 11, 'dv': 5},
}

NCASES = 16
NSLOW = 2


def bitrev7(i):
    return int(f'{i:07b}'[::-1], 2)


ZETAS = [pow(17, bitrev7(i), Q) for i in range(128)]
GAMMAS = [pow(17, 2 * bitrev7(i) + 1, Q) for i in range(128)]


def H(s):
    return hashlib.sha3_256(s).digest()


def J(s):
    return hashlib.shake_256(s).digest(32)


def G(s):
    d = hashlib.sha3_512(s).digest()
    return d[:32], d[32:]


def PRF(eta, s, b):
    return hashlib.shake_256(s + bytes([b])).digest(64 * eta)


def bytes_to_bits(b):
    return [(byte >> i) & 1 for byte in b for i in range(8)]


def bits_to_bytes(bits):
    return bytes(sum(bits[i + j] << j for j in range(8)) for i in range(0, len(bits), 8))


def byte_encode(d, f):
    bits = [(a >> j) & 1 for a in f for j in range(d)]
    return bits_to_bytes(bits)


def byte_decode(d, b):
    m = Q if d == 12 else 1 << d
    bits = bytes_to_bits(b)
    return [sum(bits[i * d + j] << j for j in range(d)) % m for i in range(N)]


def compress(d, f):
    # round(2^d/q * x) mod 2^d, rounding half up
    return [((x << (d + 1)) + Q) // (2 * Q) % (1 << d) for x in f]


def decompress(d, f):
    # round(q/2^d * y), rounding half up
    return [(y * Q * 2 + (1 << d)) >> (d + 1) for y in f]


class XofCounter:
    """Keep track of the largest number of SHAKE128 blocks SampleNTT needed."""
    max_blocks = 0


def sample_ntt(b):
    size = 3 * 168
    while True:
        c = hashlib.shake_128(b).digest(size)
        a = []
        pos = 0
        while len(a) < N and pos + 3 <= size:
            d1 = c[pos] + 256 * (c[pos + 1] % 16)
            d2 = c[pos + 1] // 16 + 16 * c[pos + 2]
            pos += 3
            if d1 < Q:
                a.append(d1)
            if d2 < Q and len(a) < N:
                a.append(d2)
        if len(a) == N:
            XofCounter.max_blocks = max(XofCounter.max_blocks, (pos + 167) // 168)
            return a
        size += 168


def sample_cbd(eta, b):
    bits = bytes_to_bits(b)
    f = []
    for i in range(N):
        x = sum(bits[2 * i * eta + j] for j in range(eta))
        y = sum(bits[2 * i * eta + eta + j] for j in range(eta))
        f.append((x - y) % Q)
    return f


def ntt(f):
    f = list(f)
    i = 1
    length = 128
    while length >= 2:
        for start in range(0, N, 2 * length):
            zeta = ZETAS[i]
            i += 1
            for j in range(start, start + length):
                t = zeta * f[j + length] % Q
                f[j + length] = (f[j] - t) % Q
                f[j] = (f[j] + t) % Q
        length //= 2
    return f


def ntt_inv(f):
    f = list(f)
    i = 127
    length = 2
    while length <= 128:
        for start in range(0, N, 2 * length):
            zeta = ZETAS[i]
            i -= 1
            for j in range(start, start + length):
                t = f[j]
                f[j] = (t + f[j + length]) % Q
                f[j + length] = zeta * (f[j + length] - t) % Q
        length *= 2
    return [x * 3303 % Q for x in f]


def multiply_ntts(f, g):
    h = [0] * N
    for i in range(128):
        a0, a1 = f[2 * i], f[2 * i + 1]
        b0, b1 = g[2 * i], g[2 * i + 1]
        h[2 * i] = (a0 * b0 + a1 * b1 * GAMMAS[i]) % Q
        h[2 * i + 1] = (a0 * b1 + a1 * b0) % Q
    return h


def poly_add(f, g):
    return [(a + b) % Q for a, b in zip(f, g)]


def poly_sub(f, g):
    return [(a - b) % Q for a, b in zip(f, g)]


def gen_matrix(k, rho):
    # a_hat[i][j] = SampleNTT(rho || j || i)
    return [[sample_ntt(rho + bytes([j, i])) for j in range(k)] for i in range(k)]


def dot(u, v):
    acc = [0] * N
    for a, b in zip(u, v):
        acc = poly_add(acc, multiply_ntts(a, b))
    return acc


def kpke_keygen(p, d):
    k = p['k']
    rho, sigma = G(d + bytes([k]))
    a_hat = gen_matrix(k, rho)
    s = [sample_cbd(p['eta1'], PRF(p['eta1'], sigma, i)) for i in range(k)]
    e = [sample_cbd(p['eta1'], PRF(p['eta1'], sigma, k + i)) for i in range(k)]
    s_hat = [ntt(x) for x in s]
    e_hat = [ntt(x) for x in e]
    t_hat = [poly_add(dot(a_hat[i], s_hat), e_hat[i]) for i in range(k)]
    ek = b''.join(byte_encode(12, x) for x in t_hat) + rho
    dk = b''.join(byte_encode(12, x) for x in s_hat)
    return ek, dk


def kpke_encrypt(p, ek, m, r):
    k = p['k']
    t_hat = [byte_decode(12, ek[384 * i:384 * (i + 1)]) for i in range(k)]
    rho = ek[384 * k:384 * k + 32]
    a_hat = gen_matrix(k, rho)
    y = [sample_cbd(p['eta1'], PRF(p['eta1'], r, i)) for i in range(k)]
    e1 = [sample_cbd(p['eta2'], PRF(p['eta2'], r, k + i)) for i in range(k)]
    e2 = sample_cbd(p['eta2'], PRF(p['eta2'], r, 2 * k))
    y_hat = [ntt(x) for x in y]
    u = [poly_add(ntt_inv(dot([a_hat[j][i] for j in range(k)], y_hat)), e1[i]) for i in range(k)]
    mu = decompress(1, byte_decode(1, m))
    v = poly_add(poly_add(ntt_inv(dot(t_hat, y_hat)), e2), mu)
    c1 = b''.join(byte_encode(p['du'], compress(p['du'], x)) for x in u)
    c2 = byte_encode(p['dv'], compress(p['dv'], v))
    return c1 + c2


def kpke_decrypt(p, dk, c):
    k = p['k']
    du = p['du']
    dv = p['dv']
    c1 = c[:32 * du * k]
    c2 = c[32 * du * k:]
    u = [decompress(du, byte_decode(du, c1[32 * du * i:32 * du * (i + 1)])) for i in range(k)]
    v = decompress(dv, byte_decode(dv, c2))
    s_hat = [byte_decode(12, dk[384 * i:384 * (i + 1)]) for i in range(k)]
    w = poly_sub(v, ntt_inv(dot(s_hat, [ntt(x) for x in u])))
    return byte_encode(1, compress(1, w))


def keygen(pset, seed):
    p = PARAMS[pset]
    d, z = seed[:32], seed[32:]
    ek, dk_pke = kpke_keygen(p, d)
    return ek, dk_pke + ek + H(ek) + z


def encaps(pset, ek, m):
    p = PARAMS[pset]
    K, r = G(m + H(ek))
    return kpke_encrypt(p, ek, m, r), K


def decaps(pset, dk, c):
    p = PARAMS[pset]
    k = p['k']
    dk_pke = dk[:384 * k]
    ek = dk[384 * k:768 * k + 32]
    h = dk[768 * k + 32:768 * k + 64]
    z = dk[768 * k + 64:768 * k + 96]
    m = kpke_decrypt(p, dk_pke, c)
    K, r = G(m + h)
    K_bar = J(z + c)
    if c != kpke_encrypt(p, ek, m, r):
        return K_bar
    return K


def sha256(b):
    return hashlib.sha256(b).digest()


# wolfSSL ML-KEM known answer tests (wolfcrypt/test/test.c, mlkem*_kat):
# keygen random (d || z), encapsulation random (m), then SHA-256 of ek, dk, c and the shared secret
KATS = {
    512: {
        'keygen_seed': '7c9935a0b07694aa0c6d10e4db6b1add2fd81a25ccb148032dcd739936737f2d8626ed79d451140800e03b59b956f8210e556067407d13dc90fa9e8b872bfb8f',
        'encaps_seed': '147c03f7a5bebba406c8fae1874d7f13c80efe79a3a9a874cc09fe76f6997615',
        'pk_sha256': '852523749efd2b78d1074e5de629060312cd9397933a19ddb7482cfda5e92614',
        'sk_sha256': '937a781daf1928b86a64f69dada5feff8b8ade060f298d187090a46c0d205cb7',
        'ct_sha256': 'bc29d7df8bc5465d980601d800259793e2603825a572da6cd198a512cc6d1a34',
        'ss': '319839e82ab6b222de7b619e80da8391522bbb37677018494a4742c53f9abfdf',
    },
    768: {
        'keygen_seed': '7c9935a0b07694aa0c6d10e4db6b1add2fd81a25ccb148032dcd739936737f2d8626ed79d451140800e03b59b956f8210e556067407d13dc90fa9e8b872bfb8f',
        'encaps_seed': '147c03f7a5bebba406c8fae1874d7f13c80efe79a3a9a874cc09fe76f6997615',
        'pk_sha256': '86adbca81f4fee893e2fb58fb98aa2fe188f501fed268d7f4056f8c05c4e53c4',
        'sk_sha256': '8757e8aee5e441aee07a43af40467d32f80aee5c51aae4ebd2bdb844c038aac7',
        'ct_sha256': '36829a2f35cbf4deb62c0a12a15c22dae9f8d2c252566fc24f88abe805cb575e',
        'ss': 'e7184a0975ee3470878d2d159ec83129c8aec253d4ee17b4810311d198cd0368',
    },
    1024: {
        'keygen_seed': '7c9935a0b07694aa0c6d10e4db6b1add2fd81a25ccb148032dcd739936737f2d8626ed79d451140800e03b59b956f8210e556067407d13dc90fa9e8b872bfb8f',
        'encaps_seed': '147c03f7a5bebba406c8fae1874d7f13c80efe79a3a9a874cc09fe76f6997615',
        'pk_sha256': '61b95ec8c32ae85ad7a17ae5b9c2dfb083e05f767da3ba9a0a8092ea6b4cbf7a',
        'sk_sha256': '926ce3868d8fd192e03410d405e61fb32697a532d7ca7d9ba9b296111df3af74',
        'ct_sha256': '508136a13f8a7920e3434498c6975cbbab457d809309eb2f92453e7409738210',
        'ss': '489dd1e9c2be4af3482bdb35bb26ce760e6e414da6ecbe489985748a825f1cd6',
    },
}


def self_test():
    for pset, kat in KATS.items():
        pk, sk = keygen(pset, bytes.fromhex(kat['keygen_seed']))
        ct, ss = encaps(pset, pk, bytes.fromhex(kat['encaps_seed']))
        assert sha256(pk).hex() == kat['pk_sha256'], f'ML-KEM-{pset} KAT: wrong encapsulation key'
        assert sha256(sk).hex() == kat['sk_sha256'], f'ML-KEM-{pset} KAT: wrong decapsulation key'
        assert sha256(ct).hex() == kat['ct_sha256'], f'ML-KEM-{pset} KAT: wrong ciphertext'
        assert ss.hex() == kat['ss'], f'ML-KEM-{pset} KAT: wrong shared secret'
        assert decaps(pset, sk, ct) == ss, f'ML-KEM-{pset} KAT: decapsulation failed'


def reject_ciphertext(ct):
    # must match the corruption done by libmlkem-lbmk/source/core.c
    return bytes([ct[0] ^ 1]) + ct[1:]


def gen_case(pset, index, slow):
    attempt = 0
    while True:
        seeds = hashlib.shake_256(f'crypto-benchmark ML-KEM-{pset} test case {index} attempt {attempt}'.encode()).digest(96)
        keygen_seed = seeds[:64]
        encaps_seed = seeds[64:]
        XofCounter.max_blocks = 0
        pk, sk = keygen(pset, keygen_seed)
        if (XofCounter.max_blocks > 3) == slow:
            break
        attempt += 1
    ct, ss = encaps(pset, pk, encaps_seed)
    assert decaps(pset, sk, ct) == ss
    ct_reject = reject_ciphertext(ct)
    ss_reject = decaps(pset, sk, ct_reject)
    assert ss_reject == J(keygen_seed[32:] + ct_reject)
    return {
        'keygen_seed': keygen_seed,
        'encaps_seed': encaps_seed,
        'pk_sha256': sha256(pk),
        'sk_sha256': sha256(sk),
        'ct_sha256': sha256(ct),
        'ss': ss,
        'ss_reject': ss_reject,
        'max_xof_blocks': XofCounter.max_blocks,
    }


def c_bytes(b):
    return '{' + ', '.join(f'0x{x:02X}' for x in b) + '}'


FIELDS = ['keygen_seed', 'encaps_seed', 'pk_sha256', 'sk_sha256', 'ct_sha256', 'ss', 'ss_reject']


def gen_c_file(pset, ncases, nslow, outdir):
    cases = [gen_case(pset, i, i >= ncases - nslow) for i in range(ncases)]
    digest = sha256(b''.join(c[f] for c in cases for f in FIELDS))
    name = f'mlkem{pset}-n{ncases}-h{digest[:4].hex().upper()}'
    var = f'mlkem{pset}_n{ncases}'
    out = f'//generated by gen-tv.py, do not edit\n'
    out += f'//types are defined in libmlkem-lbmk/source/core.c\n'
    out += f'static const mlkem_test_case_t {var}_test_cases[{ncases}] = {{\n'
    for i, c in enumerate(cases):
        out += f'{{//case {i}: SampleNTT needed up to {c["max_xof_blocks"]} SHAKE128 blocks\n'
        for f in FIELDS:
            out += f'.{f} = {c_bytes(c[f])},\n'
        out += '},\n'
    out += '};\n'
    out += f'static const mlkem_test_vectors_t {var}_test_vectors = {{\n'
    out += f'.name = "{name}",\n'
    out += f'.mlkem_pset = {pset},\n'
    out += f'.ncases = {ncases},\n'
    out += f'.cases = {var}_test_cases,\n'
    out += '};\n'
    path = os.path.join(outdir, f'{name}.c')
    with open(path, 'w') as f:
        f.write(out)
    return path


if __name__ == '__main__':
    scriptname = os.path.basename(__file__)
    parser = argparse.ArgumentParser(scriptname, description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--pset', default=list(PARAMS.keys()), nargs='+', type=int, choices=PARAMS.keys())
    parser.add_argument('--ncases', default=NCASES, type=int)
    parser.add_argument('--nslow', default=NSLOW, type=int, help='number of cases exercising the slow path of SampleNTT')
    parser.add_argument('--outdir', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'include'))
    args = parser.parse_args()

    self_test()
    print('self test passed')
    for pset in args.pset:
        print(gen_c_file(pset, args.ncases, min(args.nslow, args.ncases), args.outdir))
