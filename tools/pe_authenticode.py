"""Verify a PE file against its embedded Authenticode signature.

Usage: python3 -I tools/pe_authenticode.py <file.exe>

Steps (each printed with its result):
  1. Authenticode image digest: SHA-1 and SHA-256 of the file minus the CheckSum field, the
     Security directory entry and the certificate table. Look for it inside SpcIndirectDataContent.
  2. The signer's messageDigest attribute must equal the SHA-1 of SpcIndirectDataContent's body.
  3. RSA check of the signed attributes against the signer certificate (openssl dgst -verify).
  4. Signer chain check against the system trust store at the PE timestamp (openssl verify
     -attime; anchors from `trust extract`). Being able to verify an expired certificate at
     signing time is enough here: we only need to know who signed it, not whether it is valid today.
  5. Recompute the PE optional-header CheckSum.
Parsing is stdlib only. Steps 3-4 shell out to openssl and p11-kit `trust`. Temp files go in a
tempdir. Exits 0 only if steps 1-3 pass.
"""
import hashlib
import os
import struct
import subprocess
import sys
import tempfile


def tlv(b, o):
    l, h = b[o + 1], 2
    if l & 0x80:
        n = l & 0x7F
        l, h = int.from_bytes(b[o + 2:o + 2 + n], "big"), 2 + n
    return (o, h, l)  # start, header length, content length


def kids(b, k):
    s, h, l = k
    p, out = s + h, []
    while p < s + h + l:
        c = tlv(b, p)
        out.append(c)
        p = c[0] + c[1] + c[2]
    return out


def body(b, k):
    return b[k[0] + k[1]:k[0] + k[1] + k[2]]


def whole(b, k):
    return b[k[0]:k[0] + k[1] + k[2]]


def pem(der, label="CERTIFICATE"):
    import base64
    t = base64.encodebytes(der).decode().replace("\n", "")
    return "-----BEGIN %s-----\n%s\n-----END %s-----\n" % (
        label, "\n".join(t[i:i + 64] for i in range(0, len(t), 64)), label)


def main(argv):
    if len(argv) != 1:
        print(__doc__)
        return 2
    data = open(argv[0], "rb").read()
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    ts = struct.unpack_from("<I", data, pe + 8)[0]
    opt = pe + 24
    cks_off = opt + 64
    sec_dir = opt + 96 + 8 * 4  # IMAGE_DIRECTORY_ENTRY_SECURITY (PE32)
    cert_off, cert_len = struct.unpack_from("<II", data, sec_dir)
    if not cert_off:
        print("no certificate table")
        return 1
    rev, ctype = struct.unpack_from("<HH", data, cert_off + 4)
    print("certificate table: offset=%#x len=%d revision=%#x type=%#x" % (cert_off, cert_len, rev, ctype))
    raw = data[cert_off + 8:cert_off + cert_len]
    p7 = whole(raw, tlv(raw, 0))  # drop 8-byte alignment padding

    # 1. image digest
    pieces = [data[:cks_off], data[cks_off + 4:sec_dir], data[sec_dir + 8:cert_off],
              data[cert_off + cert_len:]]
    ci = kids(p7, tlv(p7, 0))
    sd = kids(p7, kids(p7, ci[1])[0])  # ContentInfo [0] -> SignedData
    spc = kids(p7, kids(p7, sd[2])[1])[0]  # encapContentInfo [0] -> SpcIndirectDataContent
    spc_body = body(p7, spc)
    ok1 = False
    for name in ("sha1", "sha256"):
        h = hashlib.new(name)
        for p in pieces:
            h.update(p)
        hit = h.digest() in spc_body
        ok1 |= hit
        print("1. image digest %-6s %s  in-SpcIndirectData=%s" % (name, h.hexdigest(), hit))

    # 2. messageDigest attribute
    si = kids(p7, kids(p7, sd[-1])[0])
    attrs = next(k for k in si if p7[k[0]] == 0xA0)
    sig = body(p7, next(k for k in si if p7[k[0]] == 0x04))
    md = None
    for a in kids(p7, attrs):
        ak = kids(p7, a)
        if body(p7, ak[0]) == bytes.fromhex("2a864886f70d010904"):
            md = body(p7, kids(p7, ak[1])[0])
    ok2 = md == hashlib.sha1(spc_body).digest()
    print("2. messageDigest == sha1(SpcIndirectData) : %s" % ok2)

    # certificates: [0] IMPLICIT in SignedData
    certs_k = next(k for k in sd if p7[k[0]] == 0xA0)
    certs = [whole(p7, c) for c in kids(p7, certs_k)]
    with tempfile.TemporaryDirectory() as td:
        def w(name, content, mode="w"):
            path = os.path.join(td, name)
            with open(path, mode) as f:
                f.write(content)
            return path
        sa = bytearray(whole(p7, attrs))
        sa[0] = 0x31  # signed attributes are signed as a SET
        sa_p, sig_p = w("sa.der", bytes(sa), "wb"), w("sig.bin", sig, "wb")
        ok3, signer = False, None
        for i, c in enumerate(certs):
            cp = w("c%d.pem" % i, pem(c))
            pub = subprocess.run(["openssl", "x509", "-in", cp, "-pubkey", "-noout"],
                                 capture_output=True, text=True).stdout
            pp = w("p%d.pem" % i, pub)
            r = subprocess.run(["openssl", "dgst", "-sha1", "-verify", pp, "-signature", sig_p, sa_p],
                               capture_output=True, text=True)
            if r.returncode == 0:
                ok3, signer = True, cp
                break
        subj = subprocess.run(["openssl", "x509", "-in", signer, "-noout", "-subject", "-issuer", "-dates"],
                              capture_output=True, text=True).stdout.strip() if signer else "-"
        print("3. RSA signature over signed attributes  : %s" % ok3)
        for line in subj.splitlines():
            print("   signer " + line)

        # 4. chain to system trust store at signing time
        if signer:
            others = w("others.pem", "".join(pem(c) for c in certs))
            roots = os.path.join(td, "roots.pem")
            subprocess.run(["trust", "extract", "--format=pem-bundle", "--filter=certificates", roots],
                           capture_output=True)
            r = subprocess.run(["openssl", "verify", "-CAfile", roots, "-attime", str(ts), "-purpose", "any",
                                "-untrusted", others, signer], capture_output=True, text=True)
            print("4. chain to system trust at %d        : %s" % (ts, (r.stdout + r.stderr).strip().splitlines()[-1]))

    # 5. PE checksum
    stored = struct.unpack_from("<I", data, cks_off)[0]
    s = 0
    buf = data + (b"\0" if len(data) % 2 else b"")
    for i in range(0, len(buf), 2):
        if i in (cks_off, cks_off + 2):
            continue
        s += buf[i] | (buf[i + 1] << 8)
        s = (s & 0xFFFF) + (s >> 16)
    calc = ((s & 0xFFFF) + (s >> 16)) + len(data)
    print("5. pe checksum stored=%#x computed=%#x match=%s" % (stored, calc, stored == calc))
    ok = ok1 and ok2 and ok3
    print("VERDICT: %s" % ("UNMODIFIED since signing (signature valid)" if ok else "NOT VERIFIED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
