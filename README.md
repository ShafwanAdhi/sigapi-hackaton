# SIGAPI — demo verifikasi Karhutla

Implementasi **Task 1 sedang berjalan**. Belum ada laporan persisten, routing, form publik atau TRACK. Task 2–5 menunggu koneksi WhatsApp/Groq/Vision nyata lolos sesuai [rencana](docs/superpowers/plans/2026-10-22-validation-demo-implementation.md).

Tersedia: endpoint FastAPI privat, takeover plugin OpenClaw, pemeriksaan Groq/Web Detection, batas persisten 50 request Vision, cache hasil, validasi gambar dan sampling video. Smoke WhatsApp hanya membalas `[UJI]`; pesan belum disimpan sebagai laporan.

## Setup akun dan menjalankan smoke

Ikuti [panduan Task 1](docs/setup-task-1.md). Key, sesi WhatsApp, konfigurasi nomor, hasil provider dan media tetap lokal di `.env`/`.runtime`, diabaikan Git. Jangan mengunggah `.runtime` atau mengirim QR/key ke chat.

## Pemeriksaan lokal

```powershell
Set-Location D:\sigapi
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.runtime\node\package\bin\node.exe --test --test-isolation=none openclaw-plugin/index.test.js
.\.runtime\node\package\bin\node.exe --check openclaw-plugin/index.js
.\.venv\Scripts\python.exe -m backend.cli readiness
```

Unit tests memakai transport provider tiruan. Hasilnya tidak membuktikan koneksi akun atau pengiriman WhatsApp. `readiness` memeriksa keberadaan konfigurasi/komponen, bukan keberhasilan analisis nyata.

Pilihan minimum Task 1: plugin JavaScript memakai SDK hooks yang tersedia; Vision memakai REST resmi + `google-auth`; kuota smoke memakai SQLite lokal. Intake persisten PostgreSQL dan spool mulai Task 2. FFmpeg/FFprobe belum terpasang; unduhan awal dihentikan karena koneksi lambat.
