# SIGAPI Public Web

Prototipe interaktif Stage P0 untuk overview insiden dan form konfirmasi publik. Dibangun dengan React, TypeScript, Vite, dan Tailwind CSS di folder terpisah dari eksperimen backend dan OpenClaw.

## Keputusan yang telah disepakati

- Gunakan React, TypeScript, Vite, dan Tailwind CSS.
- Kerjakan tampilan mobile terlebih dahulu, kemudian kembangkan tampilan desktop.
- Foto laporan dan peta lokasi sama-sama ditampilkan.
- Prototipe mendukung pilihan valid/invalid, checkbox selesai bersyarat, keterangan, serta preview foto unggahan.
- Screenshot dapat terdiri dari beberapa bagian halaman dan keadaan form.
- Selesaikan layout terlebih dahulu; polish visual mengikuti referensi yang akan diberikan pengguna.
- Gunakan data simulasi untuk kebutuhan pitch deck.

## Layout awal

Gunakan satu halaman scroll dengan kelompok informasi dan form yang jelas. Tombol `Berikan konfirmasi` pada overview mengarahkan pengguna ke bagian form pada halaman yang sama. Foto dan peta ditampilkan sebagai bagian tersendiri pada mobile. Keterangan dan foto tambahan diberi label opsional.

Tampilkan ketentuan lokasi sebelum pengguna mengisi bukti opsional. Permintaan lokasi hanya dimulai setelah tindakan pengguna. Untuk versi fungsional, hasil GPS yang usang perlu diperbarui menjelang pengiriman tanpa menghapus jawaban yang sudah diisi.

Layout awal ini siap ditinjau pengguna. Skenario sintetis memakai Kota Malang dengan foto AI dan peta skematis. Wordmark dan warna bersifat sementara. Perilaku GPS berupa simulasi yang dapat dicoba sesuai keputusan pengguna.

## Struktur implementasi

Ikuti pembagian Stage P0 dalam `04_ENGINEERING_RULES.md` dari `SIGAPI_Documentation_Pack_v0.1.zip`:

```text
apps/public-web/
  src/app/
  src/pages/
  src/features/incidents/
  src/components/ui/
  src/mocks/
  src/styles/
  tests/
```

Tambahkan direktori dan file implementasi saat diperlukan. Kode frontend ditempatkan di folder ini agar area kerja terpisah dari `backend/` dan `openclaw-plugin/`.

## Batas prototipe

Aplikasi berjalan tanpa backend. Tidak ada API, akses GPS perangkat, upload, penyimpanan, atau pengiriman ke penerima. Nilai jarak/akurasi adalah fixture, bukan hasil pengukuran. Semua isian hanya berada dalam memori halaman dan hilang saat reload. Halaman memakai tema terang, termasuk ketika OS memakai tema gelap.

Pilihan invalid selalu mereset checkbox selesai menjadi false. Klaim selesai merupakan pengamatan publik, bukan penutupan resmi oleh BPBD. Data pribadi pelapor dan GPS pengisi tidak ditampilkan kepada publik.

## Menjalankan

Gunakan Node.js 24 atau lebih baru. Dari root repo:

```powershell
Set-Location apps/public-web
npm ci
npm run dev
```

Buka **http://127.0.0.1:5173/laporan/demo-malang-001**. Route `/` juga membuka contoh tersebut. Slug lain menampilkan halaman laporan tidak tersedia. Dev server memakai loopback dan port 5173; port yang sudah digunakan tidak diganti diam-diam.

## Mencoba prototipe

- Tekan `Berikan konfirmasi` untuk menggulir dan memindahkan fokus ke form.
- Pilih kondisi pada `Coba kondisi lokasi`, lalu tekan `Coba lokasi simulasi`. Tersedia dalam radius 850 m, izin ditolak, dan di luar radius 2,8 km.
- Pilih jawaban. Checkbox selesai hanya tampil untuk valid dan default tidak dicentang.
- Keterangan opsional dibatasi 2.000 karakter. Foto opsional dibatasi 10 MB; tersedia preview dan hapus foto.
- Kirim hanya dapat dicoba setelah memilih jawaban dan lokasi simulasi dalam radius. Hasilnya diberi label `Simulasi selesai · belum dikirim`.

Pada desktop lebar minimal 1024px, overview dan form tampil dalam dua kolom. [Skenario demo](SCENARIO.md) dapat digunakan sebagai acuan visual WhatsApp/Channel nanti. Tidak ada pengubahan eksperimen AI yang diperlukan untuk menjalankan frontend.

## Verifikasi

```powershell
npm run build
npm test
npm run test:e2e
```

E2E memakai Playwright dengan Microsoft Edge yang terpasang. Jika Edge tidak tersedia, pasang browser tersebut atau sesuaikan `launchOptions.channel` di `playwright.config.ts` dengan browser Chromium yang tersedia. Pengujian dapat menyalakan dev server sendiri atau memakai server frontend yang sudah berjalan.

Pengujian mencakup reset checkbox selesai, pembatasan simulasi lokasi, perubahan jawaban, batas keterangan, unggahan besar/rusak, preview dan penghapusan foto, fokus keyboard, route tidak tersedia, reduced motion, serta layout 360/375/390/768/1440px dan landscape. Alur demo memeriksa tidak ada request POST. Ini bukan bukti validasi GPS, API, atau integrasi WhatsApp.

Screenshot dihasilkan ke folder `artifacts/` dan diabaikan Git:

- `01-overview-mobile.png`: bagian awal laporan, 390 × 844.
- `01b-photo-map-mobile.png`: foto dan peta pada satu tangkapan layar.
- `02-confirmation-mobile.png`: form dengan pilihan valid dan lokasi simulasi dalam radius.
- `02b-invalid-mobile.png`: pilihan invalid tanpa checkbox selesai.
- `03-location-error-mobile.png`: lokasi simulasi di luar radius.
- `04-preview-mobile.png`: hasil interaksi yang jelas belum dikirim.
- `layout-*.png`: seluruh halaman pada tiap lebar pengujian.

## Tahap berikutnya

Tinjau susunan informasi, panjang halaman, serta ukuran foto/peta bersama pengguna. Polish visual dilakukan setelah layout disepakati dan referensi diberikan. P1 nantinya memerlukan kontrak API, GPS browser, pemeriksaan radius/akurasi/waktu di server, serta persistensi nyata; kontrol lokasi simulasi bukan pengganti validasi tersebut.
