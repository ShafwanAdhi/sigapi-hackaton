# Suplemen Knowledge Sistem SIGAPI

**Ekstraksi dokumentasi repo di luar Knowledge v3 — 24 Oktober 2026, Asia/Jakarta**

## 1. Cakupan dan cara membaca

Dokumen ini menghimpun informasi sistem yang **belum ada, lebih terperinci, atau sudah diperbarui** dibandingkan `Knowledge_Doc_Terbaru_DeveloperDay_Karhutla_2026.md` tanggal 22 Oktober 2026. Perbandingan dilakukan secara makna, bukan sekadar mencari kalimat berbeda. Informasi yang sama digabung; aturan lama yang bertentangan dipisahkan sebagai arsip.

Salinan knowledge di repo identik dengan file pembanding dari pengguna. SHA-256: `e112ee09abd1d3a89a2f1aa4f69e2360d19b51ac304037a7fa2f53dd4534b0e7`.

Sumber meliputi **15 dokumen Markdown: satu knowledge pembanding dan 14 dokumen tambahan**, termasuk ledger progres tersembunyi. Daftar lengkap ada di bagian 22. Dependensi, direktori runtime, media, log mentah, dan konfigurasi privat bukan sumber tambahan yang diekspor. Nomor pribadi, credential, token, dan isi laporan warga tidak disertakan.

Label yang digunakan:

| Label | Arti |
| --- | --- |
| **Keputusan demo** | Pilihan yang sudah dikonfirmasi untuk prototipe ini; bukan otomatis SOP instansi atau parameter produksi. |
| **Tersedia menurut dokumentasi** | Dokumen implementasi menyatakan fitur sudah dibuat. Ekstraksi ini tidak menjalankan ulang aplikasinya. |
| **Bukti uji tercatat** | Ada hasil uji yang dicatat sumber, dengan lingkup dan keterbatasannya. |
| **Rencana/spesifikasi** | Perilaku yang dituju; belum boleh dianggap fitur yang tersedia. |
| **Arsip** | Konteks atau aturan lama; penggunaannya harus mengikuti keputusan yang lebih baru. |

Urutan pembacaan ketika sumber berbeda: keputusan pengguna yang dicatat audit 24 Oktober → amendemen dan panduan implementasi terbaru → rancangan/rencana sebelumnya → arsip v2. Informasi lomba, harga, kuota, dan kemampuan API di sini merupakan catatan bertanggal dari repo, bukan hasil riset web baru.

## 2. Keputusan terbaru yang memperbarui atau memperinci Knowledge v3

| Area | Ketentuan tambahan untuk demo | Dampak terhadap knowledge pembanding |
| --- | --- | --- |
| Wilayah | **Kota Malang**, kode wilayah `35.73`. | Fokus satu wilayah diperjelas menjadi wilayah tertentu. |
| Lokasi teks | Hanya untuk klarifikasi. Pelapor tetap wajib mengirim **pin/koordinat kejadian dan mengonfirmasinya**. | Alamat teks tidak menggantikan titik kejadian; alur demo tidak melakukan geocoding alamat. |
| EXIF | Opsional; jika ada, hanya bukti tambahan. | EXIF kosong dicatat unavailable/unknown dan sendirian tidak menahan laporan. Unknown tidak berarti konsisten atau autentik. |
| Pemrosesan laporan/AI | Tidak ditambahkan pemberitahuan atau gerbang persetujuan khusus untuk demo, sesuai jawaban pengguna 24 Oktober. | Memperbarui langkah persetujuan pemrosesan pada §4.1; pilihan pembuat demo ini tidak dicatat sebagai consent implisit warga. |
| Berbagi nomor | Tetap membutuhkan izin eksplisit, terpisah, opsional; **default tidak diberikan**. | Keputusan pemrosesan di atas tidak mengaktifkan izin berbagi nomor. |
| Konflik bukti | Minta klarifikasi; konflik terbuka menahan komunitas. Pernyataan “foto asli” saja tidak menghapus kecocokan web. | Kebijakan yang masih berupa rekomendasi di knowledge telah dipilih untuk demo. |
| FIRMS gagal/usang | Tahan komunitas; bukan hasil “tidak ada hotspot”. | Ketersediaan pemeriksaan dipisahkan dari kecocokan hotspot. |
| Ancaman tinggi | Eskalasi otoritas uji berlabel **BELUM TERVERIFIKASI**, setelah minimum lengkap dan titik terkonfirmasi dalam wilayah. | Jalur ini tidak harus menunggu seluruh pemeriksaan web/FIRMS selesai. |
| Hold | Tidak memiliki timer penerusan otomatis. | Klarifikasi/operator atau informasi baru diperlukan untuk mengubah keputusan. |
| Kepercayaan | Keputusan `held/eligible`, kode alasan, dan referensi bukti; tanpa persentase probabilitas kebenaran. | Gagasan skor diperinci menjadi keputusan yang dapat dijelaskan. |
| Tujuan uji | Dua nomor terpisah: komunitas dan otoritas. Keduanya berbeda dari bot dan seluruh pelapor uji. | Pengujian tidak menggunakan instansi nyata secara otomatis. |

Ketiga klarifikasi bisnis audit—pemrosesan, lokasi teks, dan EXIF—sudah terjawab. Salinan knowledge sumber sengaja dipertahankan; perubahan percakapan dicatat melalui amendemen.

Sumber: [D11], terutama amendemen dan status klarifikasi; [D09]; [D03]; [D04].

## 3. Arsitektur dan pembagian tanggung jawab

### 3.1 Komponen dan proses

**Keputusan/desain yang digunakan:** OpenClaw mengurus transport WhatsApp; FastAPI merupakan pengendali alur dan aturan. Model membantu ekstraksi, observasi, dan penjelasan. Backend menentukan kelengkapan, hak akses, wilayah, consent, penerima, keputusan, dan status pengiriman.

| Komponen | Tanggung jawab |
| --- | --- |
| Plugin OpenClaw | Mengambil alih pesan sebelum agent bawaan, menormalisasi input, menyalin media ke spool privat, meneruskan input, dan mengirim outbox. |
| API FastAPI | Memvalidasi input serta menyimpan event dan pekerjaan secara transaksional. |
| `worker` | Mengolah intake, membuka/decode media, memperbarui draft dan kelengkapan. |
| `analysis-worker` | Ekstraksi bahasa alami, pemeriksaan provider, bukti, FIRMS, kandidat insiden, dan keputusan. Provider lambat tidak menghambat penerimaan pesan. |
| PostgreSQL | Sumber state laporan, job persisten, revisi, bukti, consent, audit, dan outbox. |
| Modul geospasial | Polygon wilayah, jarak, cakupan/waktu FIRMS, serta kandidat insiden. |
| Aplikasi publik — rencana Task 4 | Overview teredaksi dan form GPS; aplikasi terpisah dari API internal, memakai modul/database yang sama. |
| Dashboard/operator UI — rancangan | Daftar/detail laporan, bukti, pengaturan penerima, dan pemantauan delivery. CLI operator sudah tersedia lebih dahulu. |

Rancangan awal menyebut satu worker umum; versi Task 3 memisahkan proses intake dan analisis. Tidak ada model percakapan kedua di OpenClaw yang membalas warga secara paralel.

Backend tetap modular dalam satu paket. Tidak diperlukan microservice per fungsi, Redis/Celery, framework multi-agent, RAG, pelatihan model, atau vector database untuk lingkup demo yang didokumentasikan. Job/delivery tidak boleh hanya bergantung pada memori atau `BackgroundTasks`.

### 3.2 Stack dan versi yang dicatat

| Bagian | Catatan repo |
| --- | --- |
| Backend | Python 3.11, FastAPI/Pydantic, psycopg 3, HTTPX, Pillow. |
| Database | PostgreSQL lokal; rencana menyebut PostgreSQL 16. PostGIS tidak diwajibkan untuk demo. |
| Geospasial | GeoJSON/Shapely untuk polygon; Haversine cukup untuk radius form. |
| Runtime WhatsApp | Node lokal **26.12.1**, OpenClaw **2026.10.6**, plugin WhatsApp **2026.10.6**. |
| Plugin penghubung | Implementasi JavaScript memakai SDK hooks. Penyebutan TypeScript pada rencana adalah rancangan awal; pemeriksaan implementasi memakai tes Node/sintaks JavaScript. |
| Video | FFmpeg dan FFprobe **9.0.2**, build resmi Gyan, checksum SHA-256 arsip diverifikasi. |
| Vision opsional | Implementasi memakai REST resmi `images:annotate` dan `google-auth`; SDK Vision tidak menjadi syarat jalur SerpApi. |
| Publikasi web — rencana | HTML template, JavaScript Geolocation, multipart upload, HTTPS Cloudflare Tunnel; tidak memerlukan SPA. |

Dependensi dipin setelah smoke test. Node/FFmpeg dipasang lokal; Node global dan PATH sistem tidak perlu diubah. CLI menambahkan FFmpeg lokal ke PATH proses. Waktu disimpan UTC dan ditampilkan Asia/Jakarta.

Sumber: [D01]; [D02] §3–5, §9; [D04]; [D07]; [D08]; [D09]; [D14].

## 4. Kontrak data dan API lintas komponen

### 4.1 Envelope dan identitas

Rancangan envelope internal memuat:

```text
schema_version, event_id, provider, account_id,
provider_message_id, conversation_id, sender_id,
received_at, text, location, media[],
reply_to_message_id (opsional)
```

`sender_id` berasal dari identitas transport yang dinormalisasi adapter. Nomor telepon tidak ditebak dari teks warga atau bentuk JID. Nomor yang berhasil diselesaikan transport boleh disimpan terpisah dan nullable; penggabungan alias identitas harus berdasarkan metadata tepercaya.

Rancangan umum menyebut kunci unik `(provider, account_id, provider_message_id)`. Kontrak demo untuk provider WhatsApp menggunakan `(account_id, provider_message_id)`. Replay identitas yang sama menghasilkan receipt penerimaan yang sama tanpa report/job tambahan.

Lokasi memuat latitude/longitude, sumber dan accuracy bila tersedia. Pin adalah **titik yang dilaporkan**, bukan bukti posisi perangkat pelapor. Pin pengganti menaikkan versi dan membatalkan konfirmasi lama.

### 4.2 Kontrak logis tambahan

| Kontrak | Field/perilaku tambahan terhadap skema ilustratif knowledge |
| --- | --- |
| `Report` | Revision, urutan input, fakta beserta kutipan sumber, kelengkapan, consent, dan hubungan ke draft/pemilik. |
| `EvidenceResult` | Report/revision, check type, outcome, reasons, source refs, checked time, model/prompt/rule version. |
| `RoutingDecision` | Incident/revision, `publish_allowed`, `authority_escalation`, alasan, referensi bukti; hasil aturan backend. |
| `Delivery` | Incident/revision, tujuan, jenis payload, attempt, outcome, provider message ID, waktu. |
| Job | Pekerjaan persisten, status, lease/token, revision/input yang dianalisis, dan batas retry. |
| Media | ID server, SHA/fingerprint, MIME hasil validasi, ukuran, lokasi privat, status staging/analisis. |
| Consent kontak | Keputusan eksplisit, cakupan, waktu, versi pertanyaan, dan pesan sumber. |
| Tujuan/rencana distribusi | Tujuan aktif menurut wilayah/jenis dan snapshot penerima/payload yang akan diperiksa ulang sebelum kirim. |

### 4.3 Endpoint: tersedia dan usulan jangan dicampur

| Endpoint | Status dokumentasi dan semantik |
| --- | --- |
| `POST /internal/whatsapp/events` | Intake tersedia; HTTP **202 setelah event dan job commit**. Duplikat mengembalikan penerimaan yang sama. |
| `GET /api/reports` | Usulan API dashboard; pagination/filter dan scope wilayah diterapkan server. |
| `GET /api/reports/{id}` | Usulan detail dashboard dengan pembatasan field sensitif. |
| `POST /api/reports/{id}/deliveries/{delivery_id}/retry` | Usulan API retry admin; menjadwalkan delivery sama setelah pemeriksaan. Saat ini ada operasi CLI. |
| `GET /laporan/{slug_id}` | Rencana Task 4; slug tersedia, route belum ada pada audit. |
| `POST /api/laporan/{slug_id}/verifications` | Perincian rencana demo Task 4; endpoint berbasis slug, menggantikan contoh endpoint berbasis ID incident sebagai pilihan implementasi demo. |

API penerima/MPA mengikuti backend tim, bukan membuat sistem konfigurasi kedua khusus bot. TRACK masuk lewat WhatsApp dan fungsi backend yang memeriksa pemilik; tidak membuka endpoint publik berisi detail pelapor.

Sumber: [D02] §4, §6–7, §13; [D04] kontrak lintas task dan Task 2–4; [D08]; [D11].

## 5. Penerimaan persisten, urutan, dan pemulihan

**Tersedia menurut dokumentasi Task 2–3:**

1. Plugin mengabaikan pesan bot sendiri dan event yang tidak relevan, lalu menormalisasi input yang sudah selesai staging.
2. Envelope dan salinan media ditulis atomik ke **spool privat** sebelum takeover dianggap selesai.
3. Plugin mengirim input ke API. Receipt 202 baru diberikan setelah event dan job tersimpan dalam satu transaksi.
4. Spool lokal dibersihkan setelah penerimaan database dikonfirmasi. Timeout penerimaan boleh mengulang ID event yang sama.
5. Worker mengambil job persisten; balasan warga juga memakai outbox.

Jika API mati, bot menyatakan input berada dalam antrean lokal, bukan mengklaim laporan sudah diterima server. Spool diputar ulang menurut urutan penerimaan. Mekanisme ini hanya melindungi pesan yang **sudah diterima plugin**, bukan pesan yang belum sampai ke gateway.

Mutasi diserialisasi per akun/pengirim. Lease token mencegah worker lama menulis setelah pekerjaan diambil alih. Analisis juga diikat ke revision dan urutan input; hasil lama tidak boleh menimpa koreksi atau memicu pengiriman snapshot lama.

Input yang gagal ditulis tidak diakui sebagai laporan tersimpan. Payload yang ditolak permanen memerlukan pemeriksaan operator, tetapi kegagalan satu pengirim tidak memblokir pengirim lain.

| Batas intake/spool demo | Nilai |
| --- | --- |
| Teks input | Maksimal **4.000 karakter**. |
| Media per pesan | Maksimal **10 media**. |
| Spool pending | Maksimal **500 pesan / 256 MB**. |
| Foto | Maksimal **10 MB**. |
| Video | Maksimal **20 MB / 30 detik**. |

Media memakai ID buatan server; ekstensi/header pengirim saja tidak cukup. Jenis dan kelayakan diperiksa melalui decode. Berkas yang melebihi batas diminta ulang, bukan diam-diam dilewati. Penyimpanan media satu host memakai volume privat; object storage merupakan kebutuhan jika kelak lintas host.

Sumber: [D02] §3, §5–6, §14; [D04] Task 1–2; [D08] jaminan operasional; [D09]; [D14].

## 6. Percakapan dan ekstraksi bahasa alami

### 6.1 Kontrol percakapan

| Input/perilaku | Makna yang didokumentasikan |
| --- | --- |
| `REPORT` | Memulai laporan. Jika ada draft aktif, bot menawarkan pilihan eksplisit. |
| `LANJUT` / `BARU` | Memilih draft lama atau laporan baru; dua kejadian tidak digabung diam-diam. |
| Foto/video/caption/pesan bertahap | Digabung ke satu draft aktif milik pengirim yang benar. Task 3 menerima bahasa alami. |
| `KETERANGAN: ...` | Jalur deterministik Task 2, minimal 10 karakter setelah prefix. Prefix tidak lagi wajib dalam percakapan Task 3. |
| `KONFIRMASI LOKASI n` | Mengonfirmasi versi pin yang diminta bot; bukan dugaan AI. |
| `IZIN KONTAK YA` | Memberi izin berbagi nomor ke otoritas. |
| `IZIN KONTAK TIDAK` | Menolak atau mencabut izin tersebut. |
| `STATUS` | Membaca kondisi tersimpan, termasuk pemeriksaan/delivery pada Task 3. |
| `TRACK` | Fitur penuh direncanakan Task 4; pada audit masih memberi balasan belum tersedia. |

Rancangan umum juga mengusulkan REPORT dapat dimulai dari pesan yang jelas melaporkan kejadian, sedangkan sapaan hanya mendapat petunjuk. Ini tidak boleh disamakan dengan bukti bahwa seluruh pemicu otomatis tersebut telah diuji pada runtime terbaru.

Pin native WhatsApp telah diterima. Panduan Task 2 secara eksplisit menyatakan **tautan teks Google Maps belum diparsing**; alamat atau tautan teks tidak boleh diasumsikan memenuhi koordinat terstruktur.

Maksimal empat pertanyaan klarifikasi tanpa informasi baru/per revisi sesuai alur demo. Sesudah batas, draft/hold tetap disimpan; fakta baru dapat melanjutkan. Informasi opsional tidak menahan kelengkapan minimum. Perubahan material setelah penerusan menjadi revisi/update yang ditandai jelas.

### 6.2 Fakta bersumber dan waktu

Contoh kebutuhan: “terjadi kebakaran di Malang” lalu “mulai jam delapan malam” menjadi satu konteks laporan. Waktu atau tanggal ambigu ditanyakan, bukan ditentukan dari dugaan.

Ekstraksi terstruktur memisahkan kategori kejadian, keterangan, klaim waktu, dan klaim ancaman. Setiap fakta menunjuk pesan/media serta kutipan yang benar-benar ada. Informasi tidak disebut tetap null/unknown. Klaim bersumber tetap **klaim**, bukan bukti bahwa isinya benar.

Pisahkan waktu pesan, waktu kejadian yang diklaim, waktu media jika tersedia, waktu observasi satelit, dan waktu pengambilan sumber. Waktu pesan tidak membuktikan waktu kejadian.

Keterangan tambahan yang direncanakan dapat mencakup api/asap masih terlihat, luas perkiraan, kedekatan permukiman/fasilitas, gambut/kebun/semak, dan orang terancam/evakuasi. Bot tidak mengarang luas, korban, jenis lahan, tanggal, atau lokasi foto.

### 6.3 Kegagalan AI dan ancaman

Jika Groq gagal, data tetap diterima dan percakapan berbasis aturan tetap berjalan. Aturan teks konservatif mengenali ancaman eksplisit; negasi atau kalimat ambigu tidak boleh otomatis dianggap darurat. Kategori yang tidak diketahui diminta klarifikasi.

Definisi demo ancaman tinggi: orang terancam/terjebak, kebutuhan evakuasi, atau api mengancam rumah/fasilitas. Setiap klaim ancaman membawa sumber; AI tidak boleh menciptakan ancaman. Tidak ada informasi risiko bukan berarti risiko rendah.

Ancaman tidak melewati gerbang minimum laporan. Panduan keselamatan dapat diberikan lebih awal dalam rancangan, tetapi audit menyatakan balasan keselamatan **belum tersedia**.

Sumber: [D02] §7–9; [D04] keputusan dan Task 2–3; [D08]; [D09]; [D11]; [D14].

## 7. Pemeriksaan media dan kontrak AI

AI dipakai untuk tiga pekerjaan yang dibedakan: ekstraksi klaim warga, observasi visual, dan ringkasan. Schema memuat enum terbatas, nullable field, source IDs/kutipan, serta penanda konflik. JSON schema-invalid tidak boleh memperbarui laporan sebagai hasil sukses.

Observasi visual terbatas pada api/asap terlihat, keterbacaan/kualitas gambar, dan isi yang tampak. Model tidak menentukan keaslian, waktu pengambilan, lokasi pasti, nomor penerima, consent, nomor darurat, atau hasil pengiriman.

**Tersedia menurut dokumentasi Task 3:** setiap media laporan diperiksa; video memakai maksimal tiga frame awal/tengah/akhir. Pemeriksaan ini tidak memahami seluruh durasi video. Hasil sebagian/gagal tidak boleh ditampilkan sebagai pemeriksaan lengkap. Voice note belum menjadi fitur demo yang dijanjikan.

Bukti disimpan bersama sumber, waktu, model/prompt/rule/check version, hash, referensi sumber, serta outcome. Cache dikaitkan dengan hash dan versi analisis; perubahan media/revisi tidak menghapus bukti sebelumnya.

Fingerprint laporan dipisahkan dari koleksi `operator_smoke` Task 1. Media tidak dibandingkan sebagai duplikat dirinya sendiri. SHA-256 identik menandai berkas sama; dHash hanya kandidat kemiripan. Ketahanan terhadap crop/kompresi dan deteksi semua gambar AI tidak diklaim.

Metadata yang tersedia dicatat, antara lain tanggal EXIF atau keberadaan GPS. `NO_EXIF` berarti tidak tersedia. **Kekurangan audit:** belum ada hasil pemeriksaan konsistensi lintas isi/caption/lokasi/waktu tersendiri yang dipasok ke mesin keputusan. Foto hutan dan pin dalam kota saja tidak membuktikan konflik lokasi.

Sumber: [D02] §9–10; [D04] Task 1 dan 3; [D05]; [D09]; [D11].

## 8. Pencarian web dan fallback provider

### 8.1 Jalur terpilih

Keputusan 23 Oktober mengganti Vision wajib menjadi:

1. Pencocokan lokal SHA-256/dHash sebagai bukti tambahan.
2. **SerpApi Google Lens sebagai pencarian web utama.**
3. **Google Cloud Vision hanya opt-in**, default `ENABLE_GOOGLE_VISION=false`, ketika SerpApi unavailable.
4. Jika semua jalur web gagal: `unavailable`, `manual_review=pending`, komunitas ditahan. Operator dapat meninjau lewat Lens/TinEye; tidak ada scraping otomatis TinEye.

Fallback hanya saat layanan gagal, tidak dikonfigurasi, atau kuota habis. Temuan konflik menghentikan fallback; sistem tidak mencoba provider lain demi mengganti hasil yang tidak menguntungkan. Bukti dan kegagalan sebelumnya tetap disimpan.

### 8.2 Detail SerpApi

- Media didecode menjadi **JPEG turunan tanpa EXIF**, maksimal **450.000 byte**, sisi maksimal **1280 px**.
- Turunan diunggah melalui **Image API** untuk mendapat `image_id`; aplikasi tidak membuat URL hosting publik bagi media asli.
- SerpApi tetap menerima data gambar sebagai pihak ketiga; pengujian menggunakan media demo berizin.
- Cari `exact_matches`; jika kosong, baru `visual_matches`.
- Exact candidate memerlukan klarifikasi. Kemiripan visual hanya bukti lemah; full/partial match juga bukan vonis laporan palsu.
- Hasil memakai whitelist link/title/source, waktu, versi, dan hash turunan. Respons vendor mentah dan secret tidak diekspor ke hasil/log.
- URL referensi hanya HTTP(S) tanpa credential dan **tidak di-fetch backend**.
- Referensi hasil disimpan maksimal 100 dalam uji yang dicatat. Jumlah kandidat ini bukan skor kepercayaan.
- Bentuk respons no-match vendor yang tidak memenuhi struktur yang diharapkan pernah ditangani konservatif sebagai unavailable, bukan dipaksakan sukses.

Pencocokan lokal tidak menyelesaikan pemeriksaan internet. `manual_review=pending` juga tidak berarti review sudah dilakukan. Pada Task 1 belum ada penyimpanan hasil review manusia; Task 3 menambahkan review bukti persisten melalui CLI.

Sumber: [D05]; [D06]; [D07] §3 dan bukti koneksi; [D09] tinjauan operator; [D14].

## 9. Model, kuota, biaya, cache, dan retry

### 9.1 Groq Free Plan

**Pilihan model yang dicatat 23 Oktober:** `qwen/qwen3.8-27b`, diatur melalui `GROQ_VISION_MODEL`, bukan hardcode. `GROQ_TEXT_MODEL` opsional dan default mengikuti model vision. Qwen masih berstatus Preview menurut catatan tersebut. Alternatif `meta-models/muse-spark-open` dicatat limited preview dan bukan pilihan minimum demo.

| Aspek | Catatan bertanggal dari repo |
| --- | --- |
| Kuota publik Free Plan | 30 request/menit; 1.000 request/hari; 8.000 token/menit; 200.000 token/hari. Console/header akun tetap menjadi acuan batas sebenarnya. |
| Token gambar | 2.048 token input/gambar di luar prompt/output; tiga frame berarti tiga analisis. Batas token bisa tercapai sebelum batas request. |
| Biaya uji | Uji tercatat berjalan pada Free Plan tanpa upgrade. |
| Harga berbayar yang dicatat | US$0,80/juta token input dan US$4/juta token output; bukan biaya yang dinyatakan terpotong dalam uji gratis. |
| Konkurensi analisis | Satu panggilan Groq aktif. |
| Pacing | Jarak mulai minimal **35 detik**; tiga frame membutuhkan sekitar 70 detik jeda di luar durasi request. |
| Batas retry | Maksimal **tiga percobaan HTTP per operasi**, tersimpan melintasi restart worker. |

Percobaan awal video tanpa pacing mendapat 429 pada frame ketiga. Retry pendek 2/5 detik sendiri tidak menjamin pulih dari limit token per menit. Proses/aplikasi lain dengan akun sama tetap bisa menghabiskan kuota.

### 9.2 Budget pencarian web

| Layanan | Kuota vendor yang dicatat | Batas aplikasi demo |
| --- | --- | --- |
| SerpApi | Free yang ditinjau: 250 pencarian/bulan, 50/jam; perlu melihat kuota akun saat digunakan. | **50 operasi HTTP total**, termasuk upload dan retry; atomik/persisten di `.runtime/serpapi-budget.sqlite3`. Satu gambar baru umumnya 2–3 operasi. |
| Vision opsional | Harga/kuota Google mengikuti project. | **50 percobaan**, termasuk retry, terpisah di `.runtime/vision-budget.sqlite3`. Video dapat memakai tiga request baru. |

Hitungan aplikasi tidak sama dengan kredit vendor dan tidak membatasi aplikasi lain pada project Google. Database budget tidak dihapus untuk mengulang kuota. Hasil sukses di-cache per hash asli dan versi provider; kegagalan tidak di-cache.

Rencana retry provider: maksimal tiga percobaan total, hanya timeout/429/5xx; backoff 2 lalu 5 detik, timeout rencana 30 detik/request. Kegagalan autentikasi/billing tidak dianggap hasil negatif. Pacing Groq Task 3 tetap berlaku di atas retry tersebut.

### 9.3 Vision jika sengaja diaktifkan

Vision menggunakan REST resmi `images:annotate`, fitur `WEB_DETECTION`, dan `google-auth`. Memerlukan project, billing aktif, API aktif, serta ADC lokal. Tidak perlu membuat service-account key JSON untuk login lokal. Izin penggunaan API/quota project seperti `serviceusage.services.use` diperlukan; role Owner untuk aplikasi bukan kebutuhan yang ditetapkan.

Budget alert Google adalah pengingat, bukan hard spending cap. Aplikasi tidak mengaktifkan API/billing otomatis. Respons `BILLING_DISABLED` tercatat pada uji lama; jalur SerpApi membuat billing Google tidak wajib untuk demo sekarang.

Arsip v2 mencatat 1.000 unit Vision awal gratis/bulan, sekitar US$3,50/1.000 gambar berikutnya, contoh 10.000 gambar sekitar US$31,50. Angka ini **arsip harga**, bukan estimasi biaya terkini atau alasan mengaktifkan billing.

Sumber: [D10]; [D07] §2–3 dan batas video; [D05]; [D04] Task 3; [D09]; [D13] §7.2.

## 10. FIRMS dan penentuan wilayah

### 10.1 Snapshot FIRMS

**Pilihan demo:** data tersimpan bersumber nyata, bukan fixture yang dinyatakan feed live. Setup Task 3 memakai CSV NASA **VIIRS 48 jam**, dengan sumber, waktu modifikasi sumber, acquisition time, fetch time, sensor, hash, dan cakupan.

| Pemeriksaan | Parameter/perilaku demo |
| --- | --- |
| Radius kandidat hotspot | **3 km** dari titik kejadian. |
| Selisih pengamatan | Maksimal **24 jam** terhadap waktu kejadian. |
| Usia snapshot/sumber | Maksimal **24 jam**, dengan pemeriksaan usia sumber dan pengambilan. |
| Cakupan awal | Harus mencakup 24 jam sebelum kejadian. |
| Cakupan akhir | Berakhir pada **waktu sumber**, bukan waktu download atau pengamatan masa depan. |
| Kejadian lebih baru dari cakupan | `unavailable` dan komunitas ditahan; bukan `no_match`. |
| Sumber usang/gagal/area tidak tercakup | `unavailable`, bukan “tidak ada hotspot”. |

Hasil `matched/no_match/unavailable/not_checked` dibedakan. `no_match` hanya sah setelah area/waktu memadai. FIRMS tidak wajib menemukan hotspot agar komunitas layak menerima laporan, tetapi pemeriksaannya harus tersedia sesuai kebijakan demo. Radius 3 km ini berbeda dari radius form GPS dan kandidat insiden.

Snapshot harus diunduh ulang untuk memperbarui data; timestamp tidak diubah manual untuk membuat data lama tampak baru.

### 10.2 Polygon wilayah

Routing menggunakan **batas GeoJSON Kota Malang**, bukan bounding box atau tebakan AI/alamat. Kandidat yang diunduh berasal dari **OpenStreetMap relation `9674151`**, kode wilayah `35.73`, dengan sumber/versi/atribusi. Ini data komunitas, bukan sertifikasi batas pemerintah.

Operator perlu memeriksa bentuk batas dan titik demo. Persetujuan diikat ke SHA-256 file; mengunduh ulang batas membatalkan persetujuan sebelumnya. Titik di luar, ambigu, atau tepat pada batas polygon ditahan untuk tinjauan dan tidak ditebak penerimanya. Reverse geocoding pada rancangan umum hanya membantu label alamat, bukan menetapkan kewenangan.

Sumber: [D02] §10; [D04] Task 3; [D09] data/aktivasi; [D11]; [D14].

## 11. Mesin keputusan dan pengelompokan insiden

### 11.1 Keputusan backend

Kelengkapan, kelayakan distribusi, dan keberhasilan kirim adalah tiga hasil berbeda. Backend menyimpan alasan dan referensi bukti, bukan menjadikan jawaban bebas AI sebagai keputusan.

| Keadaan | Perilaku demo yang didokumentasikan |
| --- | --- |
| Minimum belum lengkap | Minta data yang kurang; tidak mengklaim telah didistribusikan. |
| Ada kandidat penggunaan ulang web | Klarifikasi/review; komunitas ditahan selama konflik terbuka. |
| Media bertentangan atau pemeriksaan wajib sebagian/gagal | Komunitas ditahan. |
| FIRMS unavailable/usang | Komunitas ditahan. |
| Ancaman tinggi eksplisit, minimum lengkap, pin terkonfirmasi dalam pilot | Eskalasi otoritas uji **BELUM TERVERIFIKASI**, termasuk alasan ketidakpastian; tidak menunggu seluruh pemeriksaan lambat. |
| Pemeriksaan wajib tersedia, media api/asap jelas, waktu dapat diperiksa, konflik tidak terbuka, grouping selesai | Layak distribusi awal menurut kategori/tujuan terkonfigurasi. |
| Titik di luar/ambigu wilayah | Simpan; jangan menebak penerima. |

Reputasi nomor dalam rancangan MVP adalah `insufficient_history`; nomor baru tidak dihukum. Banyak nomor/laporan serupa menunjukkan korelasi, bukan bukti bahwa pelapor independen.

### 11.2 Kandidat insiden

- Cari kandidat dalam **500 meter dan enam jam**.
- AI memberi saran/alasan kemiripan; **operator mengonfirmasi penggabungan** melalui CLI.
- Jika tidak ada kandidat, buat insiden baru. Kandidat yang belum diputuskan menahan distribusi komunitas agar tidak mengirim laporan awal ganda.
- Report sumber tetap terpisah; bukti awal tidak dihapus ketika digabung atau dipisah.
- Koreksi pengelompokan diaudit dan membatalkan antrean lama yang belum dikirim.
- Insiden memiliki slug acak **128-bit**, satu link kanonik untuk report yang bergabung. Slug sudah tersedia, tetapi link belum dibagikan sebelum route Task 4 berfungsi.
- Jenis kejadian memengaruhi tujuan: hutan/lahan dapat menuju komunitas dan otoritas; kebakaran bangunan/permukiman ke otoritas yang dikonfigurasi.

Angka 500 m/enam jam adalah parameter demo, bukan bukti dua kebakaran yang dekat pasti sama.

Sumber: [D04] keputusan dan Task 3; [D09]; [D11]; [D14].

## 12. Distribusi, consent saat kirim, dan hasil tidak pasti

### 12.1 Penerima dan payload

Izin pengirim masuk berbeda dari penerima keluar. `allowSenders`/`channels.whatsapp.allowFrom` mengatur inbound; `outboundRecipients` mengatur outbound plugin. Dua nomor tujuan uji ditambahkan hanya ke daftar keluar yang sesuai.

Distribusi memakai kartu teks terstruktur, berlabel laporan warga/pemeriksaan awal. Teks mentah, identitas warga, dan media asli tidak diteruskan. Nomor hanya dimasukkan ke kartu otoritas jika consent masih aktif **ketika pengiriman dimulai**.

Sebelum kirim, backend memeriksa lagi revision, input terbaru, keputusan, wilayah, tujuan, konfigurasi aktif, dan consent. Payload admission yang baru dipakai; antrean lama tidak berhak mengirim snapshot yang sudah dikoreksi.

### 12.2 Idempotensi dan status

Delivery dibedakan menurut insiden, revision, tujuan, dan jenis pesan. Report baru dalam insiden yang sama tidak boleh menggandakan notifikasi awal; perubahan material dikirim sebagai pembaruan. Tujuan yang sudah sukses tidak diulang saat memperbaiki tujuan gagal.

Job/delivery dapat mempunyai status seperti `pending/sending/sent/failed/unknown/unroutable`; status teknis ini tidak dipaksa menjadi satu enum sederhana. Jika baru sebagian tujuan wajib berhasil, agregat belum boleh mengklaim seluruh penyaluran berhasil.

HTTP 200 saja bukan bukti kirim. Keberhasilan membutuhkan hasil provider/receipt WhatsApp yang valid dan tersimpan. Receipt kirim bukan bukti pesan sudah ditindaklanjuti petugas.

Jika timeout terjadi **setelah kirim dimulai**, hasil menjadi `unknown`: tidak diasumsikan gagal/sukses, dan **tidak dicoba ulang otomatis**. Operator memeriksa riwayat WhatsApp/log, lalu mencatat receipt atau mengizinkan retry jika dipastikan belum terkirim. Ini berlaku pula pada balasan outbox; pesan berikutnya tetap dapat diproses.

Unique constraint dan transaksi memberikan idempotensi internal, bukan jaminan exactly-once di WhatsApp. Batas demo **lima distribusi per sepuluh menit per tujuan**; selebihnya tetap mengantre.

Sumber: [D02] §11–12, §16; [D04] Task 3; [D08]; [D09]; [D14].

## 13. Keamanan dan privasi teknis tambahan

**Tersedia atau menjadi kontrak implementasi yang dicatat:**

- Endpoint internal ber-token dan hanya loopback; backend saat ini `127.0.0.1:8011`, tanpa dokumentasi API publik/access log. Gateway/token operator tidak dibuka ke warga.
- Konfigurasi awal membatasi DM tim serta menonaktifkan grup dan self-chat. Plugin hanya mengambil input yang lolos kebijakan kanal.
- Konten pesan/caption/tulisan gambar diperlakukan sebagai data. Konten warga tidak memperoleh tool shell, filesystem umum, browser, atau kemampuan mengubah konfigurasi.
- Validasi schema, koordinat finite/range, panjang teks, ukuran, decode/MIME, serta path diterapkan di batas layanan. Root staging terkontrol, ID media server, penolakan traversal dan URL media arbitrer mencegah akses berkas/SSRF.
- Konten ke model dipilih/redaksi tanpa identitas transport yang tidak diperlukan. Respons vendor mentah dan secret tidak dicetak ke hasil/log.
- Runtime, credential sesi, media, database dump, spool, transcript, serta log sensitif diabaikan Git. Template konfigurasi tidak berisi secret nyata.
- Role aplikasi PostgreSQL bukan superuser; database uji terpisah dari database demo.
- Perubahan consent, tujuan, review, retry, dan hasil kirim mempunyai audit dasar. Halaman audit lanjutan boleh belakangan; pencatatan tidak ditunda.

**Rancangan lanjutan:** API dashboard menerapkan scope wilayah/peran di server, bukan hanya menyembunyikan filter frontend. Akses media detail memerlukan autentikasi/tautan singkat terbatas. TLS diperlukan bila internal lintas host. Aplikasi publik terpisah; Cloudflare Tunnel hanya membuka aplikasi publik HTTPS.

Penghapusan atas permintaan direncanakan memeriksa kepemilikan dan audit. Salinan yang telah dikirim ke pihak eksternal tidak dapat dijamin ikut terhapus.

Sumber: [D02] §5, §11, §14; [D04]; [D05]; [D07]; [D08]; [D12] privasi; [D14].

## 14. Setup lokal dan perintah operasional

Bagian ini mengekstrak cara kerja yang didokumentasikan; perintah tidak dijalankan dalam proses pembuatan suplemen ini. Placeholder bukan credential atau nomor sebenarnya.

### 14.1 Struktur privat dan prasyarat

- Workspace demo: `D:\sigapi`. Jalankan Python melalui `.\.venv\Scripts\python.exe` dari direktori ini.
- `.env` menyimpan key provider, token internal/gateway, dan DSN database; jangan mengirim isinya lewat chat.
- `configure --team-number '+62NOMOR_TIM'` membuat konfigurasi privat dan dua token acak tanpa menimpa konfigurasi lama. Jika dibuat manual, token internal/gateway masing-masing minimal 32 karakter.
- Field provider: `GROQ_API_KEY`, `GROQ_VISION_MODEL`, `SERPAPI_API_KEY`; `GROQ_TEXT_MODEL` opsional. `ENABLE_GOOGLE_VISION=false` default; project Google diperlukan hanya bila Vision diaktifkan.
- Sesi WhatsApp berada di `.runtime/openclaw-state`; QR dipindai lokal melalui menu perangkat tertaut, bukan dikirim ke chat.
- Cluster PostgreSQL demo berada di `.runtime/postgres-intake/data`, hanya loopback **55432**. Database `sigapi_demo` dan `sigapi_test` terpisah; PostgreSQL lama 5432 tidak diubah. Cluster demo belum berupa Windows service.
- Konfigurasi routing privat `.runtime/task3/config.json`; GeoJSON `.runtime/task3/kota-malang.geojson`. Ekspor inspeksi, media dan hasil provider tetap privat.

### 14.2 Bootstrap checkout baru yang dicatat

```powershell
Set-Location D:\sigapi
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
New-Item -ItemType Directory -Force .runtime/node | Out-Null
npm.cmd pack node-win-x64@26.12.1 --pack-destination .runtime
tar.exe -xf .runtime/node-win-x64-26.12.1.tgz -C .runtime/node
$env:PATH=(Join-Path $PWD '.runtime/node/package/bin') + ';' + $env:PATH
$npmCli=Join-Path (Split-Path (Get-Command npm.cmd).Source) 'node_modules/npm/bin/npm-cli.js'
& .\.runtime\node\package\bin\node.exe $npmCli install --prefix .runtime/openclaw openclaw@2026.10.6 '@openclaw/whatsapp@2026.10.6' --omit=dev --no-audit --no-fund
```

Setiap langkah harus sukses sebelum langkah bergantung dijalankan. Pemanggilan `npm-cli.js` memakai Node lokal karena `npm.cmd` sistem dapat memilih Node di sampingnya. `spawn EPERM` bukan bukti instalasi siap. FFmpeg/FFprobe dipasang dari distribusi resmi yang diverifikasi, lalu digunakan dari direktori runtime lokal.

### 14.3 Persiapan dan empat proses Task 3

```powershell
Set-Location D:\sigapi
.\.venv\Scripts\python.exe -m backend.cli db-start
.\.venv\Scripts\python.exe -m backend.cli migrate
.\.venv\Scripts\python.exe -m backend.cli task3-init
.\.venv\Scripts\python.exe -m backend.cli task3-status
```

Jalankan masing-masing pada terminal berbeda:

```powershell
.\.venv\Scripts\python.exe -m backend.cli serve
.\.venv\Scripts\python.exe -m backend.cli worker
.\.venv\Scripts\python.exe -m backend.cli analysis-worker
.\.venv\Scripts\python.exe -m backend.cli openclaw -- gateway run
```

Proses lama tidak otomatis mengambil kode baru; operator menghentikan proses miliknya melalui terminal sebelum menjalankan ulang. Jangan menjalankan dua gateway akun sama. Sesi pairing yang tersimpan dipakai kembali. `serve --smoke` hanya mode metadata Task 1 dan bukan API intake persisten yang dipakai plugin utama sekarang.

Migrasi melewati versi yang sudah diterapkan. Migrasi tambahan mempertahankan data Task 2 dan **tidak otomatis menganalisis/mengirim laporan lama**.

### 14.4 Pairing, readiness, dan smoke provider

```powershell
.\.venv\Scripts\python.exe -m backend.cli readiness
.\.venv\Scripts\python.exe -m backend.cli openclaw -- config validate
.\.venv\Scripts\python.exe -m backend.cli openclaw -- channels login --channel whatsapp
.\.venv\Scripts\python.exe -m backend.cli intake-status
.\.venv\Scripts\python.exe -m backend.cli providers --image '.runtime/media/api.jpg' --case fire
```

CLI provider menerima `--provider both` (default: Groq + fallback web), `web`, `serpapi`, `groq`, atau `vision`. Vision tetap membutuhkan flag aktif. `--case` adalah label operator, bukan penilaian otomatis. Hasil unavailable tetap disimpan dan menghasilkan exit code 1. Hasil CLI provider bukan keputusan akhir sebuah laporan.

`readiness` memeriksa keberadaan konfigurasi/komponen; nilai true tidak membuktikan akun, AI, atau WhatsApp berhasil secara menyeluruh. `intake-status` memeriksa jumlah/status tanpa mencetak identitas atau isi laporan.

Jika sengaja menyiapkan Vision, panduan mencatat urutan `gcloud auth login`, memilih project, mengaktifkan `vision.googleapis.com`, `gcloud auth application-default login`, lalu `gcloud auth application-default set-quota-project PROJECT_ID`. Login/billing merupakan setup akun lokal; aplikasi tidak melakukannya otomatis.

### 14.5 Data wilayah dan aktivasi distribusi

```powershell
.\.venv\Scripts\python.exe -m backend.cli task3-fetch region
.\.venv\Scripts\python.exe -m backend.cli task3-fetch firms
.\.venv\Scripts\python.exe -m backend.cli task3-approve-region --sha256 HASH_FILE --reason "Alasan pemeriksaan batas dan lokasi demo"
```

Operator mengisi dua tujuan `community/authority` pada konfigurasi privat, memeriksa perbedaan nomor bot/pelapor, memasukkan penerima ke `outboundRecipients`, serta menyetujui hash batas. Setelah setup sesuai, `distribution_enabled` dapat diaktifkan. Konfigurasi dibaca ulang saat mulai kirim. **Pada kondisi terakhir yang tercatat, distribusi masih false, tujuan belum tersedia dan persetujuan batas kosong.**

### 14.6 Tinjauan bukti, insiden, dan delivery

```powershell
.\.venv\Scripts\python.exe -m backend.cli report-inspect UUID_LAPORAN --output .runtime/task3/inspection.json
.\.venv\Scripts\python.exe -m backend.cli analyze UUID_LAPORAN
.\.venv\Scripts\python.exe -m backend.cli review-evidence UUID_LAPORAN --key UUID_MEDIA:0 --reason "Alasan review" --reference https://sumber-bukti.example/halaman
.\.venv\Scripts\python.exe -m backend.cli review-incident UUID_LAPORAN --merge-into UUID_KANDIDAT --reason "Bukti kejadian sama"
.\.venv\Scripts\python.exe -m backend.cli review-incident UUID_LAPORAN --reason "Bukti kejadian terpisah"
.\.venv\Scripts\python.exe -m backend.cli reconcile-delivery UUID_OUTBOX --receipt ID_PESAN_WHATSAPP --reason "Receipt diperiksa"
.\.venv\Scripts\python.exe -m backend.cli reconcile-delivery UUID_OUTBOX --retry --reason "Riwayat diperiksa dan dipastikan belum terkirim"
```

Gunakan UUID lengkap. `analyze` adalah opt-in operator untuk laporan lama. Review bukti menunjuk evidence key media/frame yang benar, alasan, dan referensi; bukti awal tetap disimpan. `review-incident` tanpa `--merge-into` mengonfirmasi insiden terpisah atau memisahkan report dari kelompok lama. Ekspor inspeksi mengandung data pribadi dan tidak dipublikasikan.

Sumber: [D07]; [D08]; [D09]; [D01]; [D14].

## 15. Pelajaran integrasi dan troubleshooting yang tercatat

| Gejala/isu | Temuan dan penanganan dalam repo |
| --- | --- |
| Pesan WhatsApp jatuh ke agent OpenAI bawaan | Manifest bridge memerlukan **`activation.onStartup=true`** pada OpenClaw 2026.10.6. Plugin enabled di inventory belum berarti dimuat saat gateway start. Perbaiki aktivasi/routing; bukan menambah key OpenAI. |
| Memeriksa plugin | `openclaw -- plugins inspect sigapi-validation-demo --runtime --json`; bukti yang dicari `imported=true`, `hookCount=2`, typed hooks `message_received` dan `before_dispatch`. Inspeksi proses sendiri belum menggantikan uji pesan setelah restart. |
| Layanan belum siap walau backend aktif | `conversation_id` pada kedua hook bisa berbeda. Korelasi memakai channel/account/sender/provider message ID dan mempertahankan conversation penerimaan untuk backend. |
| Diagnosis aman | Log membedakan `FACTS_NOT_FOUND`, `BACKEND_HTTP_<status>`, `INVALID_BACKEND_RESULT`, `BACKEND_REQUEST_FAILED`, tanpa isi pesan/secret. |
| “Background check did not complete” pada uji lama | Ledger mengaitkannya dengan heartbeat OpenClaw terpisah, bukan worker intake. Cadence berulang dinonaktifkan melalui `agents.defaults.heartbeat.every=0m`; targeted wake tetap mungkin. |
| 429 pada video | Frame ketiga pernah gagal sebelum pacing; run berikutnya berhasil setelah jeda 35 detik. Run gagal tetap disimpan sebagai gagal. |
| Worker lama mengalahkan job yang diambil alih | Review menemukan masalah token fencing; diperbaiki dan memiliki regresi. |
| Koreksi laporan masih memakai anchor insiden usang | Acuan insiden diperbarui setelah koreksi, dengan pengujian urutan koreksi. |
| Waktu baru diketahui setelah provisional escalation | Pencarian kandidat dijalankan ulang setelah enrichment waktu. |
| Migrasi berulang berkonflik DDL saat intake aktif | Migrasi menghormati `schema_versions` agar DDL versi terpasang tidak diulang. |

Hook `message_received` hanya observasi; `before_dispatch` mengambil alih agar tidak ada balasan agent kedua. Manifest/plugin berubah memerlukan restart gateway. Prototype smoke lama hanya menyimpan korelasi metadata lima menit dalam memori; ini telah digantikan spool/intake persisten.

Sumber: [D02] §5; [D07] troubleshooting; [D09] review akhir; [D14].

## 16. Form GPS dan TRACK: perincian Task 4 yang belum tersedia

Bagian ini adalah **rencana implementasi**, bukan bukti form sudah berjalan. Radius 2 km sudah ada pada knowledge; tambahan di bawah adalah parameter demo, kontrol submit, endpoint, dan privasi yang lebih rinci.

### 16.1 Parameter dan validasi server

| Parameter | Pilihan demo |
| --- | --- |
| Jarak | `distance <= 2000 m`. |
| Akurasi | `0 < accuracy_m <= 100 m`. |
| Usia fix | Maksimal **60 detik** terhadap waktu server. |
| Waktu masa depan | Lebih dari **5 detik** di masa depan ditolak. |
| Angka koordinat | Finite, latitude/longitude dalam rentang sah; NaN ditolak. |
| Deskripsi | Opsional, maksimal **2.000 karakter**. |
| Foto | Opsional, maksimal **10 MB**; upload/body dibatasi. |
| Rate limit | **10 upaya per 10 menit per IP+slug**, counter database. |

Error di luar radius direncanakan memakai **HTTP 422 `OUT_OF_RADIUS`**. Kode lokasi lain adalah `INVALID_LOCATION`, `STALE_LOCATION`, atau `INACCURATE_LOCATION`; sumber belum menetapkan status HTTP masing-masing. Kegagalan teknis tidak membuat verification event atau suara invalid.

Jarak dihitung dari **titik kejadian**, bukan centroid yang bisa berubah setelah merge. Koreksi titik mempunyai revision dan waktu tercatat.

Payload rencana `POST /api/laporan/{slug_id}/verifications` memuat choice, latitude, longitude, accuracy, GPS fix time, deskripsi/foto opsional, solved, dan `request_id`. Request ID mencegah replay jaringan, bukan mengidentifikasi satu orang. Validasi slug/insiden serta normalisasi invalid+solved dilakukan server.

### 16.2 Overview, agregasi, dan TRACK

- Publik menerima foto turunan yang disetujui operator setelah pemeriksaan sensitif; asli tetap privat. Jika belum ada foto aman, tampilkan placeholder beralasan.
- GPS pengisi, nomor/identitas pelapor, EXIF lokasi, serta akses media privat tidak masuk payload publik.
- Rencana agregat: `none/supporting_valid/supporting_invalid/disputed`; `claimed_solved` bila ada valid+solved. Klaim selesai tidak menutup insiden atau menghapus konflik.
- TRACK membaca database **tanpa panggilan model**. Tanpa ID, pengguna mendapat pilihan/laporan miliknya. ID tidak ada dan ID milik orang lain memberi jawaban aman yang sama agar tidak membocorkan keberadaan laporan.
- Hosting publik terpisah; tunnel hanya mengarah ke aplikasi publik, bukan API internal/gateway/operator.

Pengujian batas yang direncanakan: 1999/2000/2001 m, accuracy 100/101 m, usia 60/61 detik, waktu masa depan, NaN, replay, invalid+solved, konflik, TRACK lintas pemilik dan kebocoran media/GPS. Uji ponsel HTTPS menggunakan insiden simulasi aman; koordinat sintetis dilabel test dan tidak diklaim sebagai konfirmasi lapangan asli.

Sumber: [D04] Task 4; [D03] form publik; [D02] §12; [D11].

## 17. Dashboard Admin Kota: spesifikasi tambahan

**Status:** spesifikasi produk, belum dashboard yang tersedia pada audit Task 3. Fungsinya memantau laporan dan mengatur distribusi, bukan mengelola operasi pemadaman.

### 17.1 Peran dan lima menu

Admin Kota hanya mengakses laporan/pengaturan kota atau kabupaten kewenangannya. Admin Sistem mengelola kota, akun admin dan pemantauan tingkat sistem. Warga tidak membuat report melalui dashboard; pelaporan tetap WhatsApp.

Lima menu: **Overview, Laporan, Peta Kebakaran, Pihak Berwenang, Saluran MPA**.

### 17.2 Overview

Empat kartu statistik: Laporan Hari Ini, Sudah Diteruskan, Belum Lengkap, Belum Terverifikasi. Hitungan memakai data sistem, bukan angka statis. Laporan antre/hold/parsial tidak semuanya dimasukkan sebagai belum lengkap.

Konten: peta ringkas report dan FIRMS, daftar terbaru, penanda menonjol jika orang terancam/perlu evakuasi; konflik/kontribusi ditambahkan jika ada. Dimensi kepercayaan, pengiriman, konfirmasi dan solved dipisahkan.

### 17.3 Daftar dan detail laporan

Kolom yang dirancang: ID, waktu, wilayah administratif/koordinat, jenis hutan/lahan/permukiman, kepercayaan, status serta hasil tujuan pengiriman, konfirmasi publik bersumber/waktu, solved claim, dan akses detail. Filter: tanggal, kecamatan, jenis, status, kepercayaan.

Detail menampilkan:

- Media asli dengan akses terbatas, keterangan asli dan ringkasan AI.
- Peta/koordinat, api/asap saat ini, luas perkiraan, kedekatan fasilitas/permukiman, jenis lahan, ancaman/evakuasi jika tersedia.
- Bukti web/FIRMS/klaster/konsistensi serta provenance; rancangan lama menyebut reputasi nomor, sedangkan MVP tidak menganggap nomor baru buruk.
- Incident ID, report sumber, pencocokan/duplikasi, link publik setelah tersedia.
- Kontribusi valid/invalid, konflik, sumber `public_link`, waktu dan solved claim; GPS pengisi dibatasi akses.
- Hasil/waktu tiap tujuan; nomor pelapor hanya dengan consent dan izin peran.

Spesifikasi masih menyebut skor kelengkapan/kepercayaan. Implementasi demo yang dicatat audit memakai alasan keputusan tanpa persentase; dokumen ini tidak menyatakan skor UI tersebut sudah tersedia.

### 17.4 Peta Kebakaran

Dua layer: report warga dan hotspot FIRMS. Filter periode hari ini, tujuh hari, atau rentang tanggal. Klik marker membuka ringkasan/foto/kepercayaan. Klaster insiden mengurangi penanda ganda, tetapi report sumber tetap terpisah dan grouping bisa dikoreksi.

Peta dibatasi wilayah admin. Sensor dan waktu pengamatan hotspot ditampilkan; label dekat hotspot terbaru/belum ada hotspot mengikuti hasil pemeriksaan, bukan kebenaran final.

### 17.5 Pihak Berwenang

Konfigurasi mencakup nama instansi/pos damkar, satu atau beberapa nomor WhatsApp, alamat, koordinat opsional, serta aktif/nonaktif. Admin mengelola penerima wilayahnya dan menjalankan uji kirim yang diotorisasi.

Pemilihan pos dapat mengikuti cakupan atau kedekatan geografis; terdekat secara koordinat bukan otomatis waktu tempuh tercepat. Jika kota belum memiliki admin/penerima, rancangan fallback memberikan kontak Posko/darurat yang telah diverifikasi dan tidak mengklaim penerusan berhasil.

### 17.6 Saluran MPA dan monitoring

Konfigurasi saluran memuat nama, tautan undangan, status konfigurasi/koneksi. Saluran dikonfigurasi sekali dan tautan dapat disalin. Auto-create Channel melalui OpenClaw **belum terbukti**; fallback adalah saluran manual, grup, atau kontak koordinator yang dikonfigurasi.

JID outbound Channel `@newsletter` dalam dokumentasi OpenClaw bukan bukti pembuatan/pengiriman Channel pada akun proyek. Pengiriman Task 3 masih dirancang dengan kontak uji.

Monitoring menampilkan tujuan, waktu, upaya/hasil, kegagalan dan retry yang aman. Audit dasar sudah wajib pada backend; prioritas P2 untuk halaman audit lanjutan tidak menunda pencatatan dasar.

Prioritas spesifikasi dashboard:

| Prioritas | Bagian |
| --- | --- |
| P0 | Laporan/detail, form publik, konfigurasi otoritas dan MPA. |
| P1 | Overview dan peta. |
| P2 | Riwayat/audit lanjutan, ekspor CSV/PDF. |

Ini prioritas spesifikasi, bukan pernyataan fitur telah dibuat. Redaksi foto, ketelitian lokasi publik, rincian anti-spam dan retensi produk masih perlu diselaraskan sebelum pilot produksi.

Sumber: [D12]; [D02] §4–5 dan §14; [D11].

## 18. Roadmap, status implementasi, dan batas penerimaan

### 18.1 Lima task berurutan

| Task | Lingkup | Status terakhir yang dicatat |
| --- | --- | --- |
| 1 | Koneksi OpenClaw, Groq dan web; input/media smoke. | **Selesai integration smoke nyata**, 23 Oktober. |
| 2 | Intake persisten dan kelengkapan. | **Selesai**, laporan lengkap WhatsApp/PostgreSQL pada 23 Oktober pukul **22:51 WIB**. |
| 3 | Pemeriksaan bukti, keputusan, insiden, distribusi terkontrol. | **Implementasi tersedia, live gate belum selesai**. Dua penerima uji belum ada; persetujuan batas belum ada. |
| 4 | Form GPS, agregasi kontribusi dan TRACK. | **Belum diimplementasikan** pada audit. |
| 5 | Rehearsal, operator UI ringkas, retensi/purge, pemeriksaan dan handoff. | **Belum selesai**; CLI dan audit dasar telah tersedia lebih dahulu. |

Target rencana demo: 25 Oktober 2026. Alokasi lama: hari pertama Task 1–2, hari kedua Task 3, hari ketiga Task 4–5; ini target kerja, bukan jaminan durasi. Implementasi direncanakan berurutan; ekstraksi dokumentasi ini tidak melaksanakan task berikutnya.

### 18.2 Bukti pengujian yang tercatat

| Tahap | Bukti | Batas klaim |
| --- | --- | --- |
| Pemilihan model | Daftar model akun HTTP 200; gambar putih sintetis 128×128 menghasilkan JSON schema-valid sekitar 0,95 detik. | Bukan SLA atau benchmark kebakaran. |
| Web nyata | Potret Grace Hopper domain publik: upload+exact search SerpApi berhasil, 100 kandidat tersimpan, dua operasi HTTP, pengulangan memakai cache. | Kandidat kecocokan, bukan probabilitas kebenaran. Vision tidak diperlukan. |
| Foto api | Operator menyatakan foto kebakaran hutan; Groq melihat api/asap clear, SerpApi memberi kandidat exact match. | Memerlukan review sumber/waktu; bukan vonis palsu atau konfirmasi lokasi. |
| Blur | Turunan buatan 8×8 lalu diperbesar/diburamkan menghasilkan unclear. | Bukan foto buram lapangan independen. |
| Video | Video 2,900211 detik didecode ke tiga frame; setelah pacing, seluruh respons Groq valid tanpa api/asap sesuai deskripsi operator. | Tidak mengamati seluruh video dan bukan benchmark akurasi. |
| Task 1 | Empat jenis input WhatsApp dikonfirmasi pengguna; **37 tes Python, 6 Node** dan sintaks tercatat lulus. | Metadata/CLI provider saat itu belum berarti intake persisten atau routing otomatis. |
| Task 2 | **58 tes Python, 12 Node**; PostgreSQL, HTTP loopback dan transport Node; laporan WhatsApp lengkap nyata diperiksa di database. | `complete` berarti minimum lengkap, belum diverifikasi/dipublikasikan. |
| Task 3 | **105 tes Python tanpa fail/error/skip, 13 Node**; sintaks/diff check; ekstraksi Groq dua pesan serta unduhan OSM/NASA nyata. | Fixture/local integration tidak membuktikan distribusi WhatsApp end-to-end. |
| Audit 24 Oktober | Subset **30 tes** rules/web/conversation tercatat lulus. | Tidak membuktikan fitur yang belum dibuat sudah tersedia. |

Angka di atas merupakan rekam hasil pada dokumen sumber, **bukan pengujian ulang saat membuat suplemen ini**. Bukti privat tetap berada di runtime dan tidak disalin.

### 18.3 Gate Task 3 yang masih pending

WhatsApp nyata harus menunjukkan: percakapan alami, hasil provider tersimpan, konflik menahan komunitas, eskalasi terlabel mencapai otoritas uji, dan laporan yang memenuhi aturan terkirim sekali. Groq langsung, unduhan data, readiness, atau tes fixture sendirian tidak meluluskan gate ini.

Pada ledger terakhir tidak ada laporan lama yang di-opt-in otomatis, distribusi masih nonaktif, dan Task 4/5 belum dikerjakan. Tidak ada dasar menyebut sistem telah beroperasi nasional atau memiliki mitra resmi.

### 18.4 Kekurangan dan batas teknis yang masih tercatat

1. **Konsistensi lintas sumber belum lengkap:** observasi dan metadata ada, tetapi hasil khusus perbandingan isi/caption/lokasi/waktu belum tersedia untuk mesin keputusan.
2. **Panduan keselamatan belum muncul** dalam balasan belum lengkap/darurat.
3. **Provisional incident kosong bekas merge** bisa muncul sebagai kandidat; menambah review operator, tanpa auto-merge atau bypass distribusi.
4. **Exception tak terduga pada satu frame** dapat melewati frame tersisa video itu. Dicatat parsial/unavailable dan menahan distribusi; media lain tetap diproses.
5. Dashboard, form/route publik, verification events dan TRACK penuh belum tersedia pada audit.
6. Mekanisme retensi/purge teruji, backup produksi, serta UI antrean gagal belum tersedia.

### 18.5 Handoff Task 5 yang direncanakan

Retensi demo **tujuh hari** untuk input/media/GPS/spool/log sensitif, dengan purge lokal teruji yang tidak berjalan otomatis saat start dan tidak menghapus konfigurasi/credential. Cakupan retensi umum juga mempertimbangkan transcript OpenClaw dan backup. Ini rencana, bukan fitur purge yang sudah tersedia.

Operator UI ringkas direncanakan menampilkan report/incident, bukti/alasan, hold, tujuan sukses/gagal/unknown, kontribusi, solved claim, readiness DB/gateway dan status provider terakhir—tanpa angka keberhasilan statis.

Handoff meliputi checkout hingga demo, startup/shutdown, pairing ulang, pemulihan spool/job, pemeriksaan credential tanpa membocorkan secret, rekonsiliasi unknown, dan reset simulasi. Data demo tidak menjadi dataset training tanpa persetujuan. Rekaman membedakan provider nyata, snapshot FIRMS, insiden simulasi dan injected failure.

Sumber: [D01]; [D04]; [D07]; [D08]; [D09]; [D10]; [D11]; [D14].

## 19. Evaluasi tambahan dan cara membaca hasil

Selain metrik pada knowledge v3, rancangan teknis menambahkan:

- Kualitas ekstraksi per field, recall ancaman eksplisit, dan jumlah fakta tanpa sumber.
- Jumlah giliran sampai lengkap, biaya model per report, serta latensi tiap tahap/provider.
- Ketepatan routing terhadap label wilayah, salah merge/pisah, serta keberhasilan transport per tujuan.

Dataset perlu memuat bahasa Indonesia informal/typo, pesan bertahap, hutan/lahan/permukiman, media ambigu, konflik teks-gambar dan ancaman orang. Contoh tuning prompt dipisahkan dari evaluasi.

Target keras suite penerimaan: tidak ada kebocoran nomor ke MPA, akses TRACK lintas warga, atau status “diteruskan” palsu. Ini target pengujian, bukan jaminan dunia nyata. Threshold kualitas/latensi ditetapkan setelah baseline, bukan dihasilkan dari beberapa smoke sample.

Fixture dipakai untuk memaksa 429, outage, restart, stale revision, consent dicabut sebelum kirim, replay dan receipt ambigu. Keberhasilan integrasi akun/provider dibuktikan terpisah melalui uji nyata. Database tes menggunakan `TEST_DATABASE_URL` terpisah, tidak diarahkan ke data demo.

Perintah verifikasi yang didokumentasikan:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.runtime\node\package\bin\node.exe --test openclaw-plugin/index.test.js openclaw-plugin/intake.test.js
.\.runtime\node\package\bin\node.exe --check openclaw-plugin/index.js
```

Sumber: [D02] §16; [D04] pemeriksaan lintas task; [D01]; [D08]; [D09].

## 20. Konteks bisnis, pembanding, dan submission dari arsip

Bagian ini berasal dari dokumen v2 tanggal 20 Oktober. Isinya menambah konteks yang tidak dimuat lengkap pada knowledge v3, tetapi **bukan riset pasar/aturan lomba terbaru yang diverifikasi ulang**.

### 20.1 Asal dan model bisnis

- Produk dikembangkan dari **LaporPak**, yang mempunyai konteks alur WhatsApp, AI, tiket, dan dashboard. Komponen yang diwarisi tidak otomatis seluruhnya dipakai.
- Nama produk/identitas visual masih sementara dalam arsip; penamaan SIGAPI di repo tidak membuktikan merek final atau keputusan visual tim.
- Usulan bisnis **B2G**: pemerintah daerah, BPBD, dinas terkait dan program kota/desa peduli api.
- Pendapatan yang diusulkan: langganan/kontrak per kota/kabupaten untuk konfigurasi, dukungan dan dashboard.
- Komponen biaya: pesan WhatsApp, pencarian gambar/Vision, AI, hosting dan nomor khusus.
- Surat dukungan/testimoni merupakan rencana, bukan bukti kemitraan. Usulan lama pilot satu–dua kota telah dipersempit menjadi satu wilayah demo Kota Malang.

### 20.2 Pelaporan yang sudah ada dan posisi produk

Arsip menyebut Posko Karhutla Kemenhut, SiPongi+, prototipe IPB dan aplikasi lokal seperti FiRe Pontianak. Penanganan melibatkan Manggala Agni, BNPB/BPBD, TNI/Polri, damkar, MPA dan relawan. Karena itu, jangan membangun narasi seolah belum ada kanal pelaporan kebakaran.

Kontak publik Posko yang tercatat pada arsip: telepon **021-5704618**, WhatsApp **+62 8131-00-35000**, email **posko.karhutla@kehutanan.go.id**. Ini referensi bertanggal dari sumber lama; bukan tujuan yang diaktifkan pada demo dan bukan daftar nomor darurat lokal yang telah diverifikasi untuk routing sekarang.

Pembeda yang **diusulkan untuk diuji**: pelengkapan pesan bebas, normalisasi data, penentuan wilayah, perutean lokal, pemeriksaan bukti dan duplikasi. Klaim bahwa kanal lain seluruhnya manual/tidak mempunyai kemampuan ini memerlukan benchmark, bukan otomatis fakta pembeda.

Instruksi arsip untuk mengirim laporan uji ke Posko adalah rencana historis, **bukan bukti pengujian dan bukan otorisasi pengiriman** dalam pekerjaan ekstraksi ini.

### 20.3 Detail latar satelit yang diwarisi

Arsip menjelaskan FIRMS MODIS/VIIRS near real-time sekitar tiga jam **setelah pengamatan**, bukan berarti satelit selalu mengamati setiap tiga jam. Satelit polar memiliki jeda lintasan; arsip menyebut kira-kira dua kali sehari per sensor. Produk ultra real-time wilayah lain tidak diasumsikan berlaku di Indonesia.

Himawari geostasioner dapat memantau lebih sering; arsip menyebut produk BMKG Geohotspot sekitar sepuluh menit, dengan resolusi kasar dan potensi api kecil terlewat. Awan/asap menghalangi deteksi. Studi Himawari-8 di Kalimantan Tengah yang dikutip mempunyai angka 31,6% dan omission 68,4%; angka tersebut **ilustrasi studi tertentu, bukan akurasi FIRMS umum atau sistem SIGAPI**.

Atribusi/syarat NASA dan BMKG perlu ditelusuri pada paper/UI. Referensi arsip mencakup NASA Earthdata data latency, NASA FIRMS, BMKG satelit/Geohotspot, studi UGM, SiPongi dan penelitian IPB.

### 20.4 Keselamatan dan fitur yang pernah direncanakan

Arsip mengusulkan tombol tindakan setelah laporan, misalnya “Apa yang bisa saya lakukan sambil menunggu?” dan penjelasan sistem. Jawaban dibatasi basis pengetahuan tetap dari panduan resmi BNPB/Kemenhut/damkar; AI memilih/merangkum, bukan mengarang instruksi.

Isi yang dicontohkan: menjauh, tidak mencoba memadamkan api besar sendiri, mengurangi paparan asap, membantu kelompok rentan dan mengikuti petugas. Cakupan tetap keselamatan kebakaran/penjelasan sistem, bukan ASK umum. Audit terbaru menyatakan panduan balasan ini **belum tersedia**. Nomor lokal tidak boleh ditebak dari generasi model.

### 20.5 Gateway: roadmap dan batas klaim lama

Arsip mencatat risiko jalur WhatsApp Web/Baileys: nomor dibatasi/diblokir, sesi QR terputus, tanpa SLA. Mitigasi yang dirancang: nomor khusus, rate limit, monitoring, pemulihan, dan adapter agar produksi dapat pindah ke WhatsApp Business Platform resmi.

Pembuatan Channel melalui gateway dan dukungan resmi Groups API disebut sebagai kemungkinan yang perlu dicek. Dokumen lama memakai sumber pihak ketiga untuk sebagian klaim; tidak membuktikan kemampuan Meta/OpenClaw terkini. Integrasi Channel otomatis tetap belum teruji pada proyek.

### 20.6 Submission lomba yang tercatat

| Topik | Catatan arsip; perlu verifikasi pada aturan penyelenggara |
| --- | --- |
| Pendaftaran | Ditutup **25 Oktober 2026**, paper/video melalui dashboard peserta. |
| Final | **10–11 November 2026**, SMESCO Indonesia disebut dengan lokasi menunggu konfirmasi; 18 finalis. |
| Lanjutan/hadiah | APICTA Award 7 Desember 2026 dan hadiah total Rp100 juta disebut pada arsip. |
| Paper | Bahasa Inggris, PDF maksimal **15 halaman / 20 MB**, dikirim sebagai tautan. |
| Video | Disarankan, maksimal **lima menit**, YouTube unlisted/public, gambaran solusi/fitur/demo. |
| Kategori usulan | Inclusions & Community Services → Sustainability & Environment; alternatif Public Sector & Government/Citizen Services jika ada keterlibatan instansi. |
| Ketentuan belum terbaca | Kewajiban domain `.id` dan kesiapan/jenis karya harus diperiksa pada developerday.id. |

Tiga belas bagian paper yang dicatat: Title Slide; Problem Statement; Target User & Market; Proposed Solution; Key Features & Tech Stack; Screenshots or Product Demo; Competitive Advantage; Current Status & Development Plan; Business Model; Impact Plan; Roadmap & Future Direction; Team Profile & Contact; Reference.

Prioritas kerja arsip: sistem → paper → video. Pembagian penulisan, dukungan mitra dan identitas visual pernah terbuka; daftar lama tidak otomatis seluruhnya masih menjadi blocker sekarang.

Sumber: [D13] §2–3, §8–10, §14–21; [D02] dasar rancangan; [D11].

## 21. Rekonsiliasi aturan lama dan hal yang tidak boleh disimpulkan

| Pernyataan pada sumber lama | Pembacaan setelah keputusan terbaru |
| --- | --- |
| Semua laporan lengkap/skor rendah tetap diteruskan. | Digantikan kebijakan demo: konflik/unavailable menahan komunitas; ancaman tinggi memenuhi syarat memakai eskalasi terlabel. |
| Foto/video hanya dianjurkan; lokasi+deskripsi dapat cukup. | Digantikan v3: media awal wajib dan harus dapat dibuka. |
| TRACK hanya dua status; link verifikasi tidak dipakai. | Digantikan v3: form/link termasuk target dan TRACK memisahkan delivery, kontribusi serta solved. Implementasinya tetap Task 4. |
| Waktu pesan otomatis merupakan waktu kejadian. | Waktu pesan, klaim kejadian, media, satelit dan fetch dipisahkan. |
| Vision/billing Google wajib. | Digantikan amendemen 23 Oktober: SerpApi utama, Vision opt-in. Minimal satu web provider nyata tetap menjadi gate Task 1. |
| Persetujuan pemrosesan khusus diminta. | Keputusan demo 24 Oktober tanpa pemberitahuan/gerbang khusus; izin berbagi nomor tetap eksplisit. |
| Alamat teks dapat dipetakan untuk memenuhi lokasi. | Keputusan demo 24 Oktober: teks hanya klarifikasi, pin/koordinat terkonfirmasi wajib. |
| EXIF kosong menghalangi pembuktian sehingga otomatis hold. | Tidak menjadi syarat demo; hilangnya EXIF sendiri tidak memblokir dan tidak berarti autentik/konsisten. |
| Routing/akurasi GPS/parameter FIRMS semuanya belum diputuskan. | Pada produk umum masih riset, tetapi parameter demo tertentu sudah dipilih. Jangan membuka ulang pilihan demo hanya karena tabel historis belum diperbarui. |
| PostgreSQL/PostGIS wajib; plugin harus TypeScript. | Demo tidak mewajibkan PostGIS; implementasi bridge tercatat JavaScript. |
| Semua butir Task 3 masih kosong berarti belum ada kode. | Checklist lama belum diperbarui penuh; panduan/ledger Task 3 lebih baru mencatat implementasi, tetapi live gate tetap pending. |
| Belum pairing/belum ada Git atau kode. | Status historis awal penyusunan; Task 1/2 kemudian terbukti pada catatan 23 Oktober. |
| Auto-create Channel lewat tombol admin sudah bisa. | Baru spesifikasi/kemungkinan; belum terbukti pada akun proyek. |
| Ada skor persentase/rumus kelengkapan berbobot sama yang sudah final. | Bobot lama tidak final; demo memakai alasan keputusan tanpa probabilitas terkalibrasi. |
| Ada ASK umum, REQUEST, fast-track tanpa minimum, atau progres pemadaman berkala. | Di luar lingkup; eskalasi ancaman bukan bypass minimum. |
| Semua tes lulus berarti demo end-to-end dan produksi siap. | Uji lokal/fixture, integrasi provider, WhatsApp nyata, dan penerimaan bisnis dibuktikan terpisah. |

Sumber: [D11]; [D04]; [D09]; [D12]; [D13]; [D14].

## 22. Indeks sumber dan cakupan ekstraksi

Seluruh dokumen Markdown sistem yang ditemukan di repo sebelum suplemen ini dibuat telah dicakup. Satu file menjadi pembanding; 14 lainnya menjadi sumber delta. Referensi ini menunjuk file repo, bukan mengharuskan pembaca membuka konfigurasi privat.

| ID | Dokumen | Konteks tambahan utama |
| --- | --- | --- |
| Dasar | [Knowledge v3](Knowledge_Doc_Terbaru_DeveloperDay_Karhutla_2026.md) | Pembanding, bukan salinan ulang isi suplemen. |
| D01 | [README](README.md) | Peta lima task dan status terbaru, runtime/pemeriksaan. |
| D02 | [Rancangan OpenClaw dan AI](docs/superpowers/specs/2026-10-21-openclaw-ai-design.md) | Arsitektur, kontrak, identitas, data, keamanan, evaluasi. |
| D03 | [Desain demo validasi](docs/superpowers/specs/2026-10-22-validation-demo-design.md) | Keputusan demo dan batas penerimaan. |
| D04 | [Rencana lima task](docs/superpowers/plans/2026-10-22-validation-demo-implementation.md) | Parameter, kontrak, langkah Task 1–5, form/retensi/handoff. |
| D05 | [Desain fallback web](docs/superpowers/specs/2026-10-23-web-evidence-fallback-design.md) | SerpApi, Vision opt-in, hash, turunan media, budget. |
| D06 | [Rencana perubahan fallback](docs/superpowers/plans/2026-10-23-web-evidence-fallback.md) | Lingkup perubahan dan gerbang/regresi fallback. |
| D07 | [Setup Task 1](docs/setup-task-1.md) | Instalasi, provider, pairing, smoke, troubleshooting. |
| D08 | [Setup Task 2](docs/setup-task-2.md) | Intake persisten, spool, urutan, batas, live gate. |
| D09 | [Setup Task 3](docs/setup-task-3.md) | Analisis, FIRMS/batas, operator, routing/delivery, kekurangan. |
| D10 | [Pemilihan model Groq](docs/groq-model-selection.md) | Model, Free Plan, token/biaya dan bukti terbatas. |
| D11 | [Audit knowledge 24 Oktober](docs/audit-knowledge-v3-2026-10-24.md) | Amendemen keputusan, kesesuaian/gap dan klarifikasi selesai. |
| D12 | [Spesifikasi Dashboard Admin Kota](<Spesifikasi Dashboard Admin Kota - Bot WhatsApp Pelaporan Karhutla.md>) | Menu, field, peran, peta, penerima, prioritas UI. |
| D13 | [Arsip knowledge v2](<Knowledge Doc Bot WhatsApp Pelaporan Karhutla (.id DeveloperDay 2026).md>) | Asal LaporPak, bisnis, pembanding, satelit, lomba dan aturan yang digantikan. |
| D14 | [Ledger progres implementasi](.superpowers/sdd/2026-10-22-validation-demo-implementation/progress.md) | Keputusan pelaksanaan, debugging, pengujian/live gate dan keterbatasan. |

[D01]: README.md
[D02]: docs/superpowers/specs/2026-10-21-openclaw-ai-design.md
[D03]: docs/superpowers/specs/2026-10-22-validation-demo-design.md
[D04]: docs/superpowers/plans/2026-10-22-validation-demo-implementation.md
[D05]: docs/superpowers/specs/2026-10-23-web-evidence-fallback-design.md
[D06]: docs/superpowers/plans/2026-10-23-web-evidence-fallback.md
[D07]: docs/setup-task-1.md
[D08]: docs/setup-task-2.md
[D09]: docs/setup-task-3.md
[D10]: docs/groq-model-selection.md
[D11]: docs/audit-knowledge-v3-2026-10-24.md
[D12]: <Spesifikasi Dashboard Admin Kota - Bot WhatsApp Pelaporan Karhutla.md>
[D13]: <Knowledge Doc Bot WhatsApp Pelaporan Karhutla (.id DeveloperDay 2026).md>
[D14]: .superpowers/sdd/2026-10-22-validation-demo-implementation/progress.md
