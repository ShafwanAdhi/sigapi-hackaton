# Rencana Implementasi Demo OpenClaw: Validasi dan Verifikasi

> Untuk pelaksana: gunakan skill `superpowers:executing-plans`, kerjakan sendiri secara berurutan. Jangan mulai task berikutnya sebelum pemeriksaan task sebelumnya lolos. Rencana ini belum menjalankan instalasi, aktivasi akun, atau implementasi.

**Tujuan:** demo WhatsApp nyata yang memeriksa input melalui Groq dan Google Vision, menunjukkan alasan keputusan distribusi, lalu menerima konfirmasi publik berbasis GPS dan menjawab TRACK.

**Arsitektur:** satu backend FastAPI, satu worker persisten, PostgreSQL lokal, plugin penghubung OpenClaw, dan halaman HTML publik sederhana. OpenClaw menangani transport; model mengekstrak informasi; kode menentukan aturan. Tidak ada agent kedua yang membalas warga.

**Stack:** Python 3.11, FastAPI/Pydantic, psycopg 3, HTTPX, google-cloud-vision, Pillow; OpenClaw/plugin TypeScript; FFmpeg untuk frame video. PostgreSQL 16 sudah berjalan. Gunakan PostgreSQL tanpa mewajibkan PostGIS untuk demo; Haversine cukup untuk radius form. Cloudflare Tunnel meneruskan hanya aplikasi publik HTTPS. Kunci versi dependensi setelah smoke test, jangan mengambil versi bergerak pada setiap start.

**Acuan:** [desain demo](../specs/2026-10-22-validation-demo-design.md), [desain utama](../specs/2026-10-21-openclaw-ai-design.md), [Knowledge v3](../../../Knowledge_Doc_Terbaru_DeveloperDay_Karhutla_2026.md). Keputusan demo di bawah memperinci acuan; tidak mengubahnya menjadi SOP operasional instansi.

## Keputusan, batas, dan struktur

- Target 25 Oktober 2026; pilot satu wilayah, data kejadian simulasi dan media berizin. WhatsApp, Groq, Vision, serta GPS berjalan nyata. FIRMS boleh snapshot dengan sumber/tanggal. Tidak mengirim ke instansi nyata.
- Foto/video, titik kejadian terkonfirmasi, dan keterangan wajib. Lokasi teks diklarifikasi sampai pelapor mengonfirmasi koordinat; tidak menebak koordinat dari nama desa saja. Maksimal empat pertanyaan klarifikasi per revisi; sesudah itu simpan draft/hold, pengguna dapat melengkapi kemudian.
- GPS: jarak <=2000 m, accuracy >0 dan <=100 m, usia fix <=60 detik terhadap waktu server; timestamp masa depan >5 detik ditolak. Ini parameter demo, bukan batas ilmiah atau bukti bebas spoofing.
- Konflik atau layanan bukti gagal: minta klarifikasi jika relevan, tahan kanal publik; ancaman tinggi yang secara eksplisit dilaporkan tetap dieskalasikan ke nomor uji dengan label BELUM TERVERIFIKASI dan alasan. Kelengkapan tetap wajib; panduan kontak darurat dapat diberikan lebih awal.
- Ancaman tinggi: warga secara eksplisit menyebut orang terancam/terjebak/perlu evakuasi, atau api mengancam rumah/fasilitas. Ekstraksi wajib membawa kutipan sumber; kandidat ancaman yang ambigu ditanyakan ulang. Unknown tidak disebut risiko rendah.
- Publikasi demo memerlukan minimum lengkap, pemeriksaan Groq/Vision berhasil, observasi api/asap pada media, dan tidak ada konflik yang belum selesai. Full/partial web match memicu klarifikasi; kemiripan visual saja dicatat sebagai bukti lemah. Tidak menemukan kecocokan bukan bukti keaslian. FIRMS tidak wajib cocok. Bila dukungan belum cukup, hold publik; eskalasi ancaman tinggi tetap berlaku.
- Satu solved claim ditampilkan sebagai klaim publik berwaktu; tidak menutup insiden otomatis. Kontribusi valid dan invalid yang bertentangan menghasilkan disputed. Event anonim tidak dihitung sebagai orang independen.
- Tidak membangun dashboard penuh, training model, skor persentase keaslian, identitas MPA, atau progres pemadaman berulang. Halaman operator lokal cukup berupa daftar insiden, bukti, outcome, dan tindakan pengelompokan/retry.

Struktur kerja: `backend/` untuk API, aturan, penyimpanan, worker dan halaman; `openclaw-plugin/` untuk transport; `tests/` untuk pemeriksaan Python dan fixtures. Pisahkan modul ingest, evidence, delivery, dan verification saat masing-masing task memperkenalkannya; hindari service/framework tambahan.

Data runtime di direktori privat yang diabaikan Git. Simpan template environment tanpa nilai rahasia. PostgreSQL menggunakan database dan role khusus demo, bukan akun superuser aplikasi. Waktu tersimpan UTC, tampilan Asia/Jakarta. Tidak ada kredensial di prompt, screenshot log, repo, atau chat.

### Kontrak lintas task

| Kontrak | Isi dan pemakai |
| --- | --- |
| `InboundEvent` | account_id, provider_message_id, sender_ref, conversation_id, received_at, text, location opsional, media_refs; adapter ke backend |
| `Report` | report_id, sender_ref, incident_id opsional, revision, fakta/kutipan sumber, lokasi kejadian, media, consent, kelengkapan |
| `EvidenceResult` | report_id, revision, check_type, outcome, reasons, source_refs, checked_at, model/rule_version; outcome membedakan mendukung, konflik, no_match, unavailable |
| `RoutingDecision` | incident_id, revision, publish_allowed, authority_escalation, reasons; dibuat kode, bukan model |
| `Delivery` | incident_id, revision, destination_ref, payload_kind, attempt, outcome, provider_message_id, sent_at |
| `VerificationEvent` | incident_id, choice valid/invalid, coordinates, accuracy_m, gps_fix_at, received_at, distance_m, description/photo opsional, solved, source public_link |

API internal/operator membutuhkan token layanan dan hanya listen lokal. API publik hanya membuka overview teredaksi, media publik tersanitasi, dan submit form. TRACK masuk melalui WhatsApp, tidak menyediakan endpoint publik berisi detail pelapor.

## Task 1 — Buktikan koneksi OpenClaw, Groq, dan Vision

**Hasil:** pesan WhatsApp nyata dapat diterima/dibalas oleh plugin; satu foto berizin dianalisis oleh Groq dan Web Detection secara nyata. Belum ada routing kejadian.

- [x] Siapkan environment Python lokal dan Git bila belum ada; abaikan environment, credential, media, database dump, sesi OpenClaw, dan log sensitif.
- [ ] Sesuaikan Node dengan persyaratan OpenClaw yang dipasang. Instal OpenClaw dan plugin WhatsApp resmi proyek OpenClaw, pin versi yang terbukti. Jangan mengganti OpenClaw dengan gateway lain jika integrasinya gagal.
- [ ] Pengguna memasangkan nomor khusus melalui QR. Awalnya allowlist hanya nomor tim. Buktikan teks, foto, video dan lokasi native diterima; output bot sendiri diabaikan.
- [ ] Buat plugin minimum yang mengambil alih dispatch sebelum agent biasa. Endpoint `POST /internal/whatsapp/events` menerima envelope; payload pengiriman berasal dari backend. Buktikan tidak ada balasan model kedua. Pada task ini endpoint cukup mode smoke dengan echo berlabel pengujian.
- [ ] Pengguna memilih Google Cloud project, menautkan billing, mengaktifkan Vision API, serta menyiapkan Application Default Credentials lokal. Buat batas persisten demo 50 request Web Detection total pada aplikasi, termasuk retry; cache satu hasil sukses per gambar/versi. Budget alert bukan hard cap biaya akun.
- [ ] Siapkan Groq key lokal. Uji model vision yang tercantum tersedia pada akun; pilih satu yang menghasilkan JSON schema-valid pada contoh api, tanpa api, dan gambar buram. Simpan model ID di environment, jangan hardcode klaim dukungan model yang belum diuji.
- [ ] Untuk video, ekstrak maksimal tiga frame pada awal/tengah/akhir setelah decode; observasi terbatas pada frame tersebut. Batas demo: foto <=10 MB; video <=20 MB dan <=30 detik. Berkas melampaui batas diminta ulang; tidak diabaikan diam-diam.

**Pemeriksaan:** smoke nyata pada nomor tim; simpan hasil provider yang telah diredaksi, ID/model/version dan waktu. Foto web yang diketahui harus memperlihatkan hasil asli Vision, walaupun provider tidak menemukan kecocokan. Ketiadaan kecocokan tidak boleh diganti fixture sukses. Kesalahan akun/transport adalah blocker task ini, bukan alasan mengklaim integrasi lulus.

**Dependensi pengguna:** login Google/billing, Groq key lokal, pairing WhatsApp. Pelaksana menyiapkan instruksi dan konfigurasi; tidak meminta secret dikirim lewat chat.

## Task 2 — Intake persisten dan percakapan kelengkapan

**Hasil:** satu laporan dapat dibangun dari beberapa pesan WhatsApp, selamat dari restart dan terisolasi dari pengirim lain.

- [ ] Buat skema awal PostgreSQL: inbound_events, reports, media, incidents, consent_events, jobs. SQL versi awal disimpan bersama backend; tidak menghapus data lama ketika start.
- [ ] `POST /internal/whatsapp/events` mengembalikan 202 setelah event/job committed. Constraint `(account_id, provider_message_id)` mengembalikan receipt sama untuk replay. Mutasi per percakapan diserialisasi; hasil AI dari revision lama tidak menimpa revisi baru.
- [ ] Ganti smoke echo dengan adapter produksi demo. Plugin menyimpan spool event/media secara atomik sebelum menyelesaikan takeover, lalu mengulang pengiriman ke backend sampai receipt diperoleh. Tidak menjanjikan recovery pesan yang belum diterima gateway.
- [ ] Implementasikan satu draft aktif per pengirim. REPORT baru ketika draft aktif meminta pilihan eksplisit; TRACK dibaca terpisah. Periksa media decode, koordinat finite/range-valid, keterangan kejadian dan konfirmasi titik. Consent berbagi kontak terpisah, default tidak diberikan.
- [ ] Simpan file di root privat dengan ID generated server dan validasi MIME/decode; tolak path bebas, traversal dan URL media arbitrer. Batasi teks 4000 karakter. Jangan mengeksekusi instruksi dari caption/media.
- [ ] Worker persisten memakai job PostgreSQL dengan locking dan lease; restart mengambil ulang job yang belum selesai. Respons percakapan memakai outbox yang sama; tidak bergantung BackgroundTasks atau memori.

**Pemeriksaan:** `python -m unittest discover -s tests -v`; kasus tiga pesan menjadi satu report, replay tidak menambah job, dua warga tidak bertukar data, restart tidak menghilangkan draft, hasil AI revisi lama tidak menimpa revisi baru, consent ditolak tetap memungkinkan laporan tanpa nomor, berkas rusak tetap belum lengkap. Task 2 lolos setelah laporan lengkap nyata tersimpan, belum otomatis dipublikasi.

## Task 3 — Pemeriksaan bukti, insiden, dan distribusi terkontrol

**Hasil:** laporan lengkap menghasilkan bukti berprovenans dan keputusan yang dapat dijelaskan; aturan konflik/eskalasi berjalan pada tujuan uji.

- [ ] Tambah evidence_results, report_incident_matches, delivery_events dan audit_events. Fungsi `analyze_report(report_id, revision)` menyimpan observasi Groq, hasil Web Detection, hash SHA-256, serta provenance snapshot FIRMS. JSON Groq divalidasi Pydantic; setiap fakta/ancaman menunjuk pesan atau media input yang benar-benar ada.
- [ ] Pisahkan hash internal, web match dan konsistensi isi/deskripsi/waktu/lokasi. EXIF kosong menjadi unavailable. Cache per hash dan versi pemeriksaan; perubahan media membuat revisi baru, tidak menghapus hasil lama.
- [ ] Terapkan aturan publikasi/eskalasi di bagian keputusan. Groq/Vision dicoba maksimal tiga kali total hanya untuk 429/5xx/timeout, dengan jeda 2 lalu 5 detik dan timeout 30 detik per request; kegagalan tetap unavailable. Kegagalan akses/billing langsung terlihat. Batas request gambar Task 1 mencakup percobaan ulang.
- [ ] FIRMS snapshot memakai sensor, acquisition time, fetched time dan sumber. Parameter eksperimen pencocokan: 3 km dan selisih pengamatan maksimal 24 jam. Tampilkan sebagai pencocokan data tersimpan; snapshot terlalu tua menghasilkan unavailable, bukan no_match. Radius ini terpisah dari GPS form.
- [ ] Cari kandidat incident dengan radius eksperimen 500 m dan selisih waktu 6 jam; AI memberi alasan kemiripan. Pengelompokan kandidat memerlukan konfirmasi operator lokal; tidak auto-merge dua kejadian hanya karena dekat. Jika tidak ada kandidat, buat incident baru. Simpan seluruh report dan audit koreksi. Link kanonik memakai slug acak 128-bit per incident.
- [ ] Tujuan berasal dari konfigurasi satu wilayah pilot dengan batas GeoJSON dan kode wilayah yang diverifikasi tim; gunakan Shapely untuk pemeriksaan titik. Titik di luar/ambigu tidak diarahkan dengan tebakan. Nomor/kanal semuanya allowlist tujuan uji. Jika channel tidak terbukti berfungsi, gunakan kontak koordinator uji dengan payload publik yang sama.
- [ ] Publikasi mengirim payload teredaksi dan link; nomor hanya boleh ke otoritas uji jika consent aktif. Tidak forward teks mentah. Delivery unik menurut incident/revision/tujuan/jenis payload; update bukti baru ditandai pembaruan, bukan laporan awal berulang.
- [ ] Kiriman sukses memerlukan hasil tool/provider yang valid. Timeout setelah request kirim menjadi unknown, bukan retry buta. Operator lokal dapat memeriksa hasil dan menjadwalkan retry; tujuan yang sudah sukses tidak diulang. Hold ditampilkan jujur dan tidak mempunyai timer penerusan otomatis.

**Pemeriksaan:** uji terisolasi dengan respons provider tercatat/fixtures, lalu smoke provider nyata. Konflik menahan publik; ancaman tinggi eskalasi berlabel; 429/JSON invalid tidak menjadi lolos; no_match tidak menjadi authentic; FIRMS mati tidak disebut tidak ada hotspot; dua report satu insiden tidak menggandakan kiriman; salah merge dapat dikoreksi; HTTP 200 tanpa receipt kirim tidak menjadi forwarded.

## Task 4 — Form GPS publik, agregasi konfirmasi, dan TRACK

**Hasil:** pemegang link dapat mengirim konfirmasi dari ponsel; TRACK menyampaikan hasil dengan atribusi yang benar.

- [ ] Jalankan aplikasi publik terpisah dari aplikasi internal/operator, tetapi memakai modul dan DB yang sama. Expose hanya aplikasi publik melalui HTTPS Cloudflare Tunnel; gateway OpenClaw, dokumentasi API internal dan token operator tetap lokal.
- [ ] `GET /laporan/{slug_id}` menampilkan overview teredaksi. Gunakan HTML template sederhana, JavaScript Geolocation API dan upload multipart; tidak perlu SPA. Foto publik berupa turunan yang disetujui operator setelah pemeriksaan data sensitif; asli tetap privat. Tanpa foto aman, tampilkan placeholder beralasan.
- [ ] `POST /api/laporan/{slug_id}/verifications` menerima choice, latitude, longitude, accuracy_m, gps_fix_at, description, photo opsional, solved dan request_id. Verifikasi slug dan insiden di server; radius dihitung dari titik kejadian, bukan centroid yang berubah setelah merge. Titik kejadian yang dikoreksi memakai revisi dan waktu yang tercatat.
- [ ] Terapkan batas GPS yang disepakati dan validasi finite/range. >2000 m mengembalikan 422 OUT_OF_RADIUS; error lokasi lain memakai kode INVALID_LOCATION, STALE_LOCATION atau INACCURATE_LOCATION. Tidak ada verification_event untuk kegagalan teknis.
- [ ] Choice invalid menormalkan solved=false pada server; UI menyembunyikan checkbox. Foto/deskripsi opsional untuk kedua pilihan. Request ID menghindari replay submit jaringan; bukan identitas unik seseorang. Tidak meminta nama/nomor wajib.
- [ ] Agregasi dari event yang tersimpan: none/supporting_valid/supporting_invalid/disputed dan claimed_solved bila ada event valid+solved. Klaim selesai tidak menutup insiden otomatis atau menghilangkan konflik. TRACK tanpa ID memilih report milik pengirim; ID pengirim lain dan ID tidak ada memberi jawaban aman yang sama.
- [ ] Batasi submit publik 10 upaya/10 menit per IP+slug melalui counter database; batas ini kontrol demo, bukan bukti orang unik. Deskripsi <=2000 karakter, foto <=10 MB, body dibatasi. Jangan tampilkan GPS pengisi ke publik; file publik tidak membocorkan GPS EXIF.

**Pemeriksaan:** 1999/2000/2001 m; accuracy 100/101 m; usia 60/61 detik; timestamp masa depan; NaN; izin ditolak; invalid+solved; replay; konflik; TRACK lintas pengirim; payload publik tanpa kontak, GPS pengisi, EXIF lokasi atau akses ke media privat. Smoke ponsel HTTPS memakai insiden simulasi aman. GPS asli dalam radius dapat diterima; koordinat sintetis hanya untuk test dan diberi label test, bukan dicatat sebagai verifikasi lapangan asli.

## Task 5 — Latihan demo, pemeriksaan akhir, dan handoff

**Hasil:** demo dapat dijalankan ulang dengan panduan singkat, bukti pengujian dan batasan yang jelas.

- [ ] Jalankan seluruh suite unit/integrasi dan rehearsal berurutan: laporan lengkap; media kurang; foto reuse web; konflik+ancaman; provider unavailable; laporan berulang; form valid/invalid; GPS ditolak; solved; TRACK; restart dan delivery gagal. Gunakan fixture untuk memaksa failure path, provider asli untuk membuktikan koneksi nyata.
- [ ] Periksa lima risiko lintas task: pesan terlambat/duplikat, salah kepemilikan, stale AI revision, timeout kirim dengan hasil ambigu, serta kebocoran kontak/media/GPS. Masing-masing harus mempunyai pemeriksaan di task pemiliknya, bukan hanya checklist manual.
- [ ] Halaman operator lokal menampilkan report/incident, bukti dan alasan, hold, tujuan sukses/gagal/unknown, kontribusi serta klaim selesai. Tambahkan readiness untuk DB/gateway dan status provider terakhir; tidak memakai angka keberhasilan statis.
- [ ] Tetapkan retensi demo tujuh hari untuk input/media/GPS/spool/log sensitif; sediakan perintah purge lokal teruji yang menghapus data terkait tanpa menyentuh konfigurasi/credential. Jangan otomatis purge saat proses start. Data demo tidak menjadi dataset training tanpa persetujuan.
- [ ] Dokumentasikan setup, environment, startup/shutdown, pairing ulang, pemeriksaan credential, pemulihan spool/job, retry unknown dan reset data simulasi. Satu daftar perintah harus dapat membawa operator dari checkout ke demo, tanpa secret di dokumen.
- [ ] Rekam skenario pendek dan simpan hasil pemeriksaan. Bedakan analisis nyata, FIRMS snapshot, data insiden simulasi dan injected failure. Jangan mengklaim autentikasi MPA, koordinat bebas spoofing, penutupan resmi BPBD, atau akurasi AI dari voting publik.

**Pemeriksaan akhir:** `python -m unittest discover -s tests -v`, build/typecheck plugin sesuai package script, lalu satu rehearsal WhatsApp sampai TRACK dari ponsel. Semua outcome harus cocok dengan data tersimpan. Lulus unit test saja tidak membuktikan integrasi WhatsApp/Groq/Vision.

## Urutan eksekusi dan handoff

Task **1 → 2 → 3 → 4 → 5**, tanpa implementasi paralel. Tiap task berakhir dengan ringkasan perubahan, perintah/hasil uji, blocker aktual, dan commit lokal bila Git tersedia. Jangan membuat commit yang mencakup credential atau data runtime.

Alokasi target: hari pertama Task 1–2; hari kedua Task 3; hari ketiga Task 4–5. Ini alokasi kerja, bukan jaminan. Jika integrasi provider/gateway belum lolos Task 1, selesaikan kendala itu sebelum mengklaim demo nyata; jangan menyamarkan kegagalan sebagai simulasi sukses.

Pilihan akun/project, credential, pairing, dataset wilayah, kontak uji dan foto berizin adalah input setup yang harus diberikan/diverifikasi sebelum task yang memakainya. Ini bukan keputusan arsitektur yang boleh ditebak pelaksana. Tidak ada instalasi atau aktivasi berbayar yang dinyatakan sudah selesai oleh rencana ini.
