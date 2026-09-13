# R01 — DIMENSION RUNNER: arahan eksekusi satu dimensi sampai skor 100

Gunakan file ini BERSAMA file dimensi (P01..P10). Runner ini mengatur
CARA kerja; file dimensi mengatur APA yang dikerjakan.

## 0. Mekanisme eksekusi per dimensi (wajib berurutan, tidak boleh loncat)
1. **RISET** — baca kode + docs yang dirujuk file dimensi. Tulis temuan
   (maks 10 baris) sebelum menyentuh apa pun.
2. **UKUR BASELINE** — jalankan pengukuran file dimensi DULU, catat angka
   ke SCOREBOARD.md kolom Baseline. Tanpa angka awal = dilarang lanjut.
3. **RENCANA** — tulis daftar fix (maks 7 item) + prediksi efek tiap item.
   Kecilkan sampai tiap item bisa selesai < 1 jam.
4. **BUILD** — kerjakan item satu per satu, commit tiap item selesai.
   Diff minimal; dilarang refactor tak terkait.
5. **AUDIT** — jalankan checklist audit file dimensi, centang satu per satu
   dengan bukti (output perintah yang ditempel, bukan klaim).
6. **QA** — full suite + safety matrix + uji spesifik dimensi.
7. **SKOR** — hitung dari rubrik file dimensi dengan bukti. Tulis ke
   SCOREBOARD.md kolom Achieved + Evidence.

## 1. Aturan tidak-pindah-dimensi (GATE 100)
- Skor < 100 (atau < target file dimensi) = ULANGI dari tahap yang gagal.
  Maksimal 3 putaran perbaikan per tahap (lihat R03 bila mentok).
- Dilarang membuka dimensi berikut sebelum dimensi kini 100.
- Dilarang menurunkan target agar lolos. Target hanya boleh berubah atas
  persetujuan Tuan dengan alasan tertulis di SCOREBOARD.

## 2. Aturan bukti (anti-halusinasi)
- Setiap kata "terverifikasi/lolos/terbukti" wajib ditempeli output asli.
- Angka hanya dari pengukuran (lab) atau produksi (VPS). Labeli tiap
  angka: `[lab]` atau `[prod]`. Angka `[prod]` mengalahkan `[lab]`.
- Klaim tanpa bukti = dimensi GAGAL otomatis.

## 3. Ritme commit
- Satu commit per item build selesai: `dim(Dn): <item> <bukti-singkat>`.
- Satu commit penutup dimensi: `dim(Dn): SCORE <n> + scoreboard`.
- Push tiap commit. Tree tidak pernah merah lebih dari 1 jam.

## 4. Perintah mulai (ucapkan persis saat eksekusi)
"Mulai dimensi Dn. Tahap: RISET. Target skor: 100."
"Tutup dimensi Dn. Skor: <n>. Bukti: <ringkas>. Lanjut/tahan: <keputusan>."
