# Demo OpenClaw: Validasi dan Verifikasi

Tanggal: 22 Oktober 2026. Target: 25 Oktober 2026, Asia/Jakarta.
Status: fondasi Task 1 diimplementasikan; integrasi akun nyata belum lulus. Lihat [setup dan gerbang Task 1](../../setup-task-1.md).

Pembaruan perencanaan 22 Oktober: pengguna memilih GPS akurasi maksimal 100 m dan usia lokasi maksimal 60 detik; ketika layanan bukti gagal, kanal publik ditahan sementara ancaman tinggi tetap dieskalasikan terlabel ke nomor uji. Pilihan tersebut berlaku untuk demo ini. [Rencana implementasi lima task](../plans/2026-10-22-validation-demo-implementation.md) memperinci urutan, parameter eksperimen tambahan, dan pemeriksaan penerimaan.

## Acuan dan keputusan pengguna

- [Knowledge v3](../../../Knowledge_Doc_Terbaru_DeveloperDay_Karhutla_2026.md) menjadi acuan produk. [Rancangan utama](2026-10-21-openclaw-ai-design.md) menjadi acuan teknis umum.
- WhatsApp nyata melalui OpenClaw; nomor khusus sudah tersedia, OpenClaw belum terpasang.
- Provider AI kandidat Groq Free Plan; analisis gambar harus nyata. Model dipilih berdasarkan akses akun dan uji gambar, bukan nama model yang diasumsikan selalu tersedia.
- Google Cloud Vision Web Detection nyata; pengguna bersedia menyiapkan billing aktif. Belum ada proyek, kredensial, atau aktivasi API yang dikonfirmasi.
- FIRMS boleh menggunakan data tersimpan dengan sumber dan waktu pengamatan/pengambilan yang ditampilkan. Data tersimpan bukan feed live.
- Form publik memakai GPS browser nyata dan validasi server radius <=2000 m.
- Konflik bukti: minta klarifikasi. Jika belum selesai, tahan dari kanal publik. Ancaman tinggi dieskalasikan ke nomor uji otoritas dengan label BELUM TERVERIFIKASI dan alasan konflik. Ini kebijakan demo, bukan SOP instansi atau persetujuan pilot operasional.
- Distribusi ke nomor/kanal uji. Tidak menghubungi instansi nyata tanpa instruksi dan izin penerima yang sesuai.

## Hasil demo

Warga mengirim media wajib, lokasi kejadian dan keterangan melalui WhatsApp. Sistem memeriksa kelengkapan, menganalisis isi gambar, mencari penggunaan ulang di web, membandingkan laporan lain serta FIRMS, lalu menunjukkan keputusan dan alasannya. Insiden mempunyai link publik; kontribusi valid/invalid yang memenuhi syarat lokasi dapat dibaca lewat TRACK. Solved hanya klaim pengguna, bukan penutupan resmi.

Demo harus menunjukkan bukti pemeriksaan nyata, bukan hanya percakapan AI yang menyatakan sudah memeriksa. Setiap hasil menyimpan status ketersediaan, sumber, waktu dan versi analisis. Pencarian tanpa kecocokan tidak menghasilkan label foto asli.

## Arsitektur minimum

OpenClaw/plugin penghubung menangani transport. FastAPI menangani state, validasi dan aturan. Groq mengekstrak informasi serta mengamati gambar; Google Vision melakukan pencocokan web. Database persisten menyimpan report, incident, hasil pemeriksaan, consent, delivery dan verification events. Media disimpan privat. Form publik terhubung ke backend yang sama lewat HTTPS.

Ikuti pola satu backend dengan worker persisten dari rancangan utama. Tidak ada model kedua di OpenClaw yang membalas warga secara paralel. Sebelum membangun alur, buktikan plugin dapat mengambil alih pesan, mengakses media/lokasi, dan mengirim hasil tanpa balasan ganda. Jika SDK versi terpasang tidak mendukung kontrak yang diasumsikan, revisi integrasi berdasarkan hasil uji; jangan mengganti OpenClaw diam-diam.

Node lokal terdeteksi 24.15.0 dan Python 3.11.3 pada 22 Oktober. OpenClaw tidak ditemukan di PATH. Versi Node perlu disesuaikan dengan persyaratan versi OpenClaw yang dipilih. Pin versi setelah smoke test.

## Alur validasi awal

1. Simpan pesan secara idempotent; kumpulkan media, lokasi dan keterangan dalam draft pengirim yang benar.
2. Periksa media dapat dibuka, koordinat valid, lokasi menunjuk kejadian, serta keterangan memadai. Teks lokasi perlu konfirmasi titik sebelum routing.
3. Groq mengeluarkan JSON tervalidasi dengan observasi api/asap, klaim pelapor, konflik dan referensi sumber. Nomor, consent dan hasil kirim tidak diputuskan model.
4. Jalankan Web Detection serta pencocokan internal; bedakan full match, partial match dan kemiripan visual. Hasil cocok tidak otomatis membuktikan laporan palsu. Hash identik dapat menjadi baseline duplikat; kemampuan tahan crop/kompresi tidak diklaim sebelum diuji.
5. Cocokkan FIRMS tersimpan dan kandidat insiden menurut lokasi/waktu. Simpan report sumber terpisah walau dikelompokkan.
6. Klarifikasi konflik; terapkan kebijakan demo yang dipilih. Routing berasal dari aturan dan tujuan uji yang dikonfigurasi, bukan nomor yang dihasilkan model.
7. Catat upaya kirim dan outcome per tujuan. TRACK hanya menyebut tujuan yang benar-benar berhasil, lalu konfirmasi publik bila tersedia.

Definisi operasional ancaman tinggi masih usulan: pernyataan eksplisit orang terancam/terjebak/butuh evakuasi atau api mengancam rumah/fasilitas. Ketiadaan informasi tidak dianggap bukti risiko rendah. Contoh dan aturan harus diuji; model tidak boleh mengarang ancaman.

Ketika Groq/Vision gagal atau bukti belum memadai setelah klarifikasi, pengguna memilih hold kanal publik, sementara ancaman tinggi dieskalasikan terlabel ke nomor uji. Simpan outcome unavailable; jangan mengklaim pemeriksaan lolos. Untuk demo, hold tidak memiliki timer penerusan otomatis; pelapor dapat melengkapi input. SOP dan SLA operasional instansi di luar demo belum ditentukan.

## Form publik dan TRACK

- Route `/laporan/{slug_id}`, slug acak per insiden; overview teredaksi, tanpa identitas/nomor pelapor.
- GPS browser melalui HTTPS; backend memeriksa koordinat, usia fix, akurasi dan jarak terhadap titik kejadian. Koordinat tetap dapat dimanipulasi; jarak server bukan autentikasi.
- `valid`/`invalid` wajib. Deskripsi/foto opsional. Solved opsional dan default false, hanya sah untuk valid.
- Lokasi tidak tersedia, usang, tidak akurat atau >2000 m menyebabkan penolakan teknis; tidak membuat suara invalid kejadian.
- Parameter demo dipilih pengguna: usia fix maksimal 60 detik, accuracy maksimal 100 m. Angka ini eksperimen demo, bukan batas ilmiah. Lokasi buruk diminta ulang; tanpa bypass GPS publik.
- Simpan kontribusi dengan sumber public_link, timestamp dan bukti. Event anonim tidak dianggap orang independen. Konflik ditampilkan tanpa menghapus data awal.
- Usulan agregasi konservatif: satu solved ditampilkan sebagai “ada pengguna melaporkan kejadian selesai”, tidak menutup insiden secara resmi. Tidak ada dashboard progres pemadaman.
- TRACK memeriksa relasi laporan dengan pengirim WhatsApp; slug publik tidak memberi akses detail privat.

## Akun dan konfigurasi

| Kebutuhan | Penyiapan |
| --- | --- |
| OpenClaw | Instal runtime yang sesuai, nomor khusus ditautkan melalui QR oleh pengguna; sesi privat |
| Groq | API key pengguna disimpan lokal di environment, model vision diuji dengan media berizin; tangani 429 dengan retry terbatas |
| Google Cloud | Pilih/buat project pengguna, tautkan billing dengan tindakan pengguna, aktifkan Vision API, autentikasi lokal atau credential layanan sesuai deployment |
| Batas biaya | Batasi sampel, kuota dan panggilan; cache hasil per hash/versi. Budget alert bukan hard spending cap |
| Form publik | HTTPS yang dapat dibuka dari ponsel; alamat publik hanya untuk form/API publik, bukan gateway operator OpenClaw |
| FIRMS | Snapshot bersumber dan bertanggal, bukan angka contoh tanpa provenance |
| Tujuan | Nomor uji otoritas dan kanal/koordinator uji; pisahkan dari data instansi nyata |

Jangan meminta API key, credential JSON, QR atau token dikirim melalui chat. Jangan menyimpan secret dalam Git, prompt atau log. Persetujuan billing tidak berarti proses aktivasi sudah selesai atau membolehkan penggunaan tanpa batas biaya. Pilihan project/account dan batas penggunaan perlu dikonfirmasi saat setup.

## Skenario penerimaan

| Kasus | Hasil yang harus terlihat |
| --- | --- |
| Media/lokasi/keterangan datang terpisah | Satu draft, pertanyaan tidak berulang; duplikat pesan tidak membuat job ganda |
| Foto yang diketahui pernah ada di web | Hasil nyata Vision beserta URL/jenis kecocokan; sinyal penggunaan ulang, bukan putusan palsu |
| Foto tanpa kecocokan web | Hasil no_match; tidak menyebut authentic |
| Konflik belum selesai | Kanal publik ditahan; jika ancaman tinggi, nomor uji menerima label dan alasan |
| Vision/Groq gagal atau 429 | Unavailable/retry terlihat; bukan hasil analisis sukses |
| Dua report sama / dua insiden dekat | Report tersimpan terpisah; pengelompokan dan distribusi tidak mengganda atau salah gabung |
| GPS dalam/luar radius | Dalam radius dan kualitas memadai diterima; >2000 m OUT_OF_RADIUS tanpa verification_event |
| GPS ditolak/usang/buruk | Submit gagal dengan feedback; tidak menambah hitungan invalid |
| Invalid dengan solved=true | Server mencegah penyimpanan solved yang bertentangan |
| Valid + solved / kontribusi berlawanan | TRACK beratribusi klaim publik / konflik; bukan konfirmasi resmi |
| Tidak ada kontribusi publik | Alur utama dan TRACK pengiriman tetap berfungsi |
| Pengiriman gagal / TRACK milik orang lain | Tidak ada klaim terkirim palsu / tidak membocorkan data |

Untuk uji radius otomatis, input koordinat sintetis ditandai pengujian. Untuk demonstrasi GPS nyata, gunakan lokasi insiden simulasi yang aman; jangan meminta orang mendekati api. Nilai tepat 2000 m dan di atasnya diuji di server.

## Urutan tiga hari

1. Hari 1: buktikan OpenClaw menerima/mengirim pesan, media dan lokasi; siapkan Groq dan Vision; simpan draft persisten.
2. Hari 2: pemeriksaan bukti nyata, kebijakan konflik, duplikat, FIRMS snapshot, serta outcome pengiriman ke nomor uji.
3. Hari 3: form GPS, verification events dan TRACK; uji skenario, perbaiki kegagalan dan rekam demo.

Ini target kerja, bukan jaminan durasi atau implementation plan final. Tunda dashboard admin penuh, ekspansi nasional, training model, skor probabilitas tanpa kalibrasi, dan progres operasi pemadaman.

## Referensi setup

- [Groq Vision](https://console.groq.com/docs/vision) dan [rate limits](https://console.groq.com/docs/rate-limits).
- [Vision setup](https://docs.cloud.google.com/vision/docs/setup), [Web Detection](https://docs.cloud.google.com/vision/docs/detecting-web), [pricing](https://cloud.google.com/vision/pricing).
- [OpenClaw install](https://docs.openclaw.ai/install).

Dokumentasi layanan diperiksa 22 Oktober 2026. Belum ada instalasi, aktivasi billing/API, pairing WhatsApp, atau uji integrasi yang dilakukan dalam penyusunan rancangan ini.
