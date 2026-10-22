# Spesifikasi Dashboard Admin Kota — Bot WhatsApp Pelaporan Karhutla

Diperbarui 22 Oktober 2026 berdasarkan [Knowledge Document v3](Knowledge_Doc_Terbaru_DeveloperDay_Karhutla_2026.md). Keputusan [FIX] v3 mengatasi aturan lama; enum, agregasi, dan routing yang berlabel rekomendasi belum dianggap final.

## Konteks Proyek

Sistem pelaporan kebakaran hutan, lahan, dan permukiman melalui satu nomor WhatsApp. Warga mengirim foto/video wajib, lokasi shareloc atau teks yang diperjelas, dan keterangan minimum. Pilot berfokus satu wilayah; ekspansi nasional adalah visi. AI memeriksa kelengkapan, menentukan kota/kabupaten dari koordinat, menghitung skor kepercayaan, lalu meneruskan laporan kepada penerima yang sesuai. Laporan warga melengkapi data hotspot NASA FIRMS, bukan menggantikannya.

Dashboard Admin Kota digunakan untuk memantau laporan dalam wilayah kota/kabupaten yang dikelola dan mengatur penerima laporan. Dashboard ini **bukan** sistem untuk mengelola progres pemadaman berulang atau operasi penanganan lapangan. Dashboard menampilkan konfirmasi publik berbasis lokasi dan klaim selesai bila tersedia, dengan sumber dan waktu yang jelas.

## Peran dan Batas Akses

- **Admin kota** hanya mengakses laporan dan pengaturan kota/kabupaten yang menjadi kewenangannya.
- **Warga** membuat laporan melalui WhatsApp, bukan melalui dashboard ini.
- **MPA** menerima ringkasan melalui saluran satu arah; pemegang link dapat berkontribusi melalui form publik, tanpa bukti keanggotaan MPA.
- **Pengisi link publik** dapat mengirim konfirmasi bila syarat GPS server-side radius 2 km terpenuhi; tidak otomatis menjadi petugas terautentikasi.
- **BPBD, damkar, atau pihak berwenang** menerima laporan langsung melalui chat WhatsApp, termasuk nomor pelapor hanya bila pelapor menyetujui.
- **Admin sistem** mengelola kota dan admin serta melakukan pemantauan tingkat sistem; peran ini berbeda dari Admin Kota.

## Struktur Navigasi

Lima menu utama:

1. Overview
2. Laporan
3. Peta Kebakaran
4. Pihak Berwenang
5. Saluran MPA

## 1. Overview

Halaman ringkasan kondisi laporan di wilayah admin.

### Kartu statistik

- **Laporan Hari Ini:** jumlah laporan yang masuk hari ini.
- **Sudah Diteruskan:** jumlah laporan dengan status sudah diteruskan.
- **Belum Lengkap:** jumlah laporan dengan status belum lengkap.
- **Belum Terverifikasi:** jumlah laporan yang diberi label kepercayaan belum terverifikasi.

**Catatan:** pisahkan kepercayaan AI, pengiriman, konfirmasi publik, dan klaim selesai. Tambahkan ringkasan konflik/kontribusi bila ada data. Nilai enum serta hitungan antre/hold/parsial menunggu kontrak final; jangan masukkan semua laporan belum terkirim ke kategori belum lengkap.

### Konten utama

- Peta ringkas persebaran laporan kebakaran dan hotspot NASA FIRMS.
- Daftar laporan terbaru di wilayah admin.
- Penanda yang menonjol apabila laporan menyebut orang terancam atau memerlukan evakuasi.

Data yang ditampilkan harus berasal dari sistem, bukan angka contoh atau data statis.

## 2. Laporan

Halaman untuk meninjau laporan yang diterima sistem.

### Tabel laporan

| Kolom | Konten |
| --- | --- |
| ID | Identitas unik laporan |
| Waktu | Tanggal dan jam laporan |
| Lokasi | Kota/kabupaten, kecamatan, kelurahan, dan koordinat bila tersedia |
| Jenis | Kebakaran hutan, lahan, atau permukiman |
| Kepercayaan | Skor atau label kepercayaan laporan |
| Pengiriman | Kelengkapan, antre/hold bila berlaku, tujuan sukses/gagal; enum final belum disepakati |
| Konfirmasi publik | Belum ada / mendukung / berbeda, dengan sumber dan waktu; agregasi belum final |
| Klaim selesai | Ada klaim selesai bila tersedia, bukan penutupan resmi BPBD |
| Detail | Akses ke rincian laporan |

Sediakan filter berdasarkan tanggal, kecamatan, jenis kejadian, status, dan tingkat kepercayaan.

### Detail laporan

Tampilkan informasi yang tersedia dari laporan:

- Foto atau video yang dikirim pelapor.
- Keterangan asli pelapor dan ringkasan yang dihasilkan AI.
- Lokasi pada peta dan koordinat.
- Jenis kejadian serta informasi tambahan yang terkumpul: apakah api/asap terlihat saat ini, perkiraan luas, kedekatan dengan permukiman/fasilitas penting, jenis lahan, dan ancaman terhadap orang atau kebutuhan evakuasi.
- Skor kelengkapan dan skor/label kepercayaan.
- Sinyal penilaian kepercayaan: kecocokan gambar di web, kedekatan dengan hotspot NASA FIRMS, klaster laporan serupa, reputasi nomor, dan konsistensi gambar terhadap deskripsi.
- Incident ID, tautan publik `/laporan/{slug_id}`, report sumber, dan hasil pencocokan/duplikasi.
- Kontribusi valid/invalid, waktu, sumber public_link, konflik, dan solved claim; koordinat pengisi dibatasi aksesnya.
- Tujuan penerusan laporan dan hasil/waktu pengiriman per tujuan.
- Nomor pelapor hanya jika ada persetujuan dan akses admin mengizinkan.

### Aturan status dan kepercayaan

**[FIX v3]** TRACK tidak lagi dibatasi dua status. Tampilkan tiga dimensi terpisah: pengiriman, konfirmasi lapangan publik, dan klaim selesai.

**[REKOMENDASI v3]** `delivery_status`: incomplete/held/forwarded/failed; `field_verification_summary`: none/supporting_valid/disputed/supporting_invalid; `solved_claim_status`: none/claimed_solved. Ini rancangan enum, bukan kontrak final. Antre, parsial, dan unknown tetap perlu representasi jujur melalui detail transport.

Pengiriman sukses bukan bukti kebakaran ditangani. Satu kontribusi publik bukan fakta final, satu invalid tidak otomatis membatalkan laporan, dan solved claim bukan kepastian resmi BPBD. Tanpa kontribusi, jangan menyimpulkan belum tertangani.

Aturan lama bahwa semua laporan lengkap berkepercayaan rendah tetap diteruskan digantikan keputusan routing yang masih terbuka. **[REKOMENDASI, belum disetujui]** Bedakan kanal publik dan eskalasi otoritas untuk risiko tinggi; risiko rendah/confidence rendah dapat di-hold. Definisi risiko, threshold, SLA, dan fallback perlu diputuskan sebelum implementasi. Skor rendah sendiri tidak membuktikan laporan palsu.

## 3. Peta Kebakaran

Halaman monitoring geografis untuk wilayah admin.

### Layer peta

- **Laporan warga:** penanda lokasi laporan yang masuk.
- **NASA FIRMS:** penanda hotspot berdasarkan data pengamatan satelit.

### Interaksi dan filter

- Filter periode laporan, misalnya hari ini, tujuh hari terakhir, atau rentang tanggal.
- Klik penanda laporan untuk melihat ringkasan kejadian, foto, dan tingkat kepercayaan.
- Kelompokkan laporan-laporan yang berdekatan dalam area dan jendela waktu yang sama sebagai klaster insiden untuk mengurangi duplikasi tampilan.
- Peta hanya menampilkan data dalam cakupan wilayah admin kota.
- Report sumber tetap terpisah walau dikelompokkan menjadi satu insiden. **[REKOMENDASI]** Admin dapat mengoreksi salah pengelompokan; kedekatan lokasi/waktu saja tidak membuktikan kejadian sama.

### Interpretasi data satelit

- Simpan dan tampilkan waktu pengamatan hotspot dan sensor bila relevan.
- Tampilkan label seperti **dekat hotspot terbaru** atau **belum ada hotspot** sesuai hasil pencocokan.
- Hotspot adalah indikasi anomali panas, bukan bukti pasti kebakaran.
- Tidak adanya hotspot tidak membuktikan laporan warga keliru.
- Radius dan jendela waktu pencocokan FIRMS belum final dan ditentukan setelah pengujian.

## 4. Pihak Berwenang

Halaman konfigurasi penerima laporan di kota/kabupaten terkait.

### Data penerima

- Nama BPBD, instansi berwenang, atau pos damkar.
- Nomor WhatsApp penerima; dapat lebih dari satu.
- Alamat lengkap.
- Lokasi/koordinat bila diperlukan untuk penentuan penerima terdekat.
- Status aktif atau nonaktif penerima.

### Pengaturan dan pemeriksaan

- Admin kota dapat menambah dan mengelola konfigurasi penerima di wilayahnya.
- Sediakan uji pengiriman pesan untuk memeriksa konfigurasi penerima.
- Penentuan tujuan laporan mengikuti jenis kejadian dan wilayah: kebakaran permukiman ke damkar yang sesuai; kebakaran hutan/lahan ke MPA dan pihak berwenang yang sesuai.
- Bila lebih dari satu pos damkar tersedia, penentuan penerima dapat mengikuti cakupan wilayah atau kedekatan geografis sesuai aturan sistem. Kedekatan geografis tidak otomatis berarti waktu tempuh tercepat.
- Jika suatu kota belum memiliki admin atau konfigurasi penerima, bot menggunakan alur cadangan dengan memberikan nomor Posko Karhutla nasional dan nomor darurat, bukan mengklaim laporan sudah diteruskan.

## 5. Saluran MPA

Halaman konfigurasi saluran WhatsApp MPA satu arah untuk kota/kabupaten terkait.

### Informasi saluran

- Nama saluran.
- Tautan undangan saluran.
- Status konfigurasi/koneksi saluran.

### Alur pengelolaan

- Saluran dikonfigurasi sekali di awal oleh admin kota.
- Admin menyalin tautan untuk dibagikan kepada anggota MPA.
- Kartu insiden yang memenuhi kebijakan publikasi memuat ringkasan, lokasi sesuai kebijakan privasi, dan link `/laporan/{slug_id}`. Kebijakan confidence/risiko untuk publikasi masih memerlukan keputusan tim.
- **Nomor pelapor tidak boleh dikirim ke saluran MPA.**
- Karena saluran bisa diikuti siapa saja yang memiliki tautan, informasi sensitif dan detail lokasi yang tidak perlu harus dibatasi pada pesan saluran.

### Batasan integrasi

- Rencana prototipe menggunakan OpenClaw sebagai gateway WhatsApp melalui jalur WhatsApp Web yang tidak resmi.
- Kemampuan membuat WhatsApp Channel secara otomatis melalui modul OpenClaw yang dipakai **belum terverifikasi** dan perlu pengujian.
- Bila tidak tersedia, gunakan konfigurasi saluran yang dibuat manual atau cadangan pengiriman ke grup/kontak koordinator MPA sebagaimana direncanakan.
- Lapisan pengiriman WhatsApp harus terpisah dari logika utama agar memungkinkan migrasi ke WhatsApp Business Platform resmi di tahap produksi.

## Monitoring Pengiriman Internal

Karena sistem menggunakan gateway WhatsApp untuk meneruskan laporan, admin memerlukan informasi apakah penerusan berhasil atau gagal.

- Simpan tujuan, waktu, dan hasil upaya pengiriman.
- Tampilkan indikasi kegagalan pengiriman dalam konteks laporan atau pengaturan penerima.
- Dukung percobaan ulang saat pengiriman gagal.
- Jangan menampilkan status **sudah diteruskan** kepada warga sebelum pengiriman ke penerima yang disyaratkan benar-benar berhasil.
- TRACK menggunakan hasil pengiriman aktual bersama evidensi publik dan solved claim bila tersedia; kontrak status final belum diputuskan.
- Delivery dicatat per insiden/revisi/tujuan sebagai usulan, agar beberapa report satu insiden tidak menggandakan notifikasi awal.

## Form Konfirmasi Publik dan Dampak pada Dashboard

**[FIX]** Link `/laporan/{slug_id}` bersifat publik, bukan autentikasi MPA. Satu insiden memiliki slug acak; beberapa report dapat mengacu pada insiden tersebut. Overview menampilkan tanggal, lokasi, ringkasan, foto yang memenuhi pembatasan privasi, dan klaim selesai beratribusi jika tersedia.

- Form wajib: pilihan valid/invalid dan lokasi perangkat. Deskripsi/foto opsional untuk kedua pilihan.
- Checkbox selesai hanya untuk valid, opsional, default tidak dicentang. Server tidak menyimpan solved=true untuk invalid.
- HTTPS dan GPS wajib. Server memeriksa lokasi, timestamp, accuracy, dan jarak <=2000 m dari titik kejadian. >2000 m ditolak OUT_OF_RADIUS; gagal submit bukan pilihan invalid dan tidak membuat verification_event.
- Threshold akurasi dan usia fix belum final. Jangan menyediakan bypass GPS manual publik.
- Banyak kontribusi dapat dicatat; jumlah event anonim tidak sama dengan jumlah orang independen. Agregasi konflik dan syarat pengumuman selesai belum disetujui.
- Form opsional dan tidak menjadi penghambat alur utama. Tidak ada siklus update progres berulang.
- GPS client dapat dimanipulasi. Label: konfirmasi pengguna di sekitar lokasi, bukan verifikasi petugas resmi. Jangan meminta warga mendekati api demi radius.

Dashboard menampilkan sumber/waktu konfirmasi, konflik, dan klaim selesai tanpa mengubahnya menjadi fakta final. Gagal GPS ditampilkan sebagai kegagalan teknis terpisah dari analitik valid/invalid. Metrik akurasi AI memerlukan ground truth independen; voting publik tidak cukup.

## Privasi dan Keamanan

- Simpan persetujuan warga beserta waktu persetujuan sebelum nomor pelapor diteruskan kepada pihak berwenang.
- Nomor pelapor tidak boleh ditampilkan di saluran MPA.
- Admin kota hanya mengakses data sesuai wilayah dan perannya.
- Terapkan pembatasan akses pada data laporan yang sensitif dan audit log aktivitas admin.
- Data memiliki kebijakan retensi dan penghapusan atas permintaan sesuai perencanaan perlindungan data proyek.
- Jangan mengekspos detail sensitif pada saluran maupun overview publik. Nomor/identitas pelapor dan GPS pengisi form tidak masuk payload publik. Redaksi foto, ketelitian lokasi, anti-spam, dan retensi GPS masih harus ditetapkan.
- Belum ada mitra resmi MPA/BPBD. Demo dinyatakan simulasi dan memakai nomor uji atau persetujuan eksplisit; konfigurasi nomor tidak otomatis menjadi izin menghubungi instansi.

## Prioritas Implementasi

| Prioritas | Bagian | Keterangan |
| --- | --- | --- |
| P0 | Laporan dan detail | Report/incident, pengiriman, konfirmasi dan solved claim terpisah |
| P0 | Form publik | GPS server-side radius 2 km, verification events, dan sumber TRACK |
| P0 | Pihak Berwenang | Konfigurasi tujuan penerusan ke damkar |
| P0 | Saluran MPA | Konfigurasi tujuan penerusan ke MPA |
| P1 | Overview | Ringkasan data laporan |
| P1 | Peta Kebakaran | Persebaran laporan dan hotspot FIRMS |
| P2 | Riwayat/audit pengiriman | Monitoring operasional lanjutan |
| P2 | Ekspor laporan CSV/PDF | Pengembangan berikutnya |

## Batasan Versi Lomba

- Dashboard fokus pada **pemantauan laporan** dan **pengaturan distribusi**, bukan penanganan insiden di lapangan.
- Bot berfokus REPORT dan TRACK; TRACK memuat penyaluran serta konfirmasi/solved claim bila tersedia. Enum final masih rekomendasi.
- Tidak ada ASK umum, REQUEST, jalur cepat tanpa pemeriksaan kelengkapan, autentikasi MPA berbasis kanal, atau bypass GPS publik. Link konfirmasi publik kini termasuk MVP.
- Tidak ada progres pemadaman berulang atau penutupan resmi otomatis. Klaim selesai opsional ditampilkan dengan atribusi publik.
- Tidak menetapkan bobot skor, radius pencocokan hotspot, atau jendela waktu sebagai angka final karena belum diputuskan tim.
- Jangan mengasumsikan pembuatan WhatsApp Channel otomatis telah berhasil sebelum diuji.

## Alur Demonstrasi yang Perlu Didukung

1. Warga mengirim laporan lokasi dan foto melalui WhatsApp.
2. AI meminta data yang kurang, menentukan wilayah, dan memberi label kepercayaan.
3. Laporan tampil pada daftar serta peta Admin Kota.
4. Laporan diteruskan ke penerima lokal sesuai jenis kejadian dan konfigurasi kota.
5. Admin dapat melihat tujuan dan hasil penerusan.
6. Pemegang link mengirim konfirmasi dalam radius; uji di luar radius tidak mencatat invalid kejadian.
7. Warga membaca TRACK sesuai pengiriman aktual, konfirmasi publik, konflik, dan solved claim jika tersedia.
8. Tanpa konfirmasi publik, alur laporan tetap berjalan; kasus routing hold/eskalasi diuji setelah kebijakannya disetujui.
