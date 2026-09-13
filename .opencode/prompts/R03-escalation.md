# R03 — RETRY & ESCALATION: protokol saat mentok di bawah 100

Dipakai ketika satu tahap gagal 3x berturut-turut atau skor mentok di
angka yang sama 2x berturut-turut. Tujuan: mentok itu data, bukan vonis.

## Siklus retry (maks 3x per tahap)
1. Tulis akar masalah dalam 1 kalimat + bukti yang menunjukkannya.
2. Kecilkan masalah: belah item gagal jadi 2-3 sub-item yang masing-masing
   bisa diuji sendiri dalam < 30 menit.
3. Coba pendekatan alternatif (minimal 1 alternatif berbeda dicoba dan
   dicatat hasilnya, termasuk yang gagal — kegagalan tercatat = data).
4. Bila masih gagal setelah 3x: NAIK ke eskalasi, jangan putaran ke-4.

## Eskalasi ke Tuan (format wajib, bukan keluhan bebas)
- Fakta: apa yang dicoba (3x) + output tiap percobaan.
- Diagnosis: akar masalah menurut bukti.
- Opsi A/B (+rekomendasi Anda yang mana + kenapa).
- Dampak tiap opsi ke skor dan ke dimensi lain.
- Tanpa format ini = belum boleh bertanya. Kembali bekerja.

## Aturan tambahan
- Dilarang menurunkan target diam-diam agar "lolos".
- Dilarang melewati dimensi ("nanti kembali") — tidak pernah kembali.
  Selesaikan di sini, sekarang.
- Istirahat Frost: bila 2 dimensi berturut-turut butuh eskalasi,
  hentikan misi 1 hari, tulis postmortem 10 baris, baru lanjut.
  Kelelahan yang dipaksa = bug yang diproduksi.
