# SIGAPI — pelaporan kebakaran dan dashboard Admin Kota

Implementasi MVP menambahkan API publik dengan validasi GPS, receipt idempoten,
TRACK milik pengirim, autentikasi admin, konfigurasi penerima PostgreSQL, dan
dashboard React lima menu. Desain publik, logo, serta palet SIGAPI dipertahankan.

Lihat [rencana MVP](docs/superpowers/plans/2026-11-03-public-mvp.md),
[operasional VPS](docs/mvp-operations.md), dan
[sumber panduan keselamatan](docs/safety-sources.md).

**Batas penerimaan:** fresh pairing VPS, dua kontak uji berizin, review batas
wilayah, dan rehearsal menyeluruh tetap harus dibuktikan. Distribusi dan akses
warga umum nonaktif pada konfigurasi awal. Kelulusan tes bukan bukti gate live.

## Catatan integrasi awal (23–24 Oktober 2026)

Ada **5 task berurutan** dalam [rencana implementasi](docs/superpowers/plans/2026-10-22-validation-demo-implementation.md):

1. Koneksi OpenClaw, Groq dan pemeriksaan web: selesai diuji nyata.
2. Intake persisten dan percakapan kelengkapan: selesai; laporan lengkap melalui WhatsApp nyata dan PostgreSQL telah diverifikasi.
3. Pemeriksaan bukti, insiden dan distribusi terkontrol: implementasi tersedia; gate WhatsApp nyata masih pending.
4. Form GPS publik, agregasi konfirmasi dan TRACK.
5. Latihan demo, pemeriksaan akhir dan handoff.

Jalankan versi sekarang mengikuti [panduan Task 3](docs/setup-task-3.md). FastAPI menyimpan input/job ke PostgreSQL; worker analisis terpisah menerima bahasa alami dan memeriksa bukti. Distribusi masih nonaktif sampai dua penerima uji dan tinjauan batas wilayah siap. Izin kontak default tidak diberikan. Kelengkapan, pemeriksaan awal, dan receipt pengiriman tetap terpisah.

Pemeriksaan terhadap Knowledge v3 dan keputusan pengguna pada 24 Oktober tercatat dalam [audit kesesuaian bisnis](docs/audit-knowledge-v3-2026-10-24.md). Teks lokasi hanya untuk klarifikasi; pin/koordinat tetap wajib. EXIF opsional dan ketiadaannya saja tidak menahan laporan. Demo tidak menambahkan pemberitahuan/persetujuan khusus pemrosesan laporan/AI; izin berbagi kontak tetap eksplisit dan opsional. Pemeriksaan konsistensi lintas sumber dan panduan keselamatan belum lengkap. Form GPS dan TRACK masih Task 4.

## Setup provider dan pemeriksaan Task 1

Ikuti [panduan Task 1](docs/setup-task-1.md). Key, sesi WhatsApp, konfigurasi nomor, hasil provider dan media tetap lokal di `.env`/`.runtime`, diabaikan Git. Jangan mengunggah `.runtime` atau mengirim QR/key ke chat.

## Pemeriksaan lokal

```powershell
Set-Location D:\sigapi
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.runtime\node\package\bin\node.exe --test openclaw-plugin/index.test.js openclaw-plugin/intake.test.js
.\.runtime\node\package\bin\node.exe --check openclaw-plugin/index.js
.\.venv\Scripts\python.exe -m backend.cli readiness
```

Tes provider memakai transport tiruan; tes intake memakai TEST_DATABASE_URL terpisah serta HTTP dan Node lokal. Hasilnya tidak membuktikan koneksi akun atau pengiriman WhatsApp. `readiness` memeriksa keberadaan konfigurasi/komponen, bukan keberhasilan analisis nyata.

Pilihan minimum Task 1: plugin JavaScript memakai SDK hooks yang tersedia; SerpApi memakai Image API + Lens; Vision opsional memakai REST resmi + `google-auth`; kuota smoke memakai SQLite lokal. Intake persisten PostgreSQL dan spool tersedia pada Task 2. FFmpeg/FFprobe 9.0.2 tersedia lokal di `.runtime/ffmpeg/bin`; CLI menambahkan direktori itu ke PATH proses untuk video/readiness. Arsip dari rilis resmi Gyan diverifikasi SHA-256.

Perubahan yang disetujui: [rancangan fallback](docs/superpowers/specs/2026-10-23-web-evidence-fallback-design.md). Google Vision mati secara default (`ENABLE_GOOGLE_VISION=false`). Semua layanan web gagal berarti tahan komunitas dan review manual pending; no-match bukan bukti keaslian. Pemeriksaan tersedia pada CLI smoke dan worker laporan Task 3. Uji WhatsApp distribusi nyata belum dilakukan.
