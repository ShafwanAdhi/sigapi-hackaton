> **Arsip v2 - bukan acuan keputusan terbaru.** Per 22 Oktober 2026, keputusan yang berubah mengikuti [Knowledge Document v3](Knowledge_Doc_Terbaru_DeveloperDay_Karhutla_2026.md). Aturan tanpa link verifikasi, TRACK dua status, media opsional, dan penerusan semua laporan lengkap tidak lagi boleh digunakan sebagai keputusan terkini. Bagian lain diwarisi hanya jika tidak bertentangan dengan v3.

# Knowledge Doc: Bot WhatsApp Pelaporan Karhutla

*Pengembangan dari LaporPak untuk .id DeveloperDay 2026. Dokumen kerja tim, versi 20 Oktober 2026. Nama produk masih sementara.*

## 1. Ringkasan dalam satu paragraf

Warga yang melihat api atau asap cukup mengirim pesan WhatsApp ke satu nomor bot nasional: lokasi (shareloc), foto atau video, dan keterangan singkat. Bot AI memastikan data cukup lengkap, menilai tingkat kepercayaan laporan, lalu meneruskannya ke pihak lokal yang tepat berdasarkan koordinat: saluran WhatsApp MPA (Masyarakat Peduli Api) kota tersebut, dan nomor damkar setempat. Warga tidak perlu menginstal aplikasi atau mengisi formulir. Laporan warga melengkapi data satelit (NASA FIRMS), bukan menggantikannya.

## 2. Info lomba yang harus diingat

- **Pendaftaran ditutup 25 Oktober 2026** (sudah diperpanjang). Paper dan video diunggah lewat dasbor peserta.
- Final: 10 sampai 11 November 2026 di SMESCO Indonesia (lokasi menunggu konfirmasi). 18 tim finalis. Pemenang lanjut ke APICTA Award 7 Desember 2026. Total hadiah Rp100 juta.
- **Paper:** bahasa Inggris, maksimal 15 halaman, maksimal 20 MB, PDF dikirim sebagai tautan. 13 bagian wajib: Title Slide, Problem Statement, Target User & Market, Proposed Solution, Key Features & Tech Stack, Screenshots or Product Demo, Competitive Advantage, Current Status & Development Plan, Business Model, Impact Plan, Roadmap & Future Direction, Team Profile & Contact, Reference.
- **Video demo:** disarankan, maksimal 5 menit, unggah ke YouTube (unlisted atau public). Harus memuat gambaran solusi, fitur utama, dan demonstrasi penggunaan.
- **Kategori yang diusulkan:** Inclusions & Community Services, subkategori Sustainability & Environment. Alternatif: Public Sector & Government (Citizen Services) bila ada keterlibatan instansi.
- **Belum terbaca:** bagian ketentuan "Kewajiban domain .id" dan "Kesiapan & jenis karya" ada di teks lomba tetapi isinya tidak ikut tersalin. Buka developerday.id dan baca langsung, karena disebut menentukan keabsahan karya.

## 3. Masalah dan data yang sudah diverifikasi

### 3.1 Cara menulis soal satelit (perbaikan dari asumsi awal)

Asumsi awal "data satelit telat 2 sampai 6 jam dan satelit tidak selalu di atas Indonesia" kurang tepat. Gunakan versi yang terverifikasi:

- NASA FIRMS mendistribusikan data titik api near real-time dari MODIS dan VIIRS **dalam waktu sekitar tiga jam setelah satelit mengamati**. Sebagian data ultra real-time tersedia lebih cepat, tetapi untuk Indonesia jangan diasumsikan.
- Satelit polar (MODIS dan VIIRS) mengamati lokasi yang sama sekitar dua kali sehari per sensor, jadi ada jeda antar pengamatan.
- Satelit geostasioner Himawari memang memantau Indonesia terus-menerus. BMKG punya produk Geohotspot yang diperbarui tiap 10 menit. Tetapi resolusinya kasar dan sering melewatkan api kecil. Contoh studi di Kalimantan Tengah (data Himawari-8, jadi hanya ilustrasi) menemukan akurasi 31,6 persen dan omission error 68,4 persen terhadap data kebakaran lapangan.
- Awan dan asap tebal menghalangi deteksi (BMKG menyebutnya blank zone).
- Kemenhut sendiri menegaskan hotspot hanyalah indikasi anomali suhu, bukan kepastian kebakaran dan bukan luas area terbakar.

**Kalimat aman untuk paper:** *Satelit polar memiliki jeda pengamatan dan latensi data hingga sekitar tiga jam, satelit geostasioner cepat tetapi kasar dan sering melewatkan api kecil, dan awan atau asap dapat menghalangi deteksi. Laporan warga memberi konfirmasi lapangan yang cepat dan melengkapi data satelit.*

### 3.2 Pelaporan yang sudah ada (jangan diklaim "belum ada")

- **Posko Karhutla Kemenhut** menerima laporan lewat telepon 021-5704618, **WhatsApp +62 8131-00-35000**, dan email posko.karhutla@kehutanan.go.id. Nomor ini rutin dicantumkan di rilis resmi sampai Oktober 2026.
- **SiPongi+** (Kemenhut): pemantauan hotspot dan tautan pelaporan; aplikasi mobile perlu diinstal.
- Prototipe akademik dan lokal: misalnya sistem peringatan dini dan pelaporan MPA berbasis web atau mobile dari IPB, aplikasi "FiRe" untuk Pontianak. Semuanya berbasis aplikasi atau web.
- Penanganan lapangan melibatkan Manggala Agni, BNPB, BPBD, TNI, Polri, damkar, MPA, dan relawan.

**Tindakan tim:** kirim satu laporan uji ke Posko Karhutla Kemenhut dan catat waktu balasan serta isinya. Klaim pembeda di paper harus berasal dari pengamatan ini, bukan asumsi.

### 3.3 Celah yang kita isi

Kanal nasional bersifat terpusat dan manual. Yang belum ada: pemahaman pesan bebas oleh AI, pelengkapan data otomatis, penentuan daerah dari shareloc, pengarahan otomatis ke MPA dan damkar tingkat kota, penilaian kepercayaan laporan, dan pencocokan dengan hotspot.

## 4. Keputusan tim (final untuk versi lomba)

| Topik | Keputusan |
| --- | --- |
| Nomor bot | Satu nomor nasional untuk semua daerah |
| Penentuan daerah | Otomatis dari koordinat shareloc |
| Level daerah | Per kota atau kabupaten |
| Saluran MPA | Saluran WhatsApp satu arah per kota. Admin kota membuat sekali di awal lewat sistem (dibuat atas nomor bot), lalu menyalin tautan untuk dibagikan |
| Damkar | Admin kota mengisi nomor damkar (boleh lebih dari satu) dan alamat lengkap. Laporan diteruskan langsung ke chat nomor tersebut |
| MPA dan damkar | Beda tugas. Kebakaran permukiman diarahkan ke damkar terdekat. Karhutla lahan atau hutan diarahkan ke MPA dan pihak berwenang |
| Status laporan | Satu arah, hanya dua status: "laporan belum lengkap" dan "laporan sudah diteruskan ke pihak berwenang" |
| Fitur | Hanya REPORT dan TRACK dua status. Tidak ada ASK umum dan tidak ada REQUEST |
| Jalur cepat | Tidak ada. Semua laporan melewati pemeriksaan kelengkapan |
| Integrasi data | NASA FIRMS |
| Verifikasi foto | Pencocokan gambar ke web (Google Cloud Vision Web Detection) sebagai salah satu sinyal skor |
| Privasi | Warga ditanya bersedia atau tidak dihubungi pihak berwajib. Nomor ikut diteruskan ke damkar, tidak pernah dikirim ke saluran MPA |
| Gateway WhatsApp | OpenClaw (lihat bagian 8 untuk risiko) |
| Model bisnis | B2G (pemda, BPBD, dan instansi terkait) |
| Link verifikasi per laporan untuk MPA | **Tidak dipakai** |
| Prioritas kerja | Sistem matang (walau belum implementasi lapangan), lalu paper, lalu video |

## 5. Alur sistem

1. Warga mengirim pesan ke nomor bot.
2. Bot meminta persetujuan singkat soal kontak oleh pihak berwajib dan pengelolaan data.
3. Warga mengirim shareloc, foto atau video, dan keterangan. Bot menanyakan data yang kurang secara berurutan (maksimal 3 sampai 4 pertanyaan).
4. Sistem menentukan kota dari koordinat dan menghitung skor kelengkapan.
5. Sistem menghitung skor kepercayaan (bagian 7).
6. Bila lengkap: kartu laporan diteruskan ke saluran MPA kota itu, dan ke nomor damkar kota itu (beserta nomor pelapor bila disetujui).
7. Bot menyampaikan konfirmasi "laporan sudah diteruskan", nomor darurat, dan tombol aksi cepat saran tindakan.
8. Bila tidak lengkap setelah warga berhenti menjawab, status tetap "belum lengkap". Warga yang bertanya status hanya mendapat salah satu dari dua status.

**Kasus tepi yang perlu dirancang:** warga hanya mengirim teks tanpa shareloc (bot meminta pin lokasi; bila gagal, minta nama desa dan kelurahan lalu konfirmasi di peta), lokasi di perbatasan dua kota, kota yang belum punya admin (bot memberi nomor Posko Karhutla nasional dan nomor darurat), pesan suara atau gambar buram, dan laporan ganda dari lokasi yang sama.

## 6. Kelengkapan laporan (sistem poin)

| Data | Status | Catatan |
| --- | --- | --- |
| Lokasi (shareloc) | Wajib | Syarat minimum untuk dianggap lengkap |
| Foto atau video | Sangat disarankan | Bobot besar |
| Jenis kejadian (lahan, hutan, permukiman) | Ya | Menentukan tujuan: permukiman ke damkar |
| Api atau asap terlihat sekarang | Ya | Membedakan kejadian baru dan lama |
| Perkiraan luas (kecil, sedang, besar) | Opsional | Bantu prioritas |
| Dekat permukiman atau fasilitas penting | Opsional | Bantu prioritas |
| Jenis lahan (gambut, kebun, semak) | Opsional | Gambut lebih sulit dipadamkan |
| Ada orang terancam atau butuh evakuasi | Opsional tapi penting | Tampilkan menonjol di kartu laporan |
| Waktu | Otomatis | Dari waktu pesan |
| Kontak pelapor | Dengan persetujuan | Dari nomor WhatsApp |

Aturan usulan: lengkap bila ada lokasi ditambah foto atau deskripsi yang memadai. Angka bobot ditetapkan tim setelah uji skenario. Jangan menambah pertanyaan secara berlebihan; orang yang melihat api tidak akan menjawab kuesioner panjang.

## 7. Verifikasi dan skor kepercayaan

Prinsip: **jangan menolak laporan, beri label.** Salah menolak laporan kebakaran nyata lebih berbahaya daripada meneruskan laporan palsu. Laporan skor rendah tetap diteruskan dengan label "belum terverifikasi".

### 7.1 Sinyal yang dipakai

1. **Kecocokan gambar di web (Google Cloud Vision Web Detection):** bila foto sama persis atau hasil crop dari foto yang sudah ada di internet, turunkan skor dan beri label "foto kemungkinan bukan asli".
2. **Kedekatan dengan hotspot FIRMS:** laporan dekat hotspot terbaru menaikkan skor. Ketiadaan hotspot tidak berarti laporan salah (api kecil, awan, jeda lintasan).
3. **Klaster laporan:** beberapa nomor berbeda melapor di area dan jendela waktu yang sama menaikkan skor dan digabung menjadi satu insiden.
4. **Reputasi nomor:** riwayat laporan sebelumnya.
5. **Konsistensi AI:** apakah foto sesuai deskripsi (ada api atau asap).
6. **Pembatasan:** batas jumlah laporan per nomor per jam.

### 7.2 Fakta penting tentang Google Cloud Vision

- Fitur yang dipakai adalah **Web Detection**. Outputnya mencakup gambar yang cocok penuh, halaman web yang memuat gambar tersebut, gambar yang cocok sebagian (misalnya hasil crop), dan gambar yang mirip secara visual.
- **Tidak ada API resmi Google Search untuk reverse image.** Vision Web Detection adalah jalur resmi yang paling dekat.
- Biaya: 1.000 unit pertama per bulan gratis, lalu sekitar 3,50 USD per 1.000 gambar (harga bisa berubah; cek halaman harga Google). Contoh: 10.000 gambar per bulan sekitar 31,5 USD. Biaya ini cocok untuk model B2G.
- Batas yang harus ditulis jujur: foto asli baru dari warga umumnya tidak ada di internet, jadi hasil "tidak ada kecocokan" adalah normal dan bukan bukti keaslian. Foto buatan AI tidak terdeteksi oleh metode ini. Foto generik (asap atau api umum) bisa menghasilkan kecocokan semu.
- WhatsApp biasanya menghapus metadata EXIF dari foto. Jangan mengandalkan metadata foto; pakai shareloc dan waktu pesan.
- **Tambahan murah:** simpan hash perseptual foto di basis data sendiri untuk mendeteksi foto yang sama dikirim berulang oleh nomor berbeda.

## 8. Gateway WhatsApp, OpenClaw, dan pembuatan saluran

### 8.1 Apakah OpenClaw memakai API resmi WhatsApp?

**Tidak.** Dokumentasi OpenClaw menyebut kanal WhatsApp-nya berbasis WhatsApp Web lewat library Baileys, dengan login melalui QR code seperti menautkan perangkat WhatsApp Web. Baileys adalah library tidak resmi yang menirukan klien WhatsApp Web. Ini berbeda dari WhatsApp Business Platform (Cloud API) milik Meta. Dokumentasi OpenClaw juga menyarankan memakai nomor terpisah.

### 8.2 Apa konsekuensinya?

- Cocok untuk prototipe dan demo lomba karena cepat dan fiturnya lengkap (kirim, terima, grup, media).
- Risiko: otomatisasi tidak resmi dapat membuat nomor dibatasi atau diblokir oleh WhatsApp. Sesi QR bisa putus dan harus dipindai ulang. Tidak ada jaminan layanan (SLA).
- Mitigasi: pakai nomor khusus yang tidak dipakai untuk hal lain, batasi laju kirim, pantau status koneksi, siapkan prosedur pemulihan, dan **bungkus WhatsApp di balik satu lapisan pengiriman (adapter)** agar bisa diganti ke API resmi tanpa mengubah logika sistem.

### 8.3 Pembuatan saluran (WhatsApp Channel)

- Library berbasis protokol WhatsApp Web seperti Baileys memiliki fungsi membuat "newsletter" (saluran), dan beberapa gateway pihak ketiga mengeksposnya sebagai API. Jadi alur "admin klik, bot membuat saluran, admin menyalin tautan" **secara teknis dimungkinkan lewat jalur tidak resmi**. Tim perlu menguji langsung apakah modul OpenClaw yang dipakai mengekspos aksi pembuatan saluran; dokumentasi yang kami baca fokus pada pesan dan grup.
- Dalam pencarian kami, **tidak ditemukan** fitur pembuatan saluran di WhatsApp Business Platform resmi. Statusnya perlu dikonfirmasi di dokumentasi Meta sebelum menulis klaim di paper.
- Meta kini menyediakan **Groups API** di Cloud API (membuat grup, mengelola, tautan undangan) dengan syarat dan batasan tertentu (misalnya jenis nomor dan jenis pesan yang tidak didukung). Detail batas jumlah anggota dan cara menambah anggota harus dicek di dokumentasi Meta.
- Saluran bersifat satu arah (anggota tidak bisa membalas) dan dapat diikuti siapa saja yang punya tautan. Konsekuensinya: **jangan mengirim nomor pelapor ke saluran** (sudah diputuskan) dan pertimbangkan menampilkan lokasi secara kasar di saluran, sementara lokasi lengkap dan kontak hanya ke damkar.

### 8.4 Rekomendasi bertahap

| Tahap | Pendekatan |
| --- | --- |
| Lomba dan pilot | OpenClaw dengan nomor khusus. Saluran dibuat lewat gateway bila tersedia. Cadangan: bot mengirim pesan ke grup atau kontak koordinator MPA yang didaftarkan admin |
| Produksi B2G | Migrasi ke WhatsApp Business Platform resmi lewat penyedia resmi. Notifikasi ke koordinator MPA memakai pesan template atau Groups API, sesuai kebijakan Meta saat itu |

Tulis di paper bagian Current Status dan Roadmap bahwa lapisan pengiriman dirancang modular karena alasan ini.

## 9. Integrasi NASA FIRMS

- Ambil data titik api aktif terbaru untuk wilayah Indonesia dan simpan dengan waktu pengamatan serta sensor.
- Saat laporan masuk, cari hotspot dalam radius dan jendela waktu tertentu (nilai awal usulan: beberapa kilometer dan 24 jam terakhir; diuji dan disetel tim).
- Hasil dipakai sebagai label di kartu laporan: "dekat hotspot terbaru" atau "belum ada hotspot". Jangan memberi kesan hotspot sama dengan kebakaran.
- Tampilkan di dasbor admin peta laporan dan hotspot.
- Catat atribusi dan syarat penggunaan data NASA dan BMKG di paper dan antarmuka.

## 10. Saran tindakan (aksi cepat setelah laporan terkirim)

Setelah konfirmasi, bot menampilkan tombol aksi cepat dinamis, misalnya "Apa yang bisa saya lakukan sambil menunggu?" dan "Apa itu sistem ini?".

Aturan keselamatan:

- Jawaban diambil dari **basis pengetahuan tetap** berisi panduan resmi (BNPB, Kemenhut, damkar). AI hanya memilih dan merangkum, tidak mengarang.
- Isi umum: jauhi lokasi, jangan memadamkan sendiri bila api besar, lindungi pernapasan dari asap, bantu orang rentan, ikuti petunjuk petugas, hubungi nomor darurat setempat.
- Disertai disclaimer bahwa ini saran umum.
- Cakupan dibatasi pada konteks kebakaran dan penjelasan singkat sistem. Pertanyaan lain dijawab sopan di luar cakupan.
- Pesan konfirmasi selalu memuat nomor darurat karena tidak ada jalur cepat.

## 11. Status laporan (TRACK dua status)

- "Laporan belum lengkap": data minimum belum terpenuhi.
- "Laporan sudah diteruskan ke pihak berwenang": terkirim ke saluran MPA dan damkar.

Teks wajib menjelaskan bahwa status ini berarti terkirim, bukan berarti sudah ditangani, supaya warga tidak salah paham. Pelacakan progres penanganan oleh MPA atau damkar tidak termasuk cakupan versi ini (keputusan: link verifikasi MPA tidak dipakai).

## 12. Peran pengguna

- **Warga:** pelapor lewat WhatsApp.
- **Admin kota:** mengelola nomor dan alamat damkar, membuat saluran MPA sekali, membagikan tautan saluran, melihat laporan kota.
- **MPA:** anggota saluran, menerima kartu laporan (satu arah).
- **Damkar atau pihak berwenang:** menerima laporan langsung di chat, termasuk nomor pelapor bila disetujui.
- **Admin sistem (tim):** mengelola kota, admin, dan pemantauan.

## 13. Privasi dan keamanan

- Persetujuan eksplisit sebelum nomor warga diteruskan ke damkar atau pihak berwajib; simpan catatan persetujuan beserta waktu.
- Nomor pelapor tidak dikirim ke saluran MPA.
- Batas retensi data dan penghapusan atas permintaan; sebutkan kesesuaian dengan UU Pelindungan Data Pribadi di paper secara singkat.
- Foto dan lokasi dikirim ke Google Cloud Vision hanya sebatas gambar untuk Web Detection; jelaskan di kebijakan privasi.
- Peran admin per kota dengan akses terbatas; audit log aktivitas.
- Saluran dapat diikuti siapa saja dengan tautan, jadi kurangi detail sensitif di saluran.

## 14. Arsitektur teknis (ringkas)

- **Kanal warga:** WhatsApp lewat OpenClaw (adapter pengiriman dapat diganti).
- **AI:** pemahaman pesan, ekstraksi lokasi dan detail, pertanyaan klarifikasi, klasifikasi jenis kejadian, ringkasan kartu laporan.
- **Backend dan data:** mengikuti stack LaporPak sebelumnya sebagai fondasi (alur WhatsApp, AI, tiket, dasbor). Tim memutuskan ulang komponen yang dipakai.
- **Layanan tambahan:** reverse geocoding ke kota, pengambil data FIRMS, Google Cloud Vision, mesin skor, pengelola saluran dan nomor damkar.
- **Dasbor admin:** peta laporan dan hotspot, daftar laporan kota, pengaturan damkar dan saluran.

## 15. Model bisnis (B2G)

- Pelanggan: pemerintah daerah, BPBD, dinas terkait, program desa atau kota peduli api.
- Pendapatan: langganan atau kontrak per kota atau kabupaten (pengaturan, dukungan, dasbor). Komponen biaya: pesan WhatsApp, Google Cloud Vision, AI, hosting, nomor khusus.
- Pilot: satu atau dua kota rawan; cari surat dukungan atau testimoni dari MPA, BPBD, atau damkar sekecil apa pun.

## 16. Pertanyaan juri yang kemungkinan muncul dan jawaban singkat

1. **Bukankah sudah ada Posko Karhutla WhatsApp Kemenhut?** Ya. Kanal itu terpusat dan manual. Kami menambah pemahaman AI, pelengkapan data, pengarahan otomatis ke MPA dan damkar tingkat kota, penilaian kepercayaan, dan pencocokan hotspot. Kami dapat menjadi lapisan pendukung, bukan pengganti.
2. **Bagaimana dengan laporan palsu atau spam?** Skor kepercayaan multi-sinyal, label alih-alih penolakan, pembatasan laju, penggabungan klaster.
3. **Mengapa tidak cukup dengan satelit?** Latensi, jeda lintasan, resolusi, dan awan. Laporan warga melengkapi, dan kami sendiri memakai FIRMS sebagai pembanding.
4. **Bukankah gateway tidak resmi berisiko?** Benar. Kami memakainya untuk prototipe, dengan adapter yang dapat diganti dan rencana migrasi ke API resmi.
5. **Bagaimana dengan warga yang tidak bisa shareloc?** Alur cadangan nama desa lalu konfirmasi pin.
6. **Bagaimana kalau tidak ada umpan balik ke warga?** Warga mendapat konfirmasi terkirim, nomor darurat, dan saran tindakan. Pelacakan progres penanganan bukan cakupan versi ini dan dapat dikembangkan bila instansi siap berpartisipasi.
7. **Bagaimana dengan privasi?** Persetujuan eksplisit, nomor tidak ke saluran, retensi terbatas, akses admin berperan.
8. **Bagaimana skala dan biaya?** Biaya per laporan rendah (Vision gratis 1.000 gambar per bulan lalu sekitar 3,50 USD per 1.000), migrasi ke API resmi untuk produksi.

## 17. Di luar cakupan versi lomba

Fitur ASK umum, REQUEST, jalur cepat tanpa pemeriksaan kelengkapan, link verifikasi per laporan untuk MPA, dan pelacakan progres penanganan. Boleh disebut singkat di Roadmap sebagai pengembangan masa depan bila instansi bersedia, tetapi bukan bagian dari klaim saat ini.

## 18. Rencana kerja menuju 25 Oktober

Urutan prioritas tim: sistem matang, lalu paper, lalu video.

1. Uji kanal Posko Karhutla Kemenhut dan SiPongi+ (bahan Competitive Advantage).
2. Konfirmasi ketentuan domain .id di developerday.id.
3. Uji apakah OpenClaw yang dipakai dapat membuat saluran; tentukan cadangan bila tidak.
4. Bangun alur inti: pesan, kelengkapan, penentuan kota, penerusan ke saluran dan damkar.
5. Integrasi FIRMS dan Google Cloud Vision, lalu mesin skor.
6. Dasbor admin: damkar per kota, saluran MPA, peta.
7. Siapkan data dan skenario demo (lihat bagian 19).
8. Tulis paper (13 bagian, bahasa Inggris, maksimal 15 halaman).
9. Rekam video (maksimal 5 menit) dan unggah ke YouTube.

## 19. Skenario demo untuk video dan paper

1. Laporan karhutla lahan: shareloc dan foto, bot melengkapi, kartu muncul di saluran MPA, status "sudah diteruskan".
2. Laporan kebakaran permukiman: bot mengarahkan ke damkar terdekat dan memberi nomornya, laporan masuk ke chat damkar.
3. Foto yang diambil dari internet: ditandai "belum terverifikasi" oleh Vision, tetap diteruskan.
4. Laporan tanpa data lengkap: status "belum lengkap".
5. Laporan dekat hotspot FIRMS: label konfirmasi satelit.
6. Saran tindakan setelah konfirmasi.
7. Dasbor admin kota: tambah damkar, buat saluran, peta.

## 20. Hal yang masih perlu diputuskan tim

- Nama produk dan identitas visual.
- Kota atau kota-kota untuk demo dan pilot.
- Bobot skor kelengkapan dan skor kepercayaan, radius dan jendela waktu FIRMS.
- Cadangan bila saluran tidak bisa dibuat lewat OpenClaw.
- Pembagian tugas dan siapa yang menulis tiap bagian paper.
- Apakah ada kontak MPA, BPBD, atau damkar yang bisa memberi surat dukungan.

## 21. Sumber yang dipakai

- NASA Earthdata, "Data latency": https://www.earthdata.nasa.gov/learn/earth-observation-data-basics/data-latency
- NASA FIRMS (materi GOFC-GOLD, September 2024): https://gofcgold.umd.edu/sites/default/files/2024-11/DAVIES%20\_%20FIRMS%20GOFC-FIRE%20September%2024.pdf
- BMKG, halaman satelit cuaca dan hotspot: https://www.bmkg.go.id/cuaca/satelit
- BMKG, Geohotspot Himawari: https://www.bmkg.go.id/berita/kegiatan/lawatan-para-pimpinan-kementerian-lembaga-ke-riau-dan-bengkalis-untuk-memitigasi-dampak-karhutla
- UGM, studi titik panas Himawari-8 Kalimantan Tengah: https://etd.repository.ugm.ac.id/penelitian/detail/182851
- InfoPublik, Posko Karhutla Kemenhut (Oktober 2026): https://infopublik.id/kategori/bencana/993268/hotspot-karhutla-naik-kemenhut-perkuat-penanganan-di-tanjung-puting
- InfoPublik, penegasan makna hotspot: https://infopublik.id/kategori/bencana/992842/kementerian-kehutanan-perkuat-pengendalian-karhutla-di-kalteng-dan-sumsel
- SiPongi+ panduan: https://sipongi.menlhk.go.id/assets/file/panduan-sipongi.pdf
- IPB, sistem peringatan dini dan pelaporan MPA: https://repository.ipb.ac.id/handle/123456789/173938
- Google Cloud Vision, Web Detection: https://cloud.google.com/dotnet/docs/reference/Google.Cloud.Vision.V1/latest/Google.Cloud.Vision.V1.WebDetection
- Google Cloud Vision, harga: https://cloud.google.com/vision/pricing
- OpenClaw, dokumentasi kanal WhatsApp: https://docs.openclaw.ai/whatsapp
- WhatsApp Groups API (ringkasan pihak ketiga dari dokumentasi Meta): https://www.unipile.com/whatsapp-group-api/
- Baileys (library WhatsApp Web tidak resmi): https://github.com/WhiskeySockets/Baileys

*Catatan: harga, batasan API, dan kebijakan WhatsApp dapat berubah. Verifikasi ulang sebelum menulis paper.*
