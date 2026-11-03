# Audit kesesuaian Knowledge v3 — 24 Oktober 2026

Status: audit dokumen dan implementasi Task 1–3; ketiga klarifikasi bisnis sudah dijawab pengguna pada 24 Oktober 2026. Tidak ada pemberitahuan atau persetujuan khusus pemrosesan laporan/AI untuk demo; izin berbagi kontak tetap terpisah dan opsional. Dokumen ini mencatat kondisi aktual, bukan menyatakan semua fitur Knowledge v3 telah selesai atau mengubah kebijakan runtime.

## Acuan dan urutan keputusan

File pengguna `C:\Users\shafw\Downloads\Knowledge_Doc_Terbaru_DeveloperDay_Karhutla_2026.md` identik byte demi byte dengan [salinan proyek](../Knowledge_Doc_Terbaru_DeveloperDay_Karhutla_2026.md). SHA-256 keduanya: `E112EE09ABD1D3A89A2F1AA4F69E2360D19B51AC304037A7FA2F53DD4534B0E7`. Dokumen berjudul Knowledge v3 dan bertanggal 22 Oktober 2026; audit ini bertanggal 24 Oktober 2026.

Ketentuan `[FIX]` menjadi acuan produk. Bagian `[REKOMENDASI]`/`[RISET]` tetap dibedakan dari keputusan yang sudah disetujui. Keputusan pengguna dalam percakapan memperinci demo: Kota Malang, dua kontak uji, eskalasi ancaman tinggi berlabel, FIRMS unavailable menahan komunitas, tanpa timer penerusan otomatis. Itu tidak berarti tim atau BPBD telah menyetujui SOP operasional.

Parameter FIRMS 3 km/24 jam, kandidat insiden 500 meter/enam jam, GPS form accuracy 100 meter/usia 60 detik, dan batas klarifikasi adalah parameter demo yang telah dipilih pada rencana sebelumnya. Knowledge menetapkan radius form 2 km sebagai keputusan MVP; parameter lain tidak boleh disebut batas ilmiah atau ketentuan bisnis final. Pacing Groq 35 detik adalah pengaturan teknis provider, bukan radius atau skor validasi bisnis.

### Amendemen pengguna — 24 Oktober 2026

- **Lokasi:** “Teks hanya untuk klarifikasi; pelapor tetap wajib mengirim pin/koordinat.” Untuk demo, alamat/nama tempat tidak menggantikan titik kejadian terkonfirmasi. Geocoding alamat bukan syarat implementasi. Ketentuan ini memperinci §4.1 langkah 2–3.
- **Metadata:** EXIF tidak wajib karena dapat hilang dalam pengiriman WhatsApp. Bila tersedia, gunakan sebagai bukti tambahan; bila tidak tersedia, catat unavailable/unknown. Ketiadaan EXIF saja tidak menahan laporan dan tidak membuktikan media konsisten, asli, atau palsu. Ini tidak menghapus kebutuhan membandingkan isi media, caption, klaim lokasi/waktu, serta bukti lain yang tersedia.
- **Pemrosesan:** setelah penjelasan tentang penyimpanan laporan dan pengiriman teks/media ke Groq serta layanan pencarian gambar, pengguna memilih “tidak usah ada pemberitahuan dan persetujuan”. Untuk demo, tidak ditambahkan pemberitahuan atau gerbang persetujuan khusus sebelum pemrosesan/analisis. Ini memperbarui §4.1 langkah 2 untuk pemrosesan laporan; bukan pencatatan consent implisit, dan bukan penghapusan izin berbagi nomor. Izin berbagi kontak tetap eksplisit, opsional, dan default tidak diberikan.

Salinan Knowledge sumber dipertahankan tanpa perubahan; amendemen percakapan dicatat di sini agar asal dokumen dan keputusan tambahan tetap dapat ditelusuri.

## Pisahkan dua jenis pemeriksaan

1. **Pemeriksaan awal laporan:** kelengkapan, konfirmasi titik, observasi media, kemiripan lokal/web, konsistensi bukti, FIRMS, kandidat insiden, dan aturan distribusi. Keputusan awal tidak membuktikan kejadian autentik.
2. **Konfirmasi publik setelah distribusi:** kontribusi pemegang link `/laporan/{slug_id}` yang mengirim GPS browser dalam radius 2 km. Pengisi tidak otomatis MPA terautentikasi. Kontribusi dan solved adalah evidensi/klaim tambahan, bukan final truth atau penutupan resmi.

Tidak ada syarat menunggu konfirmasi publik sebelum laporan dapat disalurkan. Penahanan karena bukti awal tidak cukup berbeda dari menunggu pengisi form publik.

## Matriks kesesuaian

| Ketentuan Knowledge | Status kode saat audit | Bukti implementasi / pekerjaan tersisa |
| --- | --- | --- |
| Media awal wajib, lokasi dan keterangan minimum (§4.1) | Sesuai untuk media, pin, dan keterangan | `backend/conversation.py`, `backend/worker.py`: media harus dapat dibuka; pin dikonfirmasi; keterangan dapat diekstrak dari bahasa alami lewat `analysis_store.py`. |
| Lokasi teks digali sampai cukup spesifik (§4.1), diperinci amendemen 24 Oktober | Sesuai kebijakan demo yang dikonfirmasi | Teks membantu klarifikasi; pelapor tetap wajib mengirim pin/koordinat dan mengonfirmasi titik kejadian. `backend/internal.py` menerima lokasi terstruktur dan plugin menerima native location. Nama tempat sebagai keterangan belum melengkapi lokasi; geocoding tidak diwajibkan. |
| Pemrosesan laporan dan izin berbagi kontak (§4.1), diperbarui amendemen 24 Oktober | Sesuai kebijakan demo yang dikonfirmasi | `store.accept`, upload/spool, dan antrean analisis tidak menunggu consent pemrosesan/AI khusus. Pengguna memilih tanpa pemberitahuan dan persetujuan pemrosesan. `consent_contact` dan `consent_events` tetap mengatur izin eksplisit berbagi nomor; default tidak diberikan. |
| Fakta AI bersumber, klasifikasi dan waktu (§4.1, §10) | Sesuai sebagai ekstraksi klaim | `backend/facts.py` memvalidasi ID dan kutipan sumber; waktu ambigu tidak ditebak. Fakta yang dikutip tetap klaim pelapor, bukan bukti benar. |
| Kemiripan media lokal dan web terpisah (§10) | Sesuai | Fingerprint laporan diperiksa terpisah dari indeks smoke; SerpApi utama, Vision opt-in. Fallback tidak mengganti hasil konflik. `no_match` tidak menjadi authentic. |
| Konsistensi isi/caption/lokasi/waktu sebagai hasil tersendiri (§4.1, §10) | Belum lengkap | `analysis_engine.py` mengumpulkan observasi api/asap, waktu klaim, tanggal EXIF bila ada, serta boolean GPS tersedia. Belum ada hasil khusus konsistensi yang membandingkan sumber yang tersedia. `decisions.py` tidak menerima hasil pemeriksaan konsistensi tersebut. Foto hutan dan pin perkotaan saja tidak membuktikan konflik. EXIF opsional tidak menghapus kekurangan implementasi pemeriksaan lintas sumber ini. |
| EXIF kosong unavailable, bukan invalid (§10), dikonfirmasi 24 Oktober | Sesuai | `analysis_engine.py` menyimpan `NO_EXIF`; EXIF tidak wajib dan ketiadaannya saja tidak menjadi alasan hold. Metadata yang tersedia hanya bukti tambahan, bukan bukti autentik. Unknown tidak dianggap consistent. |
| FIRMS hanya sinyal pendukung (§2, §4.1) | Sesuai | `backend/geospatial.py`: matched/no_match/unavailable dibedakan; sumber, waktu, cakupan dan usia diperiksa. Tidak ada hotspot tidak melabeli laporan palsu. |
| Tingkat kepercayaan AI (§4.1, §5) | Implementasi memakai alasan keputusan | `backend/decisions.py` menghasilkan eligible/held, kode alasan dan referensi bukti. Tidak ada persentase confidence. Ini sesuai keputusan demo sebelumnya untuk menghindari angka seolah terkalibrasi; skor riset dapat ditambahkan terpisah bila dibutuhkan tim. |
| Duplikasi dekat bukan auto-merge (§11) | Sesuai pada desain/aturan | Kandidat 500 meter/enam jam, AI memberi saran, operator mengonfirmasi melalui CLI. Laporan sumber dan audit tetap terpisah. Ada keterbatasan kandidat insiden kosong bekas merge yang sudah dicatat di panduan Task 3. |
| Saluran komunitas dan kontak otoritas dipisah (§3, §8) | Sesuai untuk demo kontak uji | `Task3Config`, `decisions.py`, dan outbox membedakan community/authority. Distribusi tetap nonaktif saat kontak/batas belum disiapkan; keberhasilan kanal WhatsApp publik belum dibuktikan. |
| Eskalasi ancaman tinggi walau bukti belum selesai (§8, rekomendasi) | Telah dipilih pengguna untuk demo | Ada fast escalation berlabel BELUM TERVERIFIKASI setelah minimum lengkap dan titik terkonfirmasi dalam wilayah. Kebijakan ini bukan persetujuan operasional BPBD. |
| Panduan keselamatan saat belum lengkap/darurat (§8, §12 skenario 3) | Belum tersedia | Balasan saat ini meminta data atau memberi status; belum ada arahan menjaga jarak aman/tidak mendekati api dan menghubungi layanan darurat secara langsung. Jangan menebak nomor layanan; nomor lokal perlu sumber/setup yang benar jika akan dicantumkan. |
| Identitas tidak masuk saluran; kontak hanya dengan consent (§3) | Sesuai pada payload | Kartu tidak meneruskan teks mentah/media asli/identitas. Nomor hanya ditambahkan ke kartu authority saat send admission bila consent masih aktif. Revisi, tujuan, keputusan dan consent diperiksa ulang. |
| Status penerimaan, pemeriksaan, pengiriman berbeda (§5, §7) | Sesuai sebagai fondasi | Status draft/complete dan keputusan held/eligible terpisah dari outbox pending/sent/unknown. `STATUS` membaca kondisi tersimpan; belum sama dengan fitur `TRACK` penuh. |
| Link `/laporan/{slug_id}` (§3–4) | Fondasi slug saja; Task 4 | Slug 128-bit ada, route publik belum ada. Kartu belum mencantumkan link agar tidak membagikan tautan rusak. Ini penundaan tahap, bukan penghapusan ketentuan bisnis. |
| Form publik GPS server-side <=2 km; valid/invalid; foto/deskripsi opsional (§3–6) | Belum diimplementasikan; Task 4 | Belum ada aplikasi publik atau `verification_events`. Tidak ada fitur yang saat ini boleh diklaim telah memvalidasi GPS form. |
| Invalid bukan gagal syarat GPS; solved hanya pada valid (§4–7) | Ketentuan Task 4, belum dapat diverifikasi di kode | Submit teknis gagal tidak boleh membuat event invalid. Solved harus dinormalisasi server-side dan disimpan sebagai klaim publik. |
| Banyak kontribusi, konflik, atribusi solved, TRACK milik pengirim (§3–9) | Belum diimplementasikan; Task 4 | `TRACK` saat ini memberi balasan belum tersedia. Agregasi tidak boleh memakai suara publik sebagai ground truth independen. |
| Tanpa pengisi link alur utama tetap berjalan (§3, §12) | Sesuai untuk alur yang sudah ada | Tidak ada dependency publik di syarat pemeriksaan/distribusi awal. Ketentuan ini harus dipertahankan saat Task 4 ditambahkan. |
| Dashboard ringkas dan retensi data (§9, §14) | Sebagian / Task 5 | CLI inspeksi dan audit tersedia; dashboard dan purge/retensi belum diimplementasikan. Tidak ada klaim produksi/nasional/mitra resmi. |

## Status klarifikasi

- **Q1 — pemrosesan, selesai:** pengguna memilih tanpa pemberitahuan atau persetujuan khusus pemrosesan laporan/AI setelah penjelasan cakupannya. Tidak menambahkan gerbang analisis dan tidak menyimpan pilihan ini sebagai consent warga. Izin berbagi nomor ke otoritas tetap terpisah dan opsional.
- **Q2 — alamat teks, selesai:** teks hanya untuk klarifikasi; pin/koordinat tetap wajib. Tidak perlu ekstraksi kandidat koordinat/geocoding untuk memenuhi demo.
- **Q3 — EXIF, selesai:** tidak wajib tersedia; ketiadaannya tidak otomatis memblokir. Bukti yang tidak tersedia tetap unknown/unavailable, bukan consistent/authentic. Pemeriksaan konsistensi sumber lain tetap perlu diimplementasikan.

Keputusan Q1/Q2/Q3 di atas menggantikan opsi rekomendasi sebelumnya. Tidak ada klarifikasi dari audit ini yang masih menunggu jawaban.

## Verifikasi audit

Pada 24 Oktober 2026, `python -m unittest tests.test_task3_rules tests.test_web_evidence tests.test_conversation -q` lulus **30 tes**. Cakupannya antara lain kelengkapan, konfirmasi pin, consent kontak, kutipan sumber, koreksi waktu, negasi ancaman, kebijakan hold/eskalasi, FIRMS usang, dan no-match/fallback web.

Audit fitur yang belum ada menggunakan pembacaan endpoint, skema, state percakapan dan pemanggil keputusan, bukan asumsi dari nama fitur. Kelulusan tes tersebut tidak membuktikan pemeriksaan konsistensi lintas sumber, form GPS, atau TRACK telah tersedia. Gerbang consent pemrosesan dan geocoding bukan syarat demo sesuai jawaban Q1/Q2. Pencatatan keputusan Q1/Q2/Q3 hanya mengubah dokumentasi; tidak mengubah kode/runtime. Gate WhatsApp Task 3 tetap belum dinyatakan lulus.
