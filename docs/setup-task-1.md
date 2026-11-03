# Setup Task 1: WhatsApp, Groq, fallback pencocokan foto

Jalankan PowerShell dari `D:\sigapi`. Instalasi lokal saat ini memakai Node **26.12.1**, OpenClaw dan plugin WhatsApp **2026.10.6**. Tidak perlu mengganti Node global. Belum ada pairing WhatsApp. Groq sudah merespons pada gambar sintetis dan potret publik tanpa api; uji sampel kebakaran/buram belum selesai. SerpApi berhasil mengembalikan exact-match candidates pada potret publik. Vision mengembalikan BILLING_DISABLED; sekarang opsional.

## 1. Buat konfigurasi privat

Gunakan **nomor pengirim tim**, berbeda dari nomor bot. Ganti contoh di bawah dengan nomor sebenarnya, berawalan `+62`.
```powershell
.\.venv\Scripts\python.exe -m backend.cli configure --team-number '+62NOMOR_TIM'
notepad .env
```

Perintah membuat `.env` dengan dua token acak serta konfigurasi OpenClaw privat. Tidak menimpa konfigurasi yang sudah ada. Isi `GROQ_API_KEY`, `GROQ_VISION_MODEL`, dan `SERPAPI_API_KEY`. Biarkan `ENABLE_GOOGLE_VISION=false`; `GOOGLE_CLOUD_PROJECT` hanya diperlukan jika mengaktifkan Vision. Pertahankan kedua token. Jika `.env` sudah dibuat sendiri, pastikan `INTERNAL_API_TOKEN` dan `OPENCLAW_GATEWAY_TOKEN` masing-masing berisi token acak minimal 32 karakter.

Konfigurasi membatasi DM ke nomor tim, menonaktifkan grup dan self-chat. Jangan menambahkan instansi/kanal operasional. `.runtime/openclaw-state` menampung sesi/credential WhatsApp; jangan dibagikan.

## 2. Siapkan Groq

1. Masuk [Groq Console](https://console.groq.com/keys), buat API key. Simpan langsung pada `GROQ_API_KEY` di `.env`.
2. Periksa [Vision](https://console.groq.com/docs/vision) dan model yang tersedia di akun/Playground. Isi ID model vision persis pada `GROQ_VISION_MODEL`; jangan memilih model teks saja.
3. Free Plan mempunyai kuota. Respons 429 dicoba maksimal tiga kali total, jeda 2 lalu 5 detik. Model yang menolak gambar/JSON belum memenuhi gerbang demo.

## 3. Siapkan pencocokan foto web (SerpApi)

1. Daftar akun [SerpApi](https://serpapi.com/), pilih **Free**, lalu buka dashboard/API key. Paket gratis yang ditinjau menyediakan 250 pencarian per bulan, 50 per jam; periksa kembali batas yang tampil saat mendaftar. Jangan memilih upgrade berbayar untuk mengikuti panduan ini.
2. Buka `.env` lokal dan isi `SERPAPI_API_KEY`. Jangan kirim key ke chat. `GROQ_API_KEY` tetap dipakai untuk observasi gambar; kedua layanan mempunyai tugas berbeda.
3. Pertahankan `ENABLE_GOOGLE_VISION=false`. Billing Google tidak diperlukan untuk jalur SerpApi. Jika belum memiliki key SerpApi, pemeriksaan tetap disimpan sebagai `manual_review: pending` dan `hold_public: true`.

Alur: periksa duplikat lokal SHA-256/dHash, lalu SerpApi Google Lens exact matches, lalu visual matches jika exact kosong. **Google Vision hanya dicoba ketika SerpApi tidak tersedia dan flag Vision aktif.** Temuan konflik menghentikan fallback dan perlu klarifikasi. Gagal semua layanan web meminta pemeriksaan manual melalui Google Lens/TinEye browser; belum ada input penyelesaian review manual di Task 1. Pemeriksaan lokal hanya mencakup koleksi uji operator, bukan seluruh internet.

Foto turunan JPEG tanpa EXIF diunggah ke SerpApi melalui [Image API](https://serpapi.com/image-api); aplikasi tidak membuat URL publik untuk media. SerpApi menerima data gambar sebagai pihak ketiga: gunakan media demo berizin. [Lens upload](https://serpapi.com/google-lens-upload-an-image), [exact matches](https://serpapi.com/google-lens-exact-matches-api), [pricing](https://serpapi.com/pricing).

Aplikasi membatasi SerpApi ke **50 operasi HTTP**, termasuk upload dan retry, persisten di `.runtime/serpapi-budget.sqlite3`. Batas ini lebih ketat daripada hitungan kredit vendor; satu gambar baru umumnya memakai 2?3 operasi. Hasil sukses di-cache per hash/versi, kegagalan tidak di-cache. Jangan menghapus database untuk mengulang kuota. Vision tetap memiliki database/batas sendiri.

### Opsional: Google Cloud Vision

Langkah berikut hanya untuk mengaktifkan cadangan Google. Bila siap menerima billing Google, ubah `ENABLE_GOOGLE_VISION=true`; aplikasi tidak mengaktifkan API/billing otomatis.


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

Backend memakai API resmi `images:annotate`, autentikasi `google-auth`, fitur `WEB_DETECTION`. Batas aplikasi **50 percobaan** tersimpan di `.runtime/vision-budget.sqlite3`, termasuk retry. Jangan menghapus berkas ini untuk mengulang kuota. Satu video dapat memakai sampai tiga request Vision baru. Cache satu hasil sukses per hash/versi. Pemakaian project dari aplikasi lain tidak dibatasi mekanisme ini. [Harga Vision](https://cloud.google.com/vision/pricing).

## 4. Jalankan backend dan pairing WhatsApp

Terminal pertama:

```powershell
.\.venv\Scripts\python.exe -m backend.cli readiness
.\.venv\Scripts\python.exe -m backend.cli serve
```

Jika memakai FFmpeg lokal, tambahkan `.runtime/ffmpeg/bin` ke PATH terminal ini sebelum menjalankan readiness. Readiness konfigurasi saja belum meluluskan Task 1. Backend hanya listen `127.0.0.1:8011`, tanpa dokumentasi publik atau access log. Endpoint memerlukan token lokal. **Jangan meneruskan port ini ke tunnel.**

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
.\.venv\Scripts\python.exe -m backend.cli providers --image '.runtime/media/pernah-di-web.jpg' --case web_known --provider web
.\.venv\Scripts\python.exe -m backend.cli providers --image '.runtime/media/video.mp4' --case video
```

Video memerlukan **FFmpeg dan FFprobe** di PATH, keduanya dari [distribusi yang ditautkan FFmpeg](https://ffmpeg.org/download.html#build-windows). Pada workspace ini keduanya sudah terpasang lokal versi 9.0.2, dari [rilis GitHub resmi Gyan](https://github.com/GyanD/codexffmpeg/releases/tag/9.0.2); checksum SHA-256 arsip diverifikasi sebelum ekstraksi. PATH sistem tidak diubah. Setelah ekstraksi build Windows, tambahkan direktori `bin` hanya pada terminal demo, misalnya `$env:PATH='D:\sigapi\.runtime\ffmpeg\bin;' + $env:PATH`. Periksa `ffmpeg -version` dan `ffprobe -version`. Foto maksimal 10 MB, video 20 MB/30 detik. Decoder mengambil maksimal tiga frame awal/tengah/akhir; tidak mengklaim memahami seluruh video.

Hasil provider nyata tersimpan privat di `.runtime/smoke-*.json`, berisi waktu, model dan observasi; hasil pencocokan membawa hash, versi, URL dan jenis kecocokan. `--provider both` (default) menjalankan Groq + fallback web; `web` hanya fallback web; `serpapi` hanya layanan SerpApi beserta indeks lokal; `vision` hanya Vision beserta indeks lokal dan tetap memerlukan flag aktif. Jika provider unavailable, hasil tetap disimpan tetapi exit code 1. Ini bukan hasil validasi laporan final. Label `--case` berasal dari operator, bukan evaluasi otomatis. Periksa sendiri bahwa output JSON valid dan observasinya sesuai sampel. No-match tidak berarti foto asli; full/partial match memerlukan klarifikasi, bukan otomatis laporan palsu.

## 6. Gerbang Task 1

Task 1 baru selesai setelah seluruhnya terbukti:

- Konfigurasi/plugin valid, pairing sukses, empat jenis input WhatsApp diterima dan dibalas tanpa agent kedua.
- Tiga sampel Groq menghasilkan observasi JSON yang sesuai dan ID model tercatat.
- Minimal satu layanan pencocokan web nyata (SerpApi atau Vision yang diaktifkan) berjalan pada foto yang diketahui pernah ada di web; hasil apa adanya, termasuk no-match. Fixture, duplikat lokal dan manual pending tidak meluluskan gerbang ini.
- Video nyata terdekode; batas ukuran/durasi berjalan.
- Unit tests lulus. Nomor, credential, QR, media dan hasil privat tidak masuk Git.

Saat akun siap, cukup beri status **“Groq dan SerpApi siap”**; tidak perlu membagikan key/token/QR. Pairing harus dilakukan melalui terminal lokal. Task 2 menunggu bukti koneksi tersebut.

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

## Bukti koneksi nyata ? 23 Oktober 2026

SerpApi dan Groq berhasil dijalankan pada potret Grace Hopper (foto US Navy, domain publik), diambil dari [sample data Matplotlib](https://raw.githubusercontent.com/matplotlib/matplotlib/main/lib/matplotlib/mpl-data/sample_data/grace_hopper.jpg). SerpApi memberikan 100 referensi kandidat exact match (hasil disimpan maksimal 100), outcome `conflict_candidate` dan `hold_public=true`. Ini kandidat kecocokan, bukan pembuktian laporan palsu atau umur kejadian. Hanya 2 operasi HTTP SerpApi terpakai: upload dan exact search. Pemanggilan ulang memakai cache.

Groq mengembalikan JSON schema-valid dengan `fire_visible=false` dan `smoke_visible=false`. Rincian deskripsi model masih dapat keliru; hasil ini hanya membuktikan koneksi dan observasi utama pada satu potret, bukan akurasi kebakaran. Hasil privat di `.runtime/smoke-ab627ef21b3105c5.json` (web) dan `.runtime/smoke-6e0a213f0bf25e31.json` (Groq + web). Google Vision tidak dipanggil.

Task 1 masih menunggu pairing/input WhatsApp nyata, sampel api/buram, serta FFmpeg/FFprobe dan uji video. Jangan mulai Task 2 sebelum gerbang lengkap.

## Jika pesan masuk tetapi muncul error autentikasi OpenAI

Pada OpenClaw 2026.10.6, plugin bridge harus menyatakan `activation.onStartup=true` di `openclaw.plugin.json`; manifest sudah diperbaiki. Tanpa deklarasi ini, plugin dapat tampil enabled di inventory tetapi tidak dimuat gateway, sehingga pesan jatuh ke agent bawaan. Jangan menambahkan key OpenAI untuk mengatasi kesalahan routing ini.

Restart gateway setelah perubahan manifest, pertahankan backend berjalan, lalu tunggu listener WhatsApp dan kirim ulang teks. Pemeriksaan runtime:

```powershell
.\.venv\Scripts\python.exe -m backend.cli openclaw -- plugins inspect sigapi-validation-demo --runtime --json
```

Hasil harus mencatat `imported=true`, `hookCount=2`, serta typed hooks `message_received` dan `before_dispatch`. Ini bukti pemuatan pada proses inspeksi; balasan WhatsApp `[UJI]` tetap harus dibuktikan setelah restart gateway.

### Balasan UJI layanan belum siap meskipun backend aktif

Plugin mengorelasikan DM menggunakan channel, account, sender dan provider message ID. Pada SDK terpasang, conversation ID di `message_received` dapat berbeda dari `before_dispatch`; percakapan penerimaan dipertahankan untuk backend. Perbaikan ini memerlukan restart gateway. Jika masih gagal, log `[sigapi]` membedakan `FACTS_NOT_FOUND`, `BACKEND_HTTP_<status>`, `INVALID_BACKEND_RESULT`, dan `BACKEND_REQUEST_FAILED` tanpa merekam isi pesan atau secret.

## Sampel pengguna dan uji kualitas

Foto yang oleh operator dinyatakan menampilkan kebakaran hutan diuji nyata melalui Groq dan SerpApi. Groq: api/asap terlihat, kualitas clear. SerpApi: kandidat exact match di web (100 referensi disimpan sebagai batas maksimum), sehingga hasil evidence menahan publikasi. Kandidat ini memerlukan peninjauan sumber/klarifikasi waktu dan asal foto; belum membuktikan laporan palsu. Bukti privat: `.runtime/smoke-f63626e414e654fa.json`.

Turunan yang sengaja diturunkan menjadi 8x8 piksel lalu diperbesar/diburamkan diuji terpisah: Groq memberi unclear, tanpa api/asap yang dapat terlihat. Ini uji degradasi buatan, bukan foto lapangan independen. Bukti privat: `.runtime/smoke-10f89210dbd0a66c.json`. Detail narasi model masih bisa keliru, sehingga hasil tiga sampel bukan benchmark akurasi.

Video pengguna dinyatakan tanpa kaitan dengan api/asap. Titik lokasi yang dikirim terpisah tidak otomatis menjadi lokasi kejadian terkonfirmasi atau membuktikan lokasi foto/video; percakapan kelengkapan/konfirmasi baru diterapkan pada Task 2.

### Batas Groq Free pada video

CLI memberi jeda 35 detik sebelum frame kedua dan ketiga. Tiga frame membutuhkan sekitar 70 detik jeda ditambah waktu request; pengujian awal tanpa jeda mendapat 429 pada frame ketiga, sehingga tidak dinyatakan lolos. Pembatasan ini hanya untuk satu proses smoke; pemakaian akun/proses lain tetap dapat menghabiskan kuota. Retry tetap maksimal tiga percobaan per operasi, dan gagal tetap unavailable.

### Hasil video nyata

Video yang dikirim operator berdurasi 2,900211 detik berhasil didekode menjadi tiga frame awal/tengah/akhir dengan FFmpeg/FFprobe lokal 9.0.2. Setelah jeda antar-frame diterapkan, ketiga panggilan Groq merespons JSON valid: fire_visible=false, smoke_visible=false, image_quality=clear. Ini sesuai deskripsi operator bahwa video tidak terkait api/asap. Bukti privat `.runtime/smoke-c315098bae31cc4f.json`; percobaan awal dengan frame ketiga HTTP429 tetap tersimpan terpisah di `.runtime/smoke-e6898644a1b4ad5b.json`.

Readiness menghasilkan seluruh komponen true ketika direktori lokal FFmpeg disertakan:

```powershell
$env:PATH = (Join-Path $PWD '.runtime/ffmpeg/bin') + ';' + $env:PATH
.\.venv\Scripts\python.exe -m backend.cli readiness
```

Decoder/provider smoke ini dipicu operator melalui CLI menggunakan berkas yang sudah diterima WhatsApp. Bot WhatsApp masih memberi balasan UJI metadata; analisis otomatis, penyimpanan laporan dan keputusan distribusi belum diterapkan.
