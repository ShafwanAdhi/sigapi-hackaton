# Pilihan Groq Vision — 23 Oktober 2026

Model demo: `qwen/qwen3.8-27b`. Nilai `GROQ_VISION_MODEL` pada `.env` lokal sudah diisi; nilai environment lain dipertahankan.

## Alasan

- Mendukung input gambar dan JSON mode, sesuai observasi api/asap yang divalidasi backend. Keputusan publikasi tetap dibuat aturan kode.
- Tercantum pada Free Plan: batas umum 30 request/menit, 1.000 request/hari, 8.000 token/menit, 200.000 token/hari. Batas organisasi sebenarnya perlu dilihat di console/header; tabel publik bukan jaminan kuota akun.
- Setiap gambar memakai 2.048 token input, ditambah prompt/output. Batas token dapat tercapai lebih dahulu daripada batas request. Tiga frame video berarti tiga analisis pada implementasi saat ini; jangan menganggap 30 request/menit dapat dipakai penuh untuk gambar. Demo perlu diberi jeda; retry 2/5 detik yang ada belum menjamin pulih dari limit per menit.
- Free Plan tidak memerlukan upgrade berbayar untuk uji yang berhasil ini. Jika kelak memakai layanan berbayar, tarif model yang ditampilkan adalah $0,80/juta token input dan $4/juta token output; ini bukan biaya yang dinyatakan terpotong pada uji Free Plan.
- Alternatif vision pada dokumentasi, `meta-models/muse-spark-open`, berstatus limited preview dengan akses melalui kontak penyedia. Bukan pilihan minimum untuk tenggat demo.
- Qwen sendiri masih berlabel Preview. Cocok sebagai kandidat demo, belum menjadi klaim kesiapan produksi atau akurasi kebakaran.

## Bukti akun dan batas uji

- `GET /openai/v1/models` memakai key lokal menghasilkan HTTP 200; `qwen/qwen3.8-27b` tercantum.
- Satu panggilan gambar nyata ke API memakai `backend.providers.groq_observe` berhasil dalam sekitar 0,95 detik. Input berupa gambar putih sintetis 128×128, dibuat lokal; bukan foto warga atau benchmark kebakaran.
- Output lolos schema aplikasi: `fire_visible=false`, `smoke_visible=false`, `image_quality=clear`, observasi berbahasa Indonesia sesuai bidang putih kosong.
- Latensi satu sampel bukan SLA. Uji foto api, tanpa api, buram dan frame video berizin masih diperlukan untuk gerbang Task 1. Keberhasilan ini juga tidak membuktikan Vision Google atau WhatsApp sudah terhubung.
- Key tidak ditulis ke dokumen atau log. Model diatur melalui `.env`, bukan hardcode backend. Kegagalan model tetap unavailable, tidak boleh menjadi lolos validasi.

## Sumber resmi

- [Groq Vision: dukungan gambar dan JSON](https://console.groq.com/docs/vision)
- [Qwen 3.8 27B: status, harga, token gambar](https://console.groq.com/docs/model/qwen/qwen3.8-27b)
- [Groq Free Plan rate limits](https://console.groq.com/docs/rate-limits)

Dokumentasi dan akses akun diperiksa 23 Oktober 2026. Kuota dan ketersediaan model dapat berubah.
