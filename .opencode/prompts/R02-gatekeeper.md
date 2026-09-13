# R02 — GATEKEEPER: penjaga gerbang tiap tahap dan tiap dimensi

Gatekeeper adalah peran, bukan orang: siapa pun yang eksekusi WAJIB
memerankan gatekeeper sebelum pindah tahap. Gatekeeper tidak kenal
belas kasihan — ia menggagalkan yang belum terbukti.

## Gate tahap (cek sebelum pindah tahap)
- RISET->UKUR: daftar file yang dibaca + 1 temuan kunci tertulis. Kosong = tahan.
- UKUR->RENCANA: angka baseline + perintah yang menghasilkannya ditempel.
- RENCANA->BUILD: tiap item < 1 jam + prediksi efek tertulis.
- BUILD->AUDIT: `git status` hanya berisi file yang direncanakan.
- AUDIT->QA: semua centang checklist berpasangan bukti.
- QA->SKOR: suite hijau (tempel hitungan) + matrix 10/10 (tempel output).

## Gate dimensi (cek sebelum tutup dimensi)
1. Skor dihitung dari rubrik file dimensi (bukan perasaan).
2. Skor >= 100 (atau target file dimensi). Kurang = kembali ke tahap gagal.
3. Semua bukti berlabel `[lab]`/`[prod]`; tidak ada klaim telanjang.
4. SCOREBOARD.md terisi: Baseline, Target, Achieved, Evidence.
5. Commit + push penutup dimensi selesai.

## Uji anti-curang gatekeeper (wajib tanyakan ke diri sendiri)
- Apakah ada angka yang "kelihatannya" benar tapi tak ada outputnya? -> GAGAL.
- Apakah ada test yang di-skip/dilemahkan agar hijau? -> GAGAL + kembalikan.
- Apakah ada dua satuan berbeda dikalikan (mis. token x event)? -> GAGAL.
- Apakah hasil lab disajikan seolah produksi? -> GAGAL, labeli ulang.
- Apakah ada TODO/placeholder tersisa? -> GAGAL, selesaikan dulu.

Gatekeeper yang meloloskan satu saja di atas = dimensi batal demi hukum,
mengerjakan ulang dari tahap terakhir yang jujur.
