# SIGAPI Public Web

Prototipe Stage P0 untuk halaman detail insiden dan konfirmasi publik. Mengikuti pembaruan master prompt UI/UX pengguna: mobile-first, satu halaman vertikal, palet SIGAPI dari gambar referensi terbaru, dan pengiriman tetap nonaktif tanpa backend.

## Tampilan screenshot dan tampilan developer

Sesuai permintaan terbaru pengguna, halaman utama menampilkan presentasi produk tanpa badge simulasi, caption AI, catatan prototipe/backend, atau kontrol pengujian. Referensi tampil sebagai `SIGAPI-001`; waktu kejadian menggunakan `Belum tersedia` agar tidak mengarang tanggal. Penanda asal data sintetis tetap berada di modul fixture dan dokumentasi ini.

Tampilan utama mempertahankan pilihan jawaban, checkbox, keterangan, dan preview foto. Sesuai revisi pilihan pengguna, tombol Aktifkan Lokasi dan Kirim Konfirmasi kembali memakai warna Oranye Bara, sementara fungsinya tetap nonaktif. Keterangan pemeriksaan lokasi belum tersedia tetap terlihat; teks pengiriman belum tersedia di bawah tombol Kirim Konfirmasi hanya ditampilkan pada mode pengembangan. Tidak ada GPS perangkat, validasi server, upload, atau penyimpanan nyata yang ditambahkan.

Untuk mencoba seluruh keadaan GPS beserta kontrol dan keterangan pengembang, buka **http://127.0.0.1:5173/laporan/demo-insiden-sigapi?dev=1**. Parameter ini hanya mengatur tampilan lokal; bukan kontrol akses untuk fitur atau data sensitif.

## Menjalankan

Gunakan Node.js 24 atau lebih baru. Dari root repo:

```powershell
Set-Location apps/public-web
npm ci
npm run dev
```

Buka **http://127.0.0.1:5173/laporan/demo-insiden-sigapi**. Route `/` membuka contoh tersebut. Tautan lama `/laporan/demo-malang-001` tetap didukung. Slug lain menampilkan laporan tidak tersedia.

Server memakai loopback port 5173. Tidak perlu menyalakan backend, gateway, atau database.

Seluruh ikon antarmuka, termasuk pin di dalam ilustrasi peta, menggunakan `lucide-react` melalui komponen `Icon.tsx`. Import ikon eksplisit menjaga bundle hanya memuat ikon yang dipakai. Ukuran mengikuti konteks komponen, ketebalan garis seragam 1,8, dan warna mengikuti palet lewat `currentColor`. Ikon dekoratif disembunyikan dari pembaca layar; label tombol tetap berupa teks. SVG ilustrasi peta dan pola kontur footer merupakan grafis dekoratif, bukan ikon. Logo dan favicon SIGAPI tetap menggunakan aset logo asli.

## Struktur halaman

Mobile dan tablet di bawah 1.100px menggunakan satu kolom terpusat dengan container maksimal 800px. Desktop mulai 1.100px memakai container maksimal 1.184px: informasi kejadian dan peta di kiri, kartu lokasi pengguna dan form di kanan. Kolom form mendapat ruang sedikit lebih lebar agar pilihan dan input mudah dibaca. Urutan DOM tetap mengikuti alur mobile, tanpa duplikasi konten atau scroll terpisah.

1. Header berisi logo SIGAPI milik pengguna dalam susunan horizontal dan nomor laporan. Nomor tidak ditampilkan pada route laporan yang tidak tersedia.
2. Judul Konfirmasi Laporan Kebakaran dan deskripsi singkat, masih di dalam header.
3. Kelompok konteks kejadian: status Belum dikonfirmasi resmi, foto 16:9, judul, lokasi, serta waktu bertuliskan Belum tersedia.
4. Bagian peta skematis berada dalam kelompok konteks yang sama, dengan label di dekat pin; penanda simulasi hanya ditampilkan dalam mode developer.
5. Kartu konfirmasi lokasi pengguna, status, serta tombol Aktifkan Lokasi.
6. Pilihan kejadian, checkbox selesai bersyarat, keterangan, foto tambahan, dan tombol Kirim Konfirmasi.
7. Pesan keselamatan dan footer yang menjelaskan keterbatasan konfirmasi publik.

Foto, titik peta, dan kejadian adalah simulasi. Lihat [skenario](SCENARIO.md).

Header memakai satu foto hutan penuh, dari logo hingga deskripsi “Periksa informasi kejadian...”. Foto ditampilkan tajam tanpa filter blur atau pembesaran layer tambahan, memakai gambar responsif yang sesuai viewport dan kerapatan piksel. Lapisan kabut dan gradasi hitam memiliki beberapa stop yang tersebar bertahap; jarak sebelum judul ditambah 24px agar transisi terang ke gelap mendapat ruang yang cukup. Logo transparan mempertahankan warna asli tanpa kotak atau sorotan lokal. Semua teks header memakai Putih Hangat dan garis bawah memakai Oranye Bara. Latar foto bersifat dekoratif, tidak menerima pointer, dan tidak beranimasi.

## Interaksi

Pengujian GPS dan kontrol hasil di bawah ini tersedia pada tampilan developer `?dev=1`. Tampilan utama tetap pada status Lokasi belum diperiksa untuk kebutuhan screenshot.

- Awalnya tidak ada jawaban dipilih, lokasi belum diperiksa, keterangan kosong, dan tidak ada foto tambahan.
- Tombol Aktifkan Lokasi menjalankan simulasi lokal 750 ms dengan indikator loading; tidak mengakses GPS perangkat.
- Buka Pengaturan simulasi lokasi untuk memilih hasil: memenuhi radius 850 m/akurasi 25 m, izin ditolak, di luar radius 2,8 km, atau akurasi buruk 140 m.
- Mengubah pengaturan membatalkan simulasi yang sedang berjalan. Hasil lama tidak menimpa pilihan baru.
- Lokasi yang memenuhi syarat tetap diberi label hasil simulasi dan belum diperiksa server.
- Kedua jawaban adalah pilihan sah. Pilihan invalid menyembunyikan dan mereset checkbox selesai; memilih kembali valid tidak mengembalikan centang.
- Keterangan opsional dibatasi 2.000 karakter.
- Foto opsional mendukung JPG/PNG/WebP maksimal 10 MB, pemeriksaan decode lokal, preview seluruh gambar tanpa crop, serta hapus foto. Pemilih berkas tidak memberi kesan mendukung drag-and-drop. Fokus kembali ke pemilih setelah foto dihapus. Tidak diunggah.
- Tombol Kirim Konfirmasi **selalu disabled** pada prototipe. Tidak ada request submit, receipt, toast sukses, atau simulasi penyimpanan.
- Isian hanya berada dalam memori halaman dan hilang saat reload.

## Kode dan styling

```text
src/app/                    entry point, font lokal, alias route
src/pages/                  komposisi halaman
src/features/incidents/     informasi, peta, lokasi, pilihan, upload, dan reducer
src/components/ui/          ikon outline, header, footer, dan pesan keselamatan
src/mocks/                  data insiden, pilihan, dan pesan lokasi sintetis
src/styles/tokens.css       seluruh token warna dan font sementara
src/styles/app.css          layout dan interaksi
public/media/               ilustrasi foto AI
tests/                      aturan state dan browser
```

Stack tetap React + TypeScript + Vite + Tailwind CSS. Inter dimuat lokal melalui paket Fontsource; browser tidak menghubungi layanan font eksternal. Tema tetap terang meskipun OS menggunakan dark mode.

Palet terbaru mengikuti enam nilai persis dari gambar pengguna dan menggantikan palet sementara master prompt:

| Warna | HEX | Penggunaan |
| --- | --- | --- |
| Oranye Bara | `#C84B1B` | Identitas, tombol aktif, marker, aksen peringatan/tidak sesuai |
| Teal Hutan | `#1F4D45` | Judul, wordmark, navigasi, pilihan valid, status memenuhi syarat |
| Putih Hangat | `#FFFCF8` | Latar halaman, permukaan kartu, teks tombol aktif |
| Peach Lembut | `#FBE8DE` | Sorotan, badge, pilihan tidak sesuai, latar peringatan |
| Arang Kehijauan | `#26332F` | Isi, label form, teks peringatan pada peach |
| Abu Sage | `#66736D` | Keterangan, caption, waktu, teks sekunder |

Seluruh warna dasar disimpan di `src/styles/tokens.css`; border, hover, permukaan pendukung, dan peta diturunkan dari campuran enam warna tersebut. Warna oranye/teal pada status selalu dilengkapi teks serta ikon. Peach menggunakan teks teal atau arang agar keterangan kecil tetap terbaca.

Aplikasi frontend tetap terpisah dari eksperimen AI di `backend/` dan `openclaw-plugin/`.

## Logo SIGAPI

PNG asli dari pengguna disimpan tanpa perubahan di `public/branding/sigapi-logo.png`. Hash SHA-256 salinan diperiksa sama dengan berkas sumber. Bentuk simbol dan lettering asli dipertahankan; palet UI tetap menggunakan enam token warna yang disepakati.

`BrandLogo` memakai viewport SVG untuk membingkai bagian simbol dan lettering dari PNG yang sama. Header menyusun keduanya secara horizontal agar terbaca pada mobile tanpa menambah tinggi berlebihan. Filter SVG hanya menghapus latar kertas melalui kanal alpha; ketiga kanal RGB dipertahankan. Bagian teal, api oranye, dan lettering gelap tetap memakai warna dari PNG asli. Tidak ada recoloring atau kotak latar pada tautan logo. Kabut foto dan lapisan terang yang menyatu sepanjang bagian atas menyediakan pemisah untuk logo. Logo footer tetap menggunakan komposisi bertumpuk dan warna asli tanpa filter. PNG sumber serta favicon tidak diubah oleh penyesuaian header ini.

Audit warna/transparansi logo tersimpan di `artifacts/forest-logo-review.json`. Audit gabungan foto, teks, dan logo tersedia di `artifacts/forest-sharp-header-review.json`: kontras bagian hijau logo minimum 3,84:1 dan sampel lettering gelap minimum 6,42:1 terhadap piksel latar sebenarnya pada sebelas lebar layar. Ini pemeriksaan terarah untuk desain, bukan klaim audit aksesibilitas lengkap. Artefak `peach-`, `logo-original-`, `logo-inverse-`, dan `forest-header-` berasal dari iterasi sebelumnya.

Favicon `public/branding/favicon.svg` membingkai simbol dari PNG asli yang di-embed ke SVG. Filter alpha SVG menghapus latar terang untuk tampilan tab transparan; kanal RGB simbol tetap dipertahankan. PNG sumber serta logo header/footer tidak diubah. URL favicon memakai versi cache baru agar browser memuat pembaruan.

## Foto header

Aset dekoratif `public/media/forest-header.webp` dibuat dengan tool `image_gen` bawaan, lalu diekspor ke WebP kualitas 84 untuk penyajian web. Ukurannya 2172 × 724px, 266.226 byte. Ini citra fotografis generatif untuk latar, bukan dokumentasi kejadian atau lokasi nyata di Kota Malang. Berkas PNG hasil generasi asli tetap tersimpan di direktori generated_images milik Codex.

Foto sekarang menggunakan elemen `img` dekoratif dengan `srcset`, `sizes`, `fetchPriority="high"`, dan preload responsif yang cocok dengan atribut gambar. `object-fit: cover` serta posisi `center top` mempertahankan crop. Filter `blur(2px)` dan inset pembesaran sebelumnya dihapus. Gambar turunan diekspor langsung dari PNG sumber menggunakan resampling Lanczos dan WebP kualitas 84; tidak ada upscaling buatan atau kompresi ulang dari WebP lama.

| Berkas | Resolusi | Ukuran |
| --- | --- | --- |
| `forest-header-960.webp` | 960 × 320 | 65.866 byte |
| `forest-header-1280.webp` | 1280 × 427 | 111.698 byte |
| `forest-header-1600.webp` | 1600 × 533 | 165.738 byte |
| `forest-header.webp` | 2172 × 724 | 266.226 byte |

Nilai `sizes` memperhitungkan lebar gambar yang dibutuhkan untuk menutupi tinggi header dengan rasio sumber 3:1, agar mobile tidak memilih gambar kecil yang kemudian diperbesar saat crop. Audit `forest-image-delivery-review.json` memakai konteks browser baru pada enam viewport dan DPR 1/2. Setiap halaman mengambil satu varian saja, sesuai preload: 390px/DPR 1 memakai 65.866 byte (75,3% lebih kecil dari sebelumnya), 1440px/DPR 1 memakai 165.738 byte (37,7% lebih kecil), dan DPR 2 memilih sumber 2172px. Resolusi maksimum tetap mengikuti PNG asli 2172px; aset tidak dibesarkan untuk mengklaim resolusi Retina desktop yang tidak tersedia.

Lapisan hitam memakai beberapa stop yang menyebarkan transisi dari atas ke bawah, menggantikan kenaikan opasitas tajam dalam 48px. Lapisan terang di atas juga memudar bertahap. Overlay dibuat melalui CSS tanpa mengaburkan detail foto. Jika foto gagal dimuat, elemen gambar disembunyikan agar ikon gambar rusak tidak muncul; gradient Putih Hangat ke Teal Hutan tetap menjaga pembagian terang/gelap.

Prompt final untuk aset fotografis:

```text
Use case: photorealistic-natural. Asset type: photographic forest background for an Indonesian wildfire community reporting app header, no interface elements. Generate a high quality realistic landscape photograph of a lush tropical montane forest in East Java, layers of green tree canopies and tall trunks on a misty hillside at early morning. Very wide horizontal composition suitable for a shallow website banner, approximately 3:1 aspect ratio. The upper left and upper central band has soft luminous pale gray mist and gentle diffused daylight, with subtle forest silhouettes; mid and lower portions have clearly recognizable deep green forest canopy, the right side has more detailed trees and depth. Natural understated editorial photography, quiet and grounded, realistic foliage, no sunset, no fires, no smoke, no buildings, no people, no text, no logos, no borders. Leave calm visual texture for overlaid UI text. Do not bake in a black overlay or blur; those will be applied responsively in CSS.
```

## Footer

Footer memakai Teal Hutan (`#1F4D45`) selebar layar, dipisahkan oleh garis tipis Oranye Bara. Pola kontur SVG dari desain header terdahulu diterapkan kembali dengan garis Putih Hangat beropasitas 10%; sambungan horizontalnya mulus, tanpa animasi, `aria-hidden`, dan `pointer-events: none`. Konten di dalamnya mengikuti batas lebar halaman.

Logo tetap memakai bentuk bertumpuk dan warna asli, diperbesar menjadi 72px di atas alas Putih Hangat bersudut membulat. Judul memakai Putih Hangat dan keterangan memakai Peach Lembut. Pesan keterbatasan konfirmasi publik tetap tampil; catatan simulasi footer hanya ada dalam mode developer.

Audit `artifacts/footer-review.json` memeriksa enam lebar 320–1920px, footer selebar viewport, posisi logo terpusat, tidak ada overflow, dan teks tidak terpotong. Dengan asumsi konservatif garis kontur tepat di belakang teks, kontras judul 7,06:1 dan keterangan 6,08:1. Screenshot terbaru: `footer-390.png`, `footer-1440.png`, serta `footer-page-390.png` dan `footer-page-1440.png`.

## Verifikasi dan screenshot

Hasil audit desain dan interaksi terbaru dicatat di [UI_AUDIT.md](UI_AUDIT.md). Bahasa utama konsisten menggunakan Anda, instruksi keterangan tetap terlihat saat mengetik, dan fokus keyboard textarea memiliki outline solid. Logo, palet, header foto, serta footer kontur tetap memakai pilihan pengguna.

```powershell
npm run build
npm test
npm run test:e2e
```

E2E menggunakan Microsoft Edge yang terpasang melalui Playwright. Konfigurasi dapat disesuaikan ke browser Chromium lain di `playwright.config.ts`. Dev server dapat dijalankan otomatis oleh pengujian atau digunakan kembali jika sudah aktif.

Pengujian mencakup urutan section; foto 16:9; layout satu kolom pada 320/360/390/768/1024px dan dua kolom pada 1100/1280/1440/1920px; batas header termasuk deskripsi; loading dan error lokasi; pembatalan hasil simulasi usang; reset checkbox; foto besar/rusak; preview/hapus foto; keyboard; reduced motion; landscape; reflow dengan CSS zoom 2x; dan kompatibilitas tautan lama. Pengujian juga memeriksa tidak ada pemanggilan GPS perangkat atau request POST pada alur lokasi.

Screenshot terbaru disimpan di `artifacts/` dan diabaikan Git:

- `anti-slop-after-390.png` dan `anti-slop-after-1440.png`: tampilan awal setelah audit.
- `anti-slop-filled-mobile.png` dan `anti-slop-filled-desktop.png`: jawaban valid, checkbox bersyarat, keterangan, dan foto tambahan.
- `anti-slop-error-mobile.png`: jawaban tidak sesuai serta error foto rusak.
- `anti-slop-review.json`: pemeriksaan struktur, ARIA, tautan, reflow, serta sampel kontras pada beberapa keadaan.
- `anti-slop-header-review.json`: audit piksel header setelah perbaikan copy dan nomor laporan.

Artefak di bawah mempertahankan bukti iterasi sebelumnya; gunakan prefix `anti-slop-` untuk tampilan hasil audit terbaru.

- `header-desktop-layout-*.png`: halaman penuh pada sembilan lebar pengujian layout terbaru.
- `forest-sharp-header-320.png`, `forest-sharp-header-390.png`, `forest-sharp-header-1100.png`, `forest-sharp-header-1440.png`, dan `forest-sharp-header-1920.png`: header tajam dengan gradasi yang diperhalus.
- `forest-sharp-page-390.png`, `forest-sharp-page-1100.png`, `forest-sharp-page-1440.png`, dan `forest-sharp-page-1920.png`: halaman penuh dengan header terbaru.
- `forest-sharp-retina-390.png` dan `forest-sharp-retina-1440.png`: hasil render DPR 2.
- `forest-sharp-header-fallback.png`: inspeksi tampilan ketika foto gagal dimuat.
- `capture-01-incident-mobile.png`: header serta informasi kejadian pada 390 × 844.
- `capture-02-map-location-mobile.png`, `capture-03-form-mobile.png`, dan `capture-03b-form-card-mobile.png`: bagian peta, lokasi, serta form.

Audit `forest-sharp-header-review.json` memeriksa sebelas lebar 320–2560px, termasuk kedua sisi breakpoint 640px dan 1100px, tanpa overflow horizontal. Kontras header diukur dari hasil render: teks disembunyikan sementara tanpa mengubah layout atau latar badge, lalu seluruh area baris teks disampling terhadap piksel foto/overlay. Sampel teks header minimum 4,81:1. Bagian solid logo juga dibandingkan dengan piksel latar di posisi rendernya. Fokus keyboard logo, reflow CSS zoom 2x, dan fallback tanpa foto diperiksa secara terarah. Ini bukan audit aksesibilitas lengkap.

Artefak berprefix `redesign-`, `palette-`, atau `capture-layout-` berasal dari iterasi sebelumnya; gunakan `header-desktop-layout-` untuk layout halaman penuh terbaru.

## Integrasi selanjutnya

P1 memerlukan API publik teredaksi, HTTPS/browser GPS, validasi server terhadap koordinat/radius/akurasi/usia lokasi, persistensi, dan validasi upload ulang. Parameter awal: radius 2 km, akurasi 100 m, usia fix 60 detik; tetap perlu diuji. Hanya receipt penyimpanan nyata yang boleh menghasilkan pesan sukses. Satu klaim selesai publik tidak menutup insiden secara resmi.
