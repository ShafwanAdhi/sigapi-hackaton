# Knowledge Tambahan SIGAPI — Sistem dan Operasional

Dokumen ini melengkapi `Knowledge_Doc_Terbaru_DeveloperDay_Karhutla_2026.md` dengan definisi arsitektur, perilaku, aturan keputusan, serta operasional SIGAPI. Seluruh fungsi dan prosedur dijelaskan sebagai satu sistem utuh, termasuk form publik, TRACK, dashboard, peninjauan operator, dan pengelolaan data.

## 1. Tujuan, cakupan, dan prinsip sistem

SIGAPI menerima laporan kebakaran melalui WhatsApp, melengkapi informasi secara percakapan, memeriksa bukti, mengelompokkan laporan menjadi insiden, dan menyalurkan informasi ke penerima yang sesuai wilayah serta jenis kejadian. Sistem ditujukan untuk kebutuhan pemerintah daerah, BPBD, damkar, dan komunitas peduli api.

Layanan berfokus pada REPORT dan TRACK, pemeriksaan bukti, distribusi, serta konfirmasi publik berbasis lokasi. Eskalasi ancaman tinggi tetap melewati kelengkapan minimum. Percakapan umum di luar konteks layanan tidak menjadi fungsi ASK atau REQUEST tersendiri.

Prinsip pengendalian:

- AI mengekstrak klaim, mengamati media, dan membantu penjelasan. Backend menentukan kelengkapan, akses, wilayah, consent, keputusan, penerima, dan hasil pengiriman.
- Kelengkapan laporan, keputusan pemeriksaan, keberhasilan pengiriman, konfirmasi publik, dan klaim selesai disimpan sebagai dimensi terpisah.
- Bukti awal dan riwayat koreksi dipertahankan agar keputusan dapat ditelusuri.
- Data tidak diketahui tetap `unknown/null`; kegagalan pemeriksaan tetap `unavailable`.
- Ketiadaan kecocokan web, hotspot, atau EXIF tidak membuktikan laporan benar maupun palsu.
- Form publik bersifat pelengkap. Tidak adanya kontribusi publik tidak menghentikan penyaluran awal.

## 2. Wilayah, identitas, dan persetujuan

### 2.1 Wilayah layanan

Profil wilayah SIGAPI menggunakan **Kota Malang**, kode wilayah **35.73**. Penerima dan akses admin mengikuti wilayah tersebut. Routing ditentukan dari polygon administratif yang dikonfigurasi dan disetujui operator.

Pin/koordinat kejadian wajib diberikan dan dikonfirmasi pelapor. Alamat teks membantu klarifikasi; sistem tidak menggantikan pin dengan hasil tebakan atau geocoding alamat. Titik di luar wilayah, ambigu, atau tepat pada batas ditahan untuk tinjauan, tanpa menebak penerima.

### 2.2 Pemrosesan dan berbagi kontak

Alur laporan tidak menambahkan pemberitahuan atau gerbang persetujuan khusus sebelum penyimpanan dan analisis teks/media. Ketentuan ini berbeda dari izin meneruskan nomor dan izin lokasi browser.

Izin membagikan nomor ke otoritas:

- Eksplisit, opsional, dan default tidak diberikan.
- Dicatat bersama waktu, cakupan, sumber pesan, serta versi pertanyaan.
- Dapat diberikan melalui `IZIN KONTAK YA` dan dicabut melalui `IZIN KONTAK TIDAK`.
- Tidak menjadi syarat kelengkapan laporan.
- Diperiksa kembali ketika pengiriman dimulai; izin pada saat antrean dibuat tidak cukup jika kemudian dicabut.

Nomor dan identitas pelapor tidak masuk kanal komunitas atau overview publik. Akses nomor oleh admin memerlukan consent serta izin peran. Pengisi form publik tetap harus memberikan izin lokasi perangkat melalui browser.

## 3. Arsitektur dan tanggung jawab komponen

| Komponen | Tanggung jawab |
| --- | --- |
| OpenClaw dan plugin WhatsApp | Transport pesan, normalisasi identitas/input, staging media, spool persisten, serta pengiriman balasan dan distribusi. |
| FastAPI | Validasi input, transaksi penerimaan, state laporan, aturan akses, serta API internal dan publik. |
| Worker intake | Mengolah input berurutan, memeriksa media dapat dibuka, memperbarui draft dan kelengkapan. |
| Worker analisis | Ekstraksi bahasa alami, observasi media, pencarian web, FIRMS, kandidat insiden, dan pekerjaan keputusan. |
| PostgreSQL | Sumber state laporan, insiden, job, revisi, bukti, consent, audit, dan outbox. |
| Modul geospasial | Polygon wilayah, jarak, cakupan FIRMS, serta pencarian kandidat insiden. |
| Aplikasi publik | Overview insiden teredaksi dan form konfirmasi berbasis GPS. |
| Dashboard dan CLI operator | Peninjauan laporan/bukti, pengelompokan, pengaturan penerima, pemantauan dan rekonsiliasi pengiriman. |

Backend menggunakan Python/FastAPI, Pydantic, psycopg, HTTPX, Pillow dan modul geospasial. Plugin penghubung menggunakan JavaScript pada SDK OpenClaw. FFmpeg/FFprobe mendecode video. PostgreSQL tidak mewajibkan PostGIS; Haversine digunakan untuk jarak form dan GeoJSON/Shapely untuk batas wilayah.

Fungsi backend dipisahkan sebagai modul dalam satu paket. Pekerjaan persisten diambil dari database; penerimaan dan distribusi tidak hanya bergantung pada memori proses atau `BackgroundTasks`. Satu model multimodal dapat menangani ekstraksi dan observasi tanpa mewajibkan RAG, vector database, atau pelatihan model khusus.

Aplikasi publik terpisah dari aplikasi internal/operator, dengan modul dan database yang sama. HTTPS tunnel hanya membuka aplikasi publik. Gateway, dokumentasi API internal, dan token operator tetap privat.

## 4. Penerimaan pesan yang persisten

### 4.1 Integrasi OpenClaw

Plugin menggunakan `message_received` untuk observasi dan `before_dispatch` untuk mengambil alih pesan sebelum agent bawaan membalas. Tidak ada model percakapan kedua di OpenClaw yang merespons warga secara paralel. Manifest mengaktifkan plugin pada startup melalui `activation.onStartup=true`.

Pesan bot sendiri dan event tidak relevan diabaikan. Identitas pengirim berasal dari metadata transport, bukan nomor yang ditulis warga di pesan. Korelasi input memakai channel, akun, pengirim, dan provider message ID; perbedaan conversation ID antarhook tidak mengubah pemilik laporan.

### 4.2 Spool, receipt, dan replay

1. Plugin menormalisasi teks, lokasi, identitas, dan media yang telah selesai staging.
2. Envelope serta salinan media ditulis atomik ke spool privat dengan ID event stabil.
3. Plugin mengirim input ke API internal.
4. API memberi HTTP **202 setelah event dan job commit dalam satu transaksi**.
5. Spool dibersihkan setelah penerimaan database dikonfirmasi. Timeout penerimaan dapat mengulang ID yang sama.

Replay tidak membuat report, job, atau balasan ganda. Kontrak transport WhatsApp memakai kunci unik `(account_id, provider_message_id)`; envelope juga menyimpan identitas provider untuk membedakan sumber transport.

Jika API tidak dapat dihubungi, bot menyatakan input berada dalam antrean lokal. Spool diputar ulang sesuai urutan penerimaan. Perlindungan spool berlaku setelah pesan diterima plugin; sistem tidak menjanjikan pemulihan pesan yang belum sampai ke gateway.

Mutasi diserialisasi per akun/pengirim. Job menggunakan locking, lease dan token agar worker lama tidak menulis setelah pekerjaan diambil alih. Analisis terikat ke revisi serta urutan input; hasil lama tidak menimpa koreksi atau memicu pengiriman snapshot lama.

### 4.3 Batas input

| Input | Batas |
| --- | --- |
| Teks | 4.000 karakter. |
| Media per pesan | 10 media. |
| Spool pending | 500 pesan / 256 MB. |
| Foto | 10 MB. |
| Video | 20 MB dan 30 detik. |

Jenis file diperiksa melalui decode, bukan ekstensi/header saja. Media memakai ID buatan server, bukan path/URL yang dipilih pelapor. Berkas tidak dapat dibuka atau melebihi batas diminta ulang. Input yang gagal disimpan tidak diakui sebagai laporan tersimpan.

Payload yang ditolak permanen masuk penanganan operator. Kegagalan satu pengirim tidak menahan seluruh pengirim lain.

## 5. Percakapan REPORT dan pembentukan laporan

Satu pengirim memiliki satu draft aktif. Pesan teks, caption, foto/video, pin dan jawaban berikutnya digabung ke draft milik pengirim tersebut. Jika ada kejadian baru, bot meminta pilihan melanjutkan atau membuat laporan baru; dua lokasi tidak digabung diam-diam.

| Input | Fungsi |
| --- | --- |
| `REPORT` | Memulai laporan atau memilih pengelolaan laporan aktif. |
| `LANJUT` / `BARU` | Melanjutkan draft atau membuat laporan terpisah. |
| Bahasa alami/caption | Mengisi keterangan, kategori, klaim waktu dan ancaman berdasarkan sumber. |
| `KETERANGAN: ...` | Jalur eksplisit pengisian keterangan; prefix tidak wajib untuk percakapan alami. |
| Pin native WhatsApp | Memberikan kandidat titik kejadian. |
| `KONFIRMASI LOKASI n` | Mengonfirmasi versi pin yang diminta bot. |
| `IZIN KONTAK YA/TIDAK` | Memberikan, menolak atau mencabut izin berbagi nomor. |
| `STATUS` | Membaca kelengkapan, pemeriksaan dan pengiriman tersimpan. |
| `TRACK [ID]` | Membaca status laporan, kontribusi publik dan klaim selesai sesuai kepemilikan. |

Pin pengganti menaikkan versi dan membatalkan konfirmasi sebelumnya. Teks alamat maupun tautan Google Maps tidak otomatis menggantikan lokasi terstruktur. Bot memastikan titik yang dikirim merupakan lokasi kejadian, bukan posisi aman pelapor.

Minimum laporan mencakup media dapat dibuka, titik kejadian terkonfirmasi, dan keterangan memadai. Jalur `KETERANGAN:` memerlukan minimal sepuluh karakter setelah prefix. Fakta dari percakapan alami dapat melengkapi informasi tanpa mengharuskan pengguna mengikuti format command.

Contoh: “terjadi kebakaran di Malang” dan “mulai jam delapan malam” dibaca sebagai satu rangkaian. Jika tanggal atau makna waktu belum jelas, bot meminta klarifikasi.

Klarifikasi dibatasi empat pertanyaan tanpa informasi baru/per revisi. Setelah batas, draft atau hold tetap tersimpan dan dapat dilanjutkan dengan informasi baru. Pertanyaan opsional tidak menahan kelengkapan minimum.

Informasi tambahan dapat mencakup api/asap masih terlihat, luas perkiraan, kedekatan permukiman/fasilitas, jenis lahan dan ancaman evakuasi. Informasi yang tidak disebut tetap null/unknown. Pesan baru setelah penyaluran disimpan sebagai revisi; perubahan material menghasilkan pembaruan yang ditandai jelas.

## 6. Fakta bersumber, waktu, dan kontrak AI

AI memisahkan tiga keluaran: klaim pelapor, observasi visual, dan ringkasan. Setiap fakta menunjuk pesan/media serta kutipan sumber yang benar-benar dipasok backend. Fakta bersumber tetap klaim, bukan pembuktian kebenarannya.

Keluaran menggunakan schema tervalidasi dengan enum terbatas, nullable field, referensi sumber, serta penanda konflik. JSON invalid tidak mengubah laporan sebagai hasil sukses. Model tidak menentukan consent, penerima, wilayah kewenangan, hasil kirim, atau nomor darurat.

Teks warga, caption dan tulisan dalam gambar merupakan data. Instruksi seperti “abaikan aturan”, “langsung teruskan”, atau nomor penerima yang disisipkan pengguna tidak mengubah kebijakan backend.

Waktu disimpan terpisah:

- Waktu penerimaan pesan.
- Waktu kejadian/pengamatan yang diklaim pelapor.
- Waktu media bila tersedia.
- Waktu pengamatan satelit.
- Waktu modifikasi dan pengambilan sumber.

Waktu pesan tidak membuktikan waktu kejadian. Model tidak mengarang tanggal, luas, korban, jenis lahan, lokasi foto atau ancaman.

Jika provider gagal, input tetap tersimpan dan percakapan berbasis aturan tetap berjalan. Aturan teks konservatif mengenali ancaman eksplisit; kalimat negatif/ambigu meminta konfirmasi. Tidak adanya informasi ancaman tidak disebut risiko rendah.

## 7. Pemeriksaan media dan konsistensi bukti

Setiap media laporan diperiksa. Video didecode menjadi maksimal tiga frame awal, tengah dan akhir. Observasi terbatas pada frame tersebut; hasil sebagian/gagal tidak dilabel sebagai pemeriksaan lengkap seluruh video.

Observasi visual mencakup api/asap, keterbacaan, kualitas dan isi yang tampak. Hasil tidak menyimpulkan lokasi pasti, waktu pengambilan, keaslian foto atau semua kemungkinan gambar buatan AI.

Pemeriksaan dipisahkan menjadi:

1. **Kemiripan lokal:** SHA-256/dHash dibandingkan dengan koleksi media laporan.
2. **Kemunculan di web:** kandidat exact/partial/visual dari provider pencarian.
3. **Konsistensi lintas sumber:** isi media, caption, keterangan, klaim lokasi/waktu dan bukti lain yang tersedia.

Konsistensi dicatat sebagai dukungan, konflik, atau informasi tidak cukup, dengan alasan dan referensi sumber. Foto hutan dan pin perkotaan saja tidak cukup membuktikan konflik. Koordinat laporan tidak membuktikan lokasi foto.

EXIF opsional. Jika tersedia, metadata menjadi bukti tambahan; jika hilang, atribut terkait `unavailable/unknown`. Ketiadaan EXIF sendiri tidak menahan laporan dan tidak dianggap konsisten/autentik.

Fingerprint laporan terpisah dari koleksi uji operator. Media tidak menghitung dirinya sebagai duplikat. SHA identik berarti berkas sama; dHash hanya kandidat kemiripan, dengan keterbatasan crop/kompresi.

Setiap hasil menyimpan report/revision, media/frame, jenis pemeriksaan, outcome, alasan, source refs, checked time, hash, serta model/prompt/rule/check version. Revisi baru tidak menghapus bukti lama.

## 8. Pencarian web dan fallback

Groq melakukan ekstraksi dan observasi. **SerpApi Google Lens** menjadi pencarian web utama. **Google Cloud Vision** tersedia sebagai fallback opt-in melalui `ENABLE_GOOGLE_VISION=true`; default tidak aktif.

Alur web:

1. Decode media dan buat JPEG turunan tanpa EXIF, maksimal **450.000 byte** dan sisi **1280 px**.
2. Unggah turunan ke SerpApi Image API untuk memperoleh `image_id`.
3. Cari `exact_matches`; jika kosong, lanjutkan `visual_matches`.
4. Kandidat exact/partial yang menimbulkan konflik memicu klarifikasi/review.
5. Jika SerpApi gagal, tidak dikonfigurasi atau kuota habis, Vision dapat dipakai bila diaktifkan.
6. Jika semua pemeriksaan web gagal, hasil `unavailable`, review manual pending dan komunitas ditahan.

Fallback tidak dijalankan untuk mengganti temuan konflik dengan hasil yang lebih menguntungkan. Bukti/kegagalan sebelumnya dipertahankan. Kemiripan visual adalah sinyal lemah; no-match bukan label autentik.

SerpApi menerima gambar sebagai pihak ketiga; aplikasi tidak menghosting media asli secara publik. Hasil memakai whitelist link/title/source, waktu, versi dan hash. URL hanya HTTP(S) tanpa credential, tidak di-fetch backend. Respons vendor mentah dan secret tidak dicetak. Referensi kandidat dibatasi penyimpanannya; jumlah kandidat bukan skor kebenaran.

Review manual dapat menggunakan Lens/TinEye melalui browser. Review pending dan hash lokal tidak menyelesaikan kewajiban pemeriksaan web. Operator menyimpan hasil review dengan bukti/alasan, tanpa menghapus temuan awal.

## 9. Provider, budget, cache, dan retry

Model diatur melalui konfigurasi. Profil Groq menggunakan `GROQ_VISION_MODEL`; `GROQ_TEXT_MODEL` opsional dan default mengikuti model vision. Profil model yang tercantum pada dokumentasi adalah `qwen/qwen3.8-27b` dengan input gambar dan JSON mode. Pemilihan model mengikuti kemampuan dan akses akun yang dikonfigurasi.

| Kontrol | Ketentuan |
| --- | --- |
| Konkurensi Groq | Satu panggilan aktif. |
| Pacing Groq | Minimal 35 detik antarwaktu mulai request. |
| Retry | Maksimal tiga percobaan HTTP per operasi; hitungan persisten melintasi restart. |
| Error retryable | Timeout, 429 dan 5xx; backoff 2 lalu 5 detik, disertai pacing provider. |
| Timeout request | Profil 30 detik per request. |
| Budget SerpApi | 50 operasi HTTP, termasuk upload dan retry, pada counter persisten. |
| Budget Vision | 50 percobaan, termasuk retry, terpisah dari budget SerpApi. |
| Cache | Hasil sukses menurut hash asli dan versi provider/model/prompt; kegagalan tidak di-cache. |

Budget aplikasi lebih ketat daripada kredit vendor. Counter tidak dihapus untuk mengulang kuota. Kuota akun juga dipengaruhi pemakaian proses/aplikasi lain. Tiga frame video memakai tiga analisis; batas token dapat tercapai sebelum batas request. Pacing tetap diperlukan meskipun retry singkat tersedia.

Kegagalan akses/billing langsung dicatat sebagai unavailable; tidak dianggap hasil negatif atau lolos. Vision memerlukan project, API, billing serta ADC lokal yang sah. Aplikasi tidak mengaktifkan billing otomatis; budget alert vendor tidak dianggap hard spending cap.

Pemantauan biaya memisahkan operasi upload, pencarian, percobaan ulang, cache hit, token input/output dan jumlah media/frame. Kuota/harga vendor dibaca dari akun serta ketentuan layanan yang berlaku, bukan diasumsikan tetap dari tabel harga lama.

## 10. FIRMS, wilayah, dan provenance

FIRMS menggunakan snapshot bersumber nyata, termasuk CSV NASA VIIRS 48 jam. Snapshot menyimpan sumber, sensor, waktu pengamatan, waktu modifikasi sumber, waktu pengambilan, hash serta cakupan area/waktu. Snapshot ditampilkan sebagai data tersimpan dengan waktunya.

Profil pencocokan:

- Radius hotspot **3 km** dari titik kejadian.
- Selisih pengamatan maksimal **24 jam** terhadap waktu kejadian.
- Usia sumber dan pengambilan maksimal **24 jam**.
- Awal cakupan memadai untuk 24 jam sebelum kejadian.
- Akhir cakupan mengikuti waktu sumber, bukan waktu download atau pengamatan masa depan.

Hasil dibedakan menjadi `matched`, `no_match`, `unavailable`, dan `not_checked`. Kejadian lebih baru daripada cakupan sumber, area tidak tercakup, sumber usang atau gagal menghasilkan unavailable. `no_match` hanya dinyatakan setelah cakupan memadai.

FIRMS tidak wajib menemukan hotspot agar laporan layak disalurkan, tetapi pemeriksaannya harus tersedia untuk jalur komunitas. Ketiadaan hotspot tidak menjadi label palsu. Snapshot diperbarui dengan unduhan baru, bukan mengganti timestamp file lama.

Wilayah menggunakan GeoJSON dengan sumber, versi, kode administratif dan hash. Profil Kota Malang mencakup sumber OpenStreetMap relation `9674151`; operator memeriksa kesesuaiannya. Data OSM tidak disebut sertifikasi pemerintah. Persetujuan terikat hash dan dibatalkan ketika file batas diunduh ulang.

Bounding box tidak menggantikan polygon administratif. Reverse geocoding hanya membantu label alamat; tidak menetapkan kewenangan atau menggantikan titik kejadian terkonfirmasi.

## 11. Aturan keputusan dan eskalasi

| Kondisi | Tindakan sistem |
| --- | --- |
| Data minimum belum lengkap | Meminta kelengkapan dan memberi panduan keselamatan sesuai konteks. |
| Ada kandidat reuse web | Klarifikasi/review; tahan komunitas selama konflik terbuka. |
| Media bertentangan atau pemeriksaan wajib gagal/parsial | Tahan komunitas dan simpan alasan. |
| FIRMS unavailable/usang | Tahan komunitas. |
| Ancaman tinggi eksplisit, minimum lengkap, titik terkonfirmasi dalam wilayah | Eskalasi otoritas dengan label **BELUM TERVERIFIKASI** dan alasan ketidakpastian. |
| Pemeriksaan wajib tersedia, media api/asap jelas, waktu dapat diperiksa, konflik tertutup dan grouping selesai | Layak distribusi awal sesuai kategori dan penerima. |
| Titik di luar/ambigu wilayah | Simpan dan tinjau tanpa menebak penerima. |

Ancaman tinggi mencakup orang terancam/terjebak, kebutuhan evakuasi atau api mengancam rumah/fasilitas. Klaim harus memiliki sumber. Jalur ini tidak harus menunggu seluruh pemeriksaan web/FIRMS selesai, tetapi tidak melewati minimum laporan dan syarat wilayah.

Hold tidak mempunyai timer penerusan otomatis. Pernyataan “foto ini asli” saja tidak menghapus kecocokan web. Operator atau informasi baru harus memberikan dasar perubahan keputusan.

Keputusan menggunakan kode alasan dan referensi bukti, tanpa persentase probabilitas kebenaran. Nomor baru tidak dihukum; reputasi tanpa riwayat memadai berstatus `insufficient_history`. Banyak laporan serupa tidak otomatis berarti banyak saksi independen.

## 12. Insiden dan koreksi pengelompokan

Kandidat insiden dicari dalam **500 meter dan enam jam**. AI menjelaskan kemiripan; operator mengonfirmasi penggabungan. Jika tidak ada kandidat, sistem membuat insiden baru. Kandidat belum diputuskan menahan distribusi komunitas untuk mencegah notifikasi awal ganda.

Setiap report tetap mempunyai pemilik, sumber, bukti dan revisinya sendiri. Penggabungan tidak menghapus report sumber. Pemisahan atau koreksi diaudit dan membatalkan antrean lama yang belum dikirim.

Insiden mempunyai slug acak **128-bit** dan satu link kanonik `/laporan/{slug_id}`. Report yang tergabung mengacu ke link insiden tersebut. Koreksi titik kejadian membawa revisi dan waktu; radius form dihitung terhadap titik kejadian, bukan centroid yang berubah setelah merge.

Routing mengikuti jenis kejadian: hutan/lahan dapat menuju komunitas dan otoritas; kebakaran bangunan/permukiman menuju otoritas yang dikonfigurasi. Kedekatan lokasi/waktu saja tidak membuktikan dua kebakaran merupakan satu kejadian.

## 13. Distribusi dan kepastian hasil kirim

### 13.1 Penerima dan payload

Penerima berasal dari konfigurasi wilayah/jenis, bukan keluaran bebas model. Daftar izin pengirim masuk terpisah dari penerima keluar: `allowSenders`/`allowFrom` untuk inbound dan `outboundRecipients` untuk outbound.

Kartu keluar berupa teks terstruktur: label laporan warga/pemeriksaan awal, kategori, ringkasan fakta, titik, waktu, bukti/ketidakpastian, serta link insiden. Eskalasi menggunakan label BELUM TERVERIFIKASI. Teks mentah, identitas pelapor dan media asli tidak diteruskan ke komunitas.

Nomor hanya masuk kartu otoritas ketika consent masih aktif. Sebelum kirim, sistem memeriksa revisi, urutan input, keputusan, wilayah, tujuan, konfigurasi dan consent terbaru. Payload dibuat dari admission yang baru, bukan snapshot usang.

### 13.2 Outbox dan rekonsiliasi

Delivery dibedakan menurut insiden, revisi, tujuan dan jenis pesan. Report tambahan dalam insiden sama tidak menggandakan notifikasi awal; perubahan material menjadi pembaruan. Tujuan yang sudah sukses tidak diulang ketika memperbaiki tujuan gagal.

Status teknis mencakup `pending/sending/sent/failed/unknown/unroutable`. Keberhasilan memerlukan hasil provider/receipt WhatsApp valid yang tersimpan; HTTP 200 saja tidak cukup. Keberhasilan sebagian tujuan wajib tidak disebut seluruh penyaluran berhasil.

Timeout setelah kirim dimulai menghasilkan `unknown`, tanpa retry otomatis. Operator memeriksa riwayat WhatsApp/log dan mencatat receipt atau mengizinkan retry setelah dipastikan belum terkirim. Aturan ini juga berlaku pada balasan outbox. Pesan berikutnya tetap dapat diproses.

Idempotensi internal tidak dijanjikan sebagai exactly-once WhatsApp. Batas distribusi **lima pesan per sepuluh menit per tujuan**; sisanya tetap mengantre. Pelapor menerima status sesuai hasil nyata; receipt kirim tidak berarti petugas sudah menangani kebakaran.

## 14. Form konfirmasi publik berbasis GPS

Pemegang link `/laporan/{slug_id}` melihat overview insiden teredaksi: ringkasan, waktu, lokasi, foto yang aman dipublikasikan dan klaim selesai jika ada. Foto publik berupa turunan yang disetujui operator; asli tetap privat. Jika tidak ada foto aman, sistem menampilkan placeholder beralasan.

Form memuat pilihan wajib valid/invalid, lokasi browser wajib, deskripsi opsional, foto opsional, dan checkbox selesai yang hanya muncul untuk valid. Checkbox default tidak dicentang. Server menormalkan invalid+solved menjadi false.

| Pemeriksaan submit | Aturan |
| --- | --- |
| Transport | HTTPS dan izin lokasi browser. |
| Koordinat | Finite dan dalam rentang latitude/longitude sah. |
| Jarak | Maksimal **2.000 meter** dari titik kejadian. |
| Accuracy | Lebih dari nol dan maksimal **100 meter**. |
| Usia fix | Maksimal **60 detik** terhadap waktu server. |
| Timestamp masa depan | Lebih dari **lima detik** di masa depan ditolak. |
| Deskripsi | Maksimal **2.000 karakter**, opsional. |
| Foto | Maksimal **10 MB**, opsional, dengan validasi decode dan body upload. |
| Replay jaringan | `request_id` mencegah submit jaringan yang sama disimpan berulang. |
| Rate limit | **10 upaya per 10 menit per IP+slug**, memakai counter database. |

Di luar radius menghasilkan HTTP 422 `OUT_OF_RADIUS`. Kode lokasi lain meliputi `INVALID_LOCATION`, `STALE_LOCATION` dan `INACCURATE_LOCATION`. Kegagalan syarat teknis tidak membuat verification event dan tidak menjadi pilihan invalid terhadap kejadian.

Request ID dan rate limit tidak membuktikan satu orang unik. GPS client dapat dimanipulasi; form mengumpulkan konfirmasi dari pemegang link yang memenuhi pemeriksaan koordinat, bukan autentikasi petugas MPA.

GPS pengisi, identitas/nomor pelapor, EXIF lokasi serta akses media asli tidak masuk payload publik. Banyak kontribusi disimpan masing-masing. Sistem tidak meminta pengisi mendekati api demi memenuhi radius.

## 15. TRACK, agregasi, dan interpretasi status

TRACK membaca database tanpa meminta model mengarang status. Tanpa ID, pengguna mengakses pilihan/laporan miliknya. ID tidak ditemukan dan ID milik orang lain menghasilkan jawaban aman yang sama agar keberadaan laporan tidak bocor.

| Dimensi | Contoh status | Interpretasi |
| --- | --- | --- |
| Kelengkapan | Draft / complete | Minimum administratif laporan. |
| Keputusan | Held / eligible / eskalasi terlabel | Hasil pemeriksaan dan aturan routing. |
| Pengiriman | Antre / sending / sent / failed / unknown / unroutable | Hasil teknis per tujuan. |
| Konfirmasi publik | None / supporting_valid / supporting_invalid / disputed | Ringkasan kontribusi yang tersimpan. |
| Klaim selesai | None / claimed_solved | Ada pengguna menyatakan kejadian telah selesai. |

Satu valid ditampilkan sebagai dukungan berbasis lokasi. Satu invalid merupakan kontribusi berlawanan, bukan pembatalan otomatis. Kontribusi valid dan invalid bersama-sama menghasilkan disputed. Valid+solved menghasilkan claimed_solved dengan sumber/waktu, tanpa menghapus konflik atau menutup insiden secara resmi.

Contoh penyampaian:

- “Laporan diteruskan ke tujuan yang tercatat. Belum ada konfirmasi kondisi lapangan pada sistem.”
- “Terdapat konfirmasi dari pengguna yang memenuhi pemeriksaan lokasi.”
- “Konfirmasi lapangan berbeda-beda; belum ada kesimpulan.”
- “Ada pengguna melaporkan kejadian telah selesai pada waktu berikut. Ini bukan konfirmasi resmi penutupan oleh BPBD.”

Tidak adanya solved claim tidak berarti kejadian belum tertangani. Layanan tidak melacak progres pemadaman berulang atau mengarang tindakan petugas.

## 16. Dashboard Admin Kota

Dashboard memantau laporan dan distribusi sesuai wilayah kewenangan. Admin Kota mengelola data/penerima wilayahnya; Admin Sistem mengelola wilayah, akun admin dan pemantauan sistem. Scope wilayah/peran diterapkan di server.

### 16.1 Overview

Empat ringkasan utama: Laporan Hari Ini, Sudah Diteruskan, Belum Lengkap, dan Belum Terverifikasi. Data diambil dari state sistem. Laporan antre, held dan unknown tidak semuanya dihitung sebagai belum lengkap.

Overview memuat peta ringkas laporan/hotspot, daftar terbaru, konflik/kontribusi jika ada, serta penanda menonjol untuk ancaman terhadap orang atau evakuasi.

### 16.2 Laporan

Daftar memuat ID, waktu, wilayah/koordinat, kategori, alasan/label keputusan, hasil pengiriman tiap tujuan, konfirmasi publik, klaim selesai dan akses detail. Filter mencakup tanggal, kecamatan, jenis, status dan label pemeriksaan.

Detail memuat media dengan akses terbatas, keterangan asli, ringkasan AI, peta, fakta/kutipan sumber, waktu, bukti lokal/web/FIRMS/konsistensi, incident ID, report sumber, hasil grouping, kontribusi publik dan audit pengiriman. Nomor pelapor memerlukan consent serta izin peran. GPS pengisi tidak dibuka ke publik.

### 16.3 Peta Kebakaran

Layer laporan warga dan hotspot FIRMS ditampilkan terpisah. Filter periode mendukung hari ini, tujuh hari atau rentang tanggal. Klik marker menampilkan ringkasan, foto aman dan label pemeriksaan.

Klaster insiden mengurangi penanda ganda; report sumber tetap dapat ditelusuri. Peta hanya mencakup wilayah admin. Sensor/waktu pengamatan hotspot ikut ditampilkan agar data satelit tidak dibaca sebagai kondisi tanpa batas waktu.

### 16.4 Pihak Berwenang

Konfigurasi mencakup nama instansi/pos, nomor E.164, alamat, koordinat bila relevan, cakupan wilayah, jenis penerima, akun transport dan status aktif. Satu wilayah dapat mempunyai beberapa penerima.

Pemilihan mengikuti wilayah dan kategori. Jarak geografis dapat menjadi pertimbangan, tetapi tidak diklaim sebagai waktu tempuh tercepat. Uji kirim hanya menggunakan penerima yang diotorisasi. Jika penerima tidak tersedia, sistem menyampaikan kendala routing dan kontak cadangan terverifikasi tanpa mengklaim penerusan berhasil.

### 16.5 Saluran MPA

Admin mengelola nama saluran, tautan undangan dan status koneksi. Transport komunitas dapat berupa Channel, grup atau kontak koordinator yang dikonfigurasi. Pembuatan Channel otomatis bukan prasyarat; saluran dapat dibuat manual dan didaftarkan.

Payload komunitas mengikuti aturan privasi yang sama pada seluruh transport. Nomor pelapor tidak ikut disertakan. Tautan saluran tidak membuktikan identitas MPA pemegang link.

### 16.6 Monitoring dan audit

Admin/operator melihat waktu upaya, hasil per tujuan, antrean, hold, failed/unknown/unroutable, alasan keputusan dan audit. Pengubahan penerima, consent, review, grouping serta retry dapat ditelusuri. Ekspor laporan mengikuti scope wilayah/peran dan tidak otomatis memasukkan field sensitif.

## 17. Panduan keselamatan dan batas penjelasan bot

Saat data belum lengkap atau ada ancaman tinggi, bot memberi arahan keselamatan singkat: menjaga jarak aman, tidak mendekati api untuk mengambil bukti, tidak memadamkan api besar sendiri, mengurangi paparan asap, membantu kelompok rentan dan mengikuti petugas.

Panduan bersumber dari basis pengetahuan tetap yang mengacu pada lembaga resmi. AI hanya memilih/merangkum materi relevan. Nomor layanan darurat berasal dari konfigurasi yang telah diverifikasi, tidak digenerasikan oleh model.

Pelapor dengan ancaman terhadap jiwa/permukiman diarahkan menghubungi layanan darurat secara langsung. Bot tetap menjelaskan bahwa status penerimaan atau pengiriman tidak menjamin petugas sedang menuju lokasi. Penjelasan sistem dan tindakan sambil menunggu dibatasi pada konteks kebakaran.

## 18. Keamanan, privasi, dan retensi

API internal menggunakan token layanan, hanya loopback pada profil satu host. Token internal/gateway minimal 32 karakter dan disimpan privat. Jika lintas host, koneksi internal menggunakan TLS. Konten warga tidak mempunyai akses shell, filesystem umum, browser operator atau pengubahan konfigurasi.

Validasi batas layanan mencakup schema, panjang teks, koordinat, ukuran, MIME/decode, path dan URL. Staging hanya dari root terkontrol; traversal dan URL media arbitrer ditolak untuk mencegah akses berkas serta SSRF.

Provider hanya menerima teks/media yang diperlukan tanpa identitas transport yang tidak relevan. Endpoint gateway, credential sesi, QR, DSN, media asli, spool, database dump dan log sensitif tetap privat. Secret tidak masuk prompt, respons publik, screenshot operasional atau repository.

Akses dashboard/inspeksi mengikuti peran dan wilayah. Media detail menggunakan akses terautentikasi atau tautan terbatas. Ekspor inspeksi disimpan privat karena mengandung data pribadi. Audit mencatat tindakan operator tanpa mencetak credential.

Profil retensi menyimpan input/media/GPS/spool/log sensitif maksimal **tujuh hari**, dengan cakupan penghapusan mempertimbangkan database, transcript dan backup. Operator menjalankan purge eksplisit sesuai kebijakan; purge tidak berjalan otomatis saat startup dan tidak menghapus konfigurasi/credential.

Permintaan penghapusan memeriksa kepemilikan dan dicatat dalam audit. Penghapusan data internal tidak menjanjikan penghapusan seluruh salinan yang sudah dikirim kepada penerima eksternal. Data laporan tidak dialihkan menjadi dataset training tanpa persetujuan yang sesuai.

Retensi per jenis data, redaksi foto, ketelitian lokasi publik, akses backup dan kebijakan pemrosesan provider merupakan parameter operasional yang ditetapkan pada konfigurasi/kebijakan layanan. Tidak ada angka SLA, RPO atau RTO yang diasumsikan tanpa penetapan.

## 19. Operasional layanan dan prosedur operator

### 19.1 Bootstrap dan konfigurasi

Runtime/dependensi dipin untuk pemasangan yang dapat diulang. Profil instalasi menggunakan Python 3.11, Node lokal 26.12.1, OpenClaw dan plugin WhatsApp 2026.10.6, serta FFmpeg/FFprobe 9.0.2. Node/FFmpeg lokal tidak mengharuskan perubahan versi global atau PATH sistem.

Konfigurasi privat mencakup key/model provider, token internal/gateway, DSN database, akun bot, izin inbound/outbound, wilayah, sumber FIRMS, tujuan dan flag distribusi. Perintah konfigurasi tidak menimpa konfigurasi lama tanpa tindakan operator yang sesuai. Pairing WhatsApp dilakukan melalui QR lokal; sesi tersimpan dipakai kembali.

Database pengujian dipisahkan dari database operasional; role aplikasi bukan superuser. Profil lokal menggunakan database loopback 55432 dan API internal `127.0.0.1:8011`. Deployment lintas host mempertahankan batas akses dan autentikasi yang sama.

### 19.2 Startup, migrasi, dan shutdown

Operator menyiapkan database, menjalankan migrasi idempoten dan memeriksa konfigurasi sebelum memulai API, worker intake, worker analisis serta gateway. Aplikasi publik dijalankan terpisah. Satu akun hanya memakai satu gateway aktif.

```powershell
.\.venv\Scripts\python.exe -m backend.cli db-start
.\.venv\Scripts\python.exe -m backend.cli migrate
```

Empat proses berikut dijalankan pada terminal/proses layanan masing-masing:

```powershell
.\.venv\Scripts\python.exe -m backend.cli serve
.\.venv\Scripts\python.exe -m backend.cli worker
.\.venv\Scripts\python.exe -m backend.cli analysis-worker
.\.venv\Scripts\python.exe -m backend.cli openclaw -- gateway run
```

Migrasi menghormati versi skema yang telah diterapkan, mempertahankan data, dan tidak otomatis menganalisis/mengirim laporan lama. Operator menghentikan proses miliknya melalui terminal saat shutdown/restart. Runtime tidak dihapus untuk restart. Perubahan plugin/manifest memerlukan pemuatan ulang gateway.

### 19.3 Aktivasi wilayah dan penerima

Sebelum distribusi diaktifkan, operator:

1. Memeriksa identitas bot, pengirim yang diizinkan, akun transport dan penerima.
2. Menentukan tujuan komunitas/otoritas yang sah untuk wilayah serta jenis kejadian.
3. Memisahkan izin inbound/outbound; untuk simulasi, dua penerima uji berbeda satu sama lain, bot dan pelapor.
4. Mengunduh/memeriksa polygon, provenance, kode wilayah, bentuk batas dan titik operasional.
5. Menyetujui SHA-256 file batas dengan alasan tercatat.
6. Memperbarui FIRMS dan memeriksa cakupannya.
7. Mengaktifkan `distribution_enabled` setelah prasyarat terpenuhi.

Pengiriman membaca ulang konfigurasi saat admission. Unduhan ulang batas menghapus persetujuan hash lama. Perubahan penerima/aktivasi diaudit. Nomor pada konfigurasi tidak otomatis menjadi izin menghubungi instansi tanpa otorisasi yang sesuai.

### 19.4 Monitoring harian dan readiness

Operator memantau koneksi database/gateway, status provider terakhir, usia/cakupan FIRMS, kapasitas spool, job dan outbox, report held, rate limit, budget, cache hit, serta failed/unknown/unroutable. Tampilan memakai data aktual.

`readiness` memeriksa konfigurasi/komponen. `intake-status` menyajikan jumlah/status tanpa identitas/isi laporan. Indikator kesiapan tidak menggantikan receipt per pengiriman.

Log diagnosis membedakan `FACTS_NOT_FOUND`, `BACKEND_HTTP_<status>`, `INVALID_BACKEND_RESULT` dan `BACKEND_REQUEST_FAILED` tanpa merekam secret atau isi pesan. Inspeksi plugin memeriksa import serta hooks `message_received` dan `before_dispatch`; listener dan uji pesan terotorisasi memeriksa jalur transport.

Ambang peringatan, jadwal refresh, pembagian petugas dan SLA tinjauan mengikuti kebijakan operasional wilayah. Hold tidak diubah menjadi penerusan otomatis hanya karena waktu berlalu.

### 19.5 Peninjauan bukti dan insiden

Operator membuka report dengan UUID lengkap dan mengekspor inspeksi hanya ke penyimpanan privat. Analisis laporan lama/ulang dijalankan secara eksplisit. Review bukti menunjuk media/frame/evidence key yang benar, alasan dan referensi pendukung.

```powershell
.\.venv\Scripts\python.exe -m backend.cli report-inspect UUID_LAPORAN --output .runtime/inspection.json
.\.venv\Scripts\python.exe -m backend.cli analyze UUID_LAPORAN
.\.venv\Scripts\python.exe -m backend.cli review-evidence UUID_LAPORAN --key UUID_MEDIA:0 --reason "Alasan review" --reference https://sumber-bukti.example/halaman
.\.venv\Scripts\python.exe -m backend.cli review-incident UUID_LAPORAN --merge-into UUID_KANDIDAT --reason "Dasar pengelompokan"
.\.venv\Scripts\python.exe -m backend.cli review-incident UUID_LAPORAN --reason "Dasar kejadian terpisah"
```

Pengelompokan ulang menjaga sumber/bukti awal serta audit. Koreksi waktu/lokasi mengharuskan evaluasi terhadap acuan insiden terbaru dan membatalkan antrean usang.

### 19.6 Gangguan dan pemulihan

| Gangguan | Tindakan sistem/operator |
| --- | --- |
| API mati | Spool privat menahan input yang telah diterima; replay berurutan setelah API pulih. |
| Worker restart | Job belum selesai diambil kembali melalui lease/token; hasil worker usang ditolak. |
| Provider lambat/429 | Intake tetap berjalan; analisis mengikuti pacing, retry persisten dan budget. |
| Provider gagal/JSON invalid | Simpan unavailable; percakapan aturan dan kebijakan hold/eskalasi tetap berlaku. |
| FIRMS usang/tidak mencakup | Unduh sumber baru; jangan mengubah timestamp atau menyatakan no-match. |
| Media/video sebagian gagal | Catat cakupan pemeriksaan/partial; jangan menganggap semua media sudah lolos. |
| WhatsApp terputus | Pantau koneksi, gunakan sesi tersimpan atau pairing ulang lokal; job/outbox tetap di database. |
| Payload ditolak permanen | Operator meninjau sebab tanpa memblokir semua pengirim. |
| Receipt tidak pasti | Tandai unknown dan lakukan rekonsiliasi sebelum retry. |
| Kapasitas/budget habis | Tampilkan gangguan yang sesuai, pertahankan antrean yang tersimpan dan tinjau kapasitas; tidak menghapus counter untuk mengulang kuota. |

Rekonsiliasi pengiriman menggunakan receipt yang diperiksa atau retry yang disetujui setelah dipastikan pesan belum terkirim:

```powershell
.\.venv\Scripts\python.exe -m backend.cli reconcile-delivery UUID_OUTBOX --receipt ID_PESAN_WHATSAPP --reason "Receipt diperiksa"
.\.venv\Scripts\python.exe -m backend.cli reconcile-delivery UUID_OUTBOX --retry --reason "Dipastikan belum terkirim"
```

### 19.7 Backup, restore, dan penghapusan

Runbook menetapkan cakupan database, media, konfigurasi serta credential yang perlu dipulihkan secara konsisten, dengan pembatasan akses dan retensi backup. Jadwal, lokasi, metode perlindungan dan target pemulihan ditetapkan per deployment.

Setelah restore, operator menyelaraskan state job/outbox dengan riwayat pengiriman. Backup database tidak dianggap bukti pesan WhatsApp belum terkirim; status unknown tetap memerlukan rekonsiliasi.

Purge menghapus data terkait secara konsisten sesuai kebijakan retensi, tanpa menghapus sesi/configuration secara sembarang. Reset data simulasi dipisahkan dari data operasional. Keberadaan backup diperhitungkan dalam kebijakan retensi dan permintaan penghapusan.

### 19.8 Runbook dan pergantian operator

Runbook mencakup pemasangan, konfigurasi, startup/shutdown, pairing ulang, pemeriksaan credential aman, pemutakhiran/persetujuan wilayah dan FIRMS, review bukti/insiden, antrean gagal, pemulihan spool/job, unknown, budget, purge, backup/restore dan reset simulasi.

Insiden simulasi, koordinat sintetis dan injected failure diberi label agar tidak dibaca sebagai laporan/konfirmasi lapangan. Pengujian pengiriman memakai penerima yang diotorisasi. Adapter transport menjaga logika bisnis terpisah agar jalur WhatsApp dapat diganti mengikuti kebutuhan dan ketentuan platform.

## 20. Model data dan API

| Entitas | Data utama |
| --- | --- |
| Inbound event | ID/schema, provider, account, provider message ID, conversation/sender, waktu, teks, lokasi dan media refs. |
| Report | Pemilik, incident ID, revisi, urutan input, fakta/kutipan, kelengkapan, lokasi, media, consent dan keputusan. |
| Incident | ID, slug acak, titik kejadian, wilayah, kategori, revisi dan agregat evidensi. |
| Evidence result | Report/revision/media/frame, check type, outcome, alasan, source refs, waktu, hash serta versi model/prompt/rule. |
| Report-incident match | Kandidat, jarak/waktu, saran AI, alasan, keputusan operator dan audit koreksi. |
| Consent event | Pemilik, cakupan, keputusan, waktu, sumber dan versi pertanyaan. |
| Job | Jenis, revision/input, status, lease/token, percobaan dan jadwal eksekusi. |
| Outbox/delivery | Incident/revision/tujuan/jenis payload, admission, upaya, outcome dan provider message ID. |
| Verification event | Insiden, valid/invalid, GPS/accuracy/fix/received time, jarak, deskripsi/foto, solved, request ID dan sumber public_link. |
| Audit | Aktor/sumber, tindakan, subject, waktu, alasan dan hasil. |
| Sumber wilayah/FIRMS | Sumber, versi, hash, cakupan, waktu, sensor/atribusi dan persetujuan wilayah. |

Kontrak layanan mencakup:

- `POST /internal/whatsapp/events`: penerimaan transaksional dan receipt replay yang konsisten.
- `GET /api/reports`: daftar berpagination/filter dengan scope wilayah.
- `GET /api/reports/{id}`: detail sesuai izin field/peran.
- `POST /api/reports/{id}/deliveries/{delivery_id}/retry`: penjadwalan retry setelah pemeriksaan.
- `GET /laporan/{slug_id}`: overview publik teredaksi.
- `POST /api/laporan/{slug_id}/verifications`: submit GPS yang divalidasi server.

TRACK tetap melalui WhatsApp dengan pemeriksaan pemilik. API konfigurasi penerima/MPA menggunakan sumber backend yang sama; tidak ada konfigurasi kedua khusus bot yang saling bertentangan.

## 21. Parameter, evaluasi, dan model layanan

Parameter wilayah, jarak, waktu, budget dan kapasitas merupakan profil operasional; masing-masing memiliki arti terpisah. Radius GPS **2 km**, radius FIRMS **3 km**, dan kandidat insiden **500 m** tidak dipertukarkan. Parameter ini tidak dinyatakan sebagai batas ilmiah universal atau SOP resmi instansi.

Evaluasi sistem mencakup kelengkapan dan jumlah giliran percakapan, kualitas ekstraksi per field, recall ancaman eksplisit, fakta tanpa sumber, ketepatan routing, salah merge, biaya/token per report, latensi, dan keberhasilan transport per tujuan.

Penilaian memakai kasus pesan informal/typo, multipesan, hutan/lahan/permukiman, media ambigu, konflik, negasi ancaman, kegagalan provider, restart, revisi usang, consent dicabut sebelum kirim, replay dan receipt unknown. Kasus GPS mencakup batas jarak/accuracy/usia, penolakan izin, NaN, invalid+solved serta akses TRACK lintas pemilik.

Metrik akurasi AI membutuhkan ground truth independen. Voting publik, jumlah kandidat web atau beberapa sampel provider tidak menjadi persentase akurasi final. Data tuning prompt dipisahkan dari data evaluasi.

Model layanan B2G mencakup konfigurasi wilayah, penerima, dashboard, dukungan serta operasi, melalui langganan/kontrak per kota atau kabupaten. Biaya mencakup transport pesan, AI/pencarian gambar, hosting, penyimpanan dan nomor khusus. SIGAPI melengkapi kanal pelaporan serta sumber satelit yang sudah ada; keberadaan konfigurasi instansi tidak dianggap bukti kemitraan atau tindakan resmi.

## 22. Acuan dokumentasi

Definisi sistem ini menyatukan knowledge utama, rancangan teknis, perincian percakapan/validasi, operasi layanan, dashboard, serta keputusan pemrosesan/lokasi/metadata.

- [Knowledge utama](Knowledge_Doc_Terbaru_DeveloperDay_Karhutla_2026.md).
- [Arsitektur OpenClaw dan AI](docs/superpowers/specs/2026-10-21-openclaw-ai-design.md).
- [Aturan dan parameter validasi](docs/superpowers/specs/2026-10-22-validation-demo-design.md).
- [Perincian alur, form, retensi dan operasi](docs/superpowers/plans/2026-10-22-validation-demo-implementation.md).
- [Fallback pencarian web](docs/superpowers/specs/2026-10-23-web-evidence-fallback-design.md).
- [Konfigurasi runtime dan provider](docs/setup-task-1.md).
- [Penerimaan persisten](docs/setup-task-2.md).
- [Analisis, wilayah, operator dan distribusi](docs/setup-task-3.md).
- [Pemilihan model](docs/groq-model-selection.md).
- [Keputusan pemrosesan, lokasi dan metadata](docs/audit-knowledge-v3-2026-10-24.md).
- [Spesifikasi dashboard](<Spesifikasi Dashboard Admin Kota - Bot WhatsApp Pelaporan Karhutla.md>).
- [Konteks layanan dan bisnis](<Knowledge Doc Bot WhatsApp Pelaporan Karhutla (.id DeveloperDay 2026).md>).
