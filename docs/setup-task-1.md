# Setup Task 1: WhatsApp, Groq, Google Vision

Jalankan PowerShell dari `D:\sigapi`. Instalasi lokal saat ini memakai Node **26.12.1**, OpenClaw dan plugin WhatsApp **2026.10.6**. Tidak perlu mengganti Node global. Belum ada pairing atau uji provider nyata.

## 1. Buat konfigurasi privat

Gunakan **nomor pengirim tim**, berbeda dari nomor bot. Ganti contoh di bawah dengan nomor sebenarnya, berawalan `+62`.

```powershell
.\.venv\Scripts\python.exe -m backend.cli configure --team-number '+62NOMOR_TIM'
notepad .env
```

Perintah membuat `.env` dengan dua token acak serta konfigurasi OpenClaw privat. Tidak menimpa konfigurasi yang sudah ada. Isi `GROQ_API_KEY`, `GROQ_VISION_MODEL`, `GOOGLE_CLOUD_PROJECT`. Pertahankan kedua token. Jika `.env` sudah dibuat sendiri, pastikan `INTERNAL_API_TOKEN` dan `OPENCLAW_GATEWAY_TOKEN` masing-masing berisi token acak minimal 32 karakter.

Konfigurasi membatasi DM ke nomor tim, menonaktifkan grup dan self-chat. Jangan menambahkan instansi/kanal operasional. `.runtime/openclaw-state` menampung sesi/credential WhatsApp; jangan dibagikan.

## 2. Siapkan Groq

1. Masuk [Groq Console](https://console.groq.com/keys), buat API key. Simpan langsung pada `GROQ_API_KEY` di `.env`.
2. Periksa [Vision](https://console.groq.com/docs/vision) dan model yang tersedia di akun/Playground. Isi ID model vision persis pada `GROQ_VISION_MODEL`; jangan memilih model teks saja.
3. Free Plan mempunyai kuota. Respons 429 dicoba maksimal tiga kali total, jeda 2 lalu 5 detik. Model yang menolak gambar/JSON belum memenuhi gerbang demo.

## 3. Siapkan Google Cloud Vision

1. Masuk [Google Cloud Console](https://console.cloud.google.com/). Pilih/buat project khusus demo. Catat **Project ID**, bukan nama tampilannya, ke `GOOGLE_CLOUD_PROJECT` di `.env`.
2. Buka **Billing**, tautkan billing account project. Aktivasi billing dilakukan sendiri pada akunmu. Buat budget alert sebagai pengingat; alert bukan batas biaya keras.
3. Buka **APIs & Services → Library → Cloud Vision API → Enable**. [Halaman API](https://console.cloud.google.com/apis/library/vision.googleapis.com).
4. Instal [Google Cloud CLI untuk Windows](https://cloud.google.com/sdk/docs/install#windows), buka PowerShell baru. Jalankan berurutan, mengganti `PROJECT_ID`:

```powershell
gcloud auth login
gcloud config set project PROJECT_ID
gcloud services enable vision.googleapis.com --project PROJECT_ID
gcloud auth application-default login
gcloud auth application-default set-quota-project PROJECT_ID
```

Login browser dilakukan langsung di perangkatmu. ADC tersimpan di profil Google Cloud lokal; tidak perlu membuat service-account key JSON. Bila akses ditolak, akun memerlukan izin memakai API/quota project, termasuk `serviceusage.services.use`. Jangan mengatasi error dengan memberikan role Owner ke aplikasi.

Backend memakai API resmi `images:annotate`, autentikasi `google-auth`, fitur `WEB_DETECTION`. Batas aplikasi **50 percobaan** tersimpan di `.runtime/vision-budget.sqlite3`, termasuk retry. Jangan menghapus berkas ini untuk mengulang kuota. Satu video dapat memakai sampai tiga request baru. Cache satu hasil sukses per hash/versi. Pemakaian project dari aplikasi lain tidak dibatasi mekanisme ini. [Harga Vision](https://cloud.google.com/vision/pricing).

## 4. Jalankan backend dan pairing WhatsApp

Terminal pertama:

```powershell
.\.venv\Scripts\python.exe -m backend.cli readiness
.\.venv\Scripts\python.exe -m backend.cli serve
```

Readiness boleh masih gagal bila FFmpeg belum tersedia; jangan menyebut Task 1 lulus. Backend hanya listen `127.0.0.1:8011`, tanpa dokumentasi publik atau access log. Endpoint memerlukan token lokal. **Jangan meneruskan port ini ke tunnel.**

Terminal kedua, cek konfigurasi dahulu, lalu pairing:

```powershell
.\.venv\Scripts\python.exe -m backend.cli openclaw -- config validate
.\.venv\Scripts\python.exe -m backend.cli openclaw -- channels login --channel whatsapp
.\.venv\Scripts\python.exe -m backend.cli openclaw -- gateway run
```

Pindai QR pada layar lokal melalui WhatsApp nomor bot: **Perangkat tertaut → Tautkan perangkat**. Jangan kirim QR ke chat. Dari nomor tim, kirim teks, foto berizin, video pendek, lalu lokasi native WhatsApp. Balasan harus tepat satu `[UJI]`, jumlah media/lokasi sesuai input. Tidak ada agent model kedua. Hentikan backend sementara dan kirim pesan: balasan harus menyatakan belum tersimpan, tanpa mengarang penerimaan laporan. Saat selesai, `Ctrl+C` pada kedua terminal.

Plugin smoke mengorelasikan metadata media/lokasi dalam memori selama lima menit. Belum mengirim file ke backend, belum recovery setelah restart. Spool persisten dan receipt 202 baru diperkenalkan pada Task 2. Lokasi native diterima sebagai input; belum merupakan koordinat kejadian terkonfirmasi.

## 5. Uji provider dengan media berizin

Simpan media lokal di `.runtime/media/`. Siapkan foto api, tanpa api, buram, foto yang diketahui pernah ada di web, serta video maksimal 30 detik. Jangan gunakan media warga tanpa izin.

```powershell
.\.venv\Scripts\python.exe -m backend.cli providers --image '.runtime/media/api.jpg' --case fire
.\.venv\Scripts\python.exe -m backend.cli providers --image '.runtime/media/tanpa-api.jpg' --case no_fire --provider groq
.\.venv\Scripts\python.exe -m backend.cli providers --image '.runtime/media/buram.jpg' --case blurred --provider groq
.\.venv\Scripts\python.exe -m backend.cli providers --image '.runtime/media/pernah-di-web.jpg' --case web_known --provider vision
.\.venv\Scripts\python.exe -m backend.cli providers --image '.runtime/media/video.mp4' --case video
```

Video memerlukan **FFmpeg dan FFprobe** di PATH, keduanya dari [distribusi yang ditautkan FFmpeg](https://ffmpeg.org/download.html#build-windows). Keduanya belum terpasang: unduhan awal dihentikan karena koneksi lambat. Setelah ekstraksi build Windows, tambahkan direktori `bin` hanya pada terminal demo, misalnya `$env:PATH='D:\sigapi\.runtime\ffmpeg\bin;' + $env:PATH`. Periksa `ffmpeg -version` dan `ffprobe -version`. Foto maksimal 10 MB, video 20 MB/30 detik. Decoder mengambil maksimal tiga frame awal/tengah/akhir; tidak mengklaim memahami seluruh video.

Hasil provider nyata tersimpan privat di `.runtime/smoke-*.json`, berisi waktu, model dan observasi; hasil Vision membawa hash, versi, URL dan jenis kecocokan. Label `--case` berasal dari operator, bukan evaluasi otomatis. Periksa sendiri bahwa output JSON valid dan observasinya sesuai sampel. No-match tidak berarti foto asli; full/partial match memerlukan klarifikasi, bukan otomatis laporan palsu.

## 6. Gerbang Task 1

Task 1 baru selesai setelah seluruhnya terbukti:

- Konfigurasi/plugin valid, pairing sukses, empat jenis input WhatsApp diterima dan dibalas tanpa agent kedua.
- Tiga sampel Groq menghasilkan observasi JSON yang sesuai dan ID model tercatat.
- Web Detection nyata berjalan pada foto yang diketahui pernah ada di web; hasil apa adanya, termasuk no-match.
- Video nyata terdekode; batas ukuran/durasi berjalan.
- Unit tests lulus. Nomor, credential, QR, media dan hasil privat tidak masuk Git.

Saat akun siap, cukup beri status **“Groq dan ADC siap”**; tidak perlu membagikan key/token/QR. Pairing harus dilakukan melalui terminal lokal. Task 2 menunggu bukti koneksi tersebut.

## Pemasangan ulang dari checkout baru

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
New-Item -ItemType Directory -Force .runtime/node | Out-Null
npm.cmd pack node-win-x64@26.12.1 --pack-destination .runtime
tar.exe -xf .runtime/node-win-x64-26.12.1.tgz -C .runtime/node
$env:PATH=(Join-Path $PWD '.runtime/node/package/bin') + ';' + $env:PATH
$npmCli=Join-Path (Split-Path (Get-Command npm.cmd).Source) 'node_modules/npm/bin/npm-cli.js'
& .\.runtime\node\package\bin\node.exe $npmCli install --prefix .runtime/openclaw openclaw@2026.10.6 '@openclaw/whatsapp@2026.10.6' --omit=dev --no-audit --no-fund
```

Pastikan setiap perintah sukses sebelum lanjut. `npm.cmd` sistem memakai `node.exe` di sampingnya; instalasi OpenClaw karena itu memanggil `npm-cli.js` lewat Node lokal secara eksplisit. Instalasi sandbox dapat memerlukan izin menjalankan subprocess; `spawn EPERM` bukan tanda OpenClaw siap. Lingkungan sesi awal memakai venv dengan paket Python sistem yang sudah tersedia; checkout baru memasang versi tertera pada venv terisolasi.
