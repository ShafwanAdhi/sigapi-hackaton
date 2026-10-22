# KNOWLEDGE DOCUMENT v3 — Bot WhatsApp Pelaporan Karhutla
**Proyek .id DeveloperDay 2026 | Dokumen kerja tim | 22 Oktober 2026**

> **Status:** Draft konsolidasi diskusi tim. Menggantikan keputusan terkait verifikasi MPA dan progres pada v2, tetapi tetap mewarisi alur pelaporan utama v2 kecuali dinyatakan berbeda. **[FIX]** = arahan pengguna/keputusan terbaru; **[REKOMENDASI]** = saran desain belum disetujui; **[RISET]** = harus diuji/ditentukan. Dokumen ini tidak menyatakan bahwa implementasi sudah berhasil.

## 1. Executive summary
Produk adalah bot WhatsApp untuk pelaporan kebakaran hutan/lahan dan, sesuai klasifikasi kejadian, kebakaran lain. Warga mengirim foto/video wajib, lokasi, dan informasi kejadian. AI melengkapi informasi, memeriksa media dan konsistensi lokasi, mencocokkan data pendukung (termasuk NASA FIRMS), mendeteksi duplikat, lalu merutekan laporan sesuai wilayah/tingkat kepercayaan menuju saluran informasi MPA dan kontak BPBD/damkar yang dikonfigurasi. Fitur TRACK memungkinkan pelapor menanyakan kondisi laporannya.

**Perubahan utama v3:** kartu laporan di saluran menyertakan tautan unik `/laporan/{slug_id}` menuju form verifikasi publik berbasis lokasi. Siapa saja yang mendapat link dapat membuka dan mengisi, tetapi **form tidak boleh tersubmit tanpa persetujuan GPS dan jarak terhitung <= 2 km dari titik kejadian** (parameter awal untuk pilot, bukan batas ilmiah final). Pengisi memilih **valid / tidak valid** tentang kebenaran kejadian, dapat menambahkan deskripsi opsional dan foto opsional, serta **checkbox opsional 'kebakaran sudah tertangani' hanya jika memilih valid**. Tidak ada sistem update progres berulang. Hasil verifikasi disimpan sebagai evidensi/analitik dan sumber informasi bagi TRACK; tidak menjadi syarat atau penghambat alur utama pelaporan.

**Batasan penting:** publik dapat membuka link, jadi pengisi tidak otomatis terautentikasi sebagai MPA, sekalipun link terdapat di saluran MPA. Istilah tepat adalah *verifikasi berbasis kedekatan lokasi oleh pemegang link*, bukan verifikasi petugas terotentikasi. Klaim bahwa GPS membuktikan keaslian tidak boleh dipakai.

## 2. Masalah dan proposisi nilai
- Laporan warga sering tidak terstruktur, lokasi tidak spesifik, dan rawan duplikasi/informasi palsu.
- Satelit menyediakan sinyal pendukung, bukan kepastian api di lapangan; ketiadaan hotspot bukan bukti tidak terjadi kebakaran.
- Kanal informasi dan pemberitahuan resmi perlu menerima laporan terstruktur dan ditujukan ke wilayah relevan.
- Sesudah laporan disalurkan, data konfirmasi kondisi lapangan masih minim. Form link membantu mengumpulkan konfirmasi **opsional** tanpa menjadikan MPA petugas wajib atau sistem pelacakan operasi BPBD.
- Proposisi nilai yang harus diuji: percepatan kelengkapan dan penyaluran laporan, pengurangan duplikasi, dan tersedianya evidensi konfirmasi lokasi untuk analitik serta jawaban TRACK.

## 3. Daftar keputusan terbaru (ground truth diskusi)
| Area | Status | Ketentuan |
|---|---|---|
| Path link | [FIX] | Setiap laporan/insiden memiliki route `/laporan/{slug_id}`; slug acak boleh digunakan. |
| Akses link | [FIX] | Publik: siapa pun yang memperoleh tautan dapat membuka/mengisi, tanpa verifikasi keanggotaan MPA. |
| Syarat kirim verifikasi | [FIX] | Browser harus memberikan lokasi; server mengecek radius maksimal **2 km** dari titik kebakaran. Di luar radius, kirim ditolak dengan feedback. |
| Batas 2 km | [FIX untuk MVP] | Angka awal yang akan divalidasi pada skenario lapangan; sebelumnya dipertimbangkan 1 km. |
| Pilihan kebenaran | [FIX] | `valid` dan `tidak valid`, untuk analitik hasil verifikasi. |
| Checkbox selesai | [FIX] | Opsional dan **hanya muncul jika memilih valid**. Tidak ada status 'belum tertangani' yang wajib. |
| Update progres | [FIX] | Tidak ada siklus update progres. Hanya data verifikasi dan flag sudah tertangani/solved saat dikonfirmasi. |
| Deskripsi | [FIX] | Input keterangan/deskripsi opsional. |
| Bukti lapangan | [FIX] | Foto bukti opsional untuk valid maupun tidak valid. |
| Verifikasi ganda | [FIX] | Banyak orang bisa mengisi pada insiden yang sama; catat kontribusi masing-masing. |
| Tanpa verifikasi | [FIX] | Tidak ada efek yang menghentikan alur utama; laporan bisa terus ada tanpa konfirmasi. |
| Status TRACK | [FIX] | Gunakan bukti verifikasi dan penyelesaian bila tersedia; jangan mengklaim status penanganan tanpa data. |
| Duplikasi laporan | [FIX] | AI membantu mengidentifikasi kemiripan waktu/lokasi/peristiwa dan mengelompokkan laporan yang sama. |
| BPBD | [FIX] | Laporan juga ditujukan ke nomor WhatsApp BPBD atau otoritas yang dikonfigurasi; MPA adalah sukarelawan. |
| Privasi | [FIX] | Nomor dan identitas pelapor tidak masuk saluran; kontak dapat diteruskan ke otoritas sesuai persetujuan dan disimpan di basis data. |
| Anti-duplikasi media | [FIX niat] | Tim berniat menggunakan pencocokan gambar web serta analisis caption/metadata terkait waktu dan lokasi. Implementasi dan kemampuan nyata perlu diuji. |
| Teknologi demo | [FIX pilihan] | OpenClaw + Baileys dianggap cukup untuk prototipe lomba; risiko gateway tidak resmi tetap dicatat. |
| Pilot | [FIX] | Fokus percontohan satu wilayah; ekspansi nasional adalah visi, bukan klaim implementasi. |
| Kerja sama | [FIX saat ini] | Belum ada mitra resmi MPA/BPBD untuk paper/video awal; demo harus dinyatakan simulasi bila relevan. |

## 4. Alur pengguna
### 4.1 Warga (alur utama; diwarisi dari v2)
1. Warga menghubungi satu nomor WhatsApp bot.
2. Bot meminta persetujuan pemrosesan data/kontak; meminta foto/video **wajib**, lokasi shareloc atau teks, dan keterangan minimum.
3. Lokasi teks digali sampai cukup spesifik; shareloc dibedakan apakah titik api atau posisi pelapor.
4. AI mengklasifikasikan peristiwa, mengecek media/lokasi, mencari kemiripan dengan laporan lain, mencocokkan sinyal NASA FIRMS, dan menghitung kepercayaan.
5. Laporan dikelompokkan ke insiden, ditentukan wilayahnya, kemudian disalurkan atau masuk antrean verifikasi berdasarkan kebijakan routing yang **masih memerlukan keputusan keselamatan** (lihat §8).
6. Kartu saluran mencantumkan overview, titik lokasi, dan link `/laporan/{slug_id}`; nomor pelapor tidak ditampilkan.
7. Otoritas setempat (BPBD/damkar sesuai konfigurasi) menerima informasi melalui WhatsApp, terpisah dari saluran publik.
8. Pengguna dapat mengirim perintah TRACK untuk membaca status penerimaan/penyaluran dan **hasil verifikasi/solved jika tersedia**.

### 4.2 Pengisi link (fitur sampingan)
1. Pemegang link membuka halaman overview insiden dengan tanggal, lokasi, foto laporan sesuai pembatasan privasi, dan status solved bila tersedia.
2. Halaman meminta izin akses lokasi perangkat melalui HTTPS.
3. Pengisi memilih `valid` atau `tidak valid` tentang kejadian (bukan tentang hasil pengecekan jarak).
4. Bila `valid`, form memunculkan checkbox `Kebakaran sudah tertangani/selesai` (tidak dicentang secara default). Bila `tidak valid`, checkbox disembunyikan dan nilainya diset null/false.
5. Pengisi dapat menambahkan deskripsi opsional dan foto opsional.
6. Saat Submit, server mengecek timestamp dan akurasi GPS, menghitung jarak pengisi ke titik kejadian, lalu **menolak** verifikasi bila lokasi tidak diizinkan, gagal terbaca, usang, atau jarak >2 km.
7. Bila lolos, simpan satu `verification_event`. Jangan menulis ulang klaim 'kebakaran valid' sebagai fakta final hanya karena satu formulir publik masuk.
8. Jika ada pernyataan solved, simpan klaim penyelesaian yang terlacak; tampilkan status secara hati-hati sesuai kebijakan agregasi (§7).

### 4.3 Umpan balik penting pada form
- `Jarak Anda sekitar 2,8 km dari titik laporan. Verifikasi tidak dapat dikirim karena batas pilot adalah 2 km.`
- `Lokasi perangkat belum diizinkan. Aktifkan izin lokasi untuk mengirim verifikasi.`
- `Akurasi lokasi belum memadai. Coba ambil ulang lokasi di area dengan penerimaan GPS lebih baik.`
- `Konfirmasi tersimpan. Terima kasih telah membantu.`
- `Kejadian ini telah ditandai selesai berdasarkan konfirmasi yang diterima.` **Jangan** tampilkan 'BPBD memastikan sudah padam' tanpa sumber resmi.

## 5. Definisi konsep agar tidak rancu
- **Report:** satu laporan warga/nomor, dapat menjadi bagian dari satu insiden bersama.
- **Incident:** kejadian kebakaran yang dikelompokkan dari satu atau beberapa report; punya `incident_id` dan link unik.
- **AI confidence:** estimasi sistem sebelum ada bukti konfirmasi tambahan; bukan label kebenaran absolut.
- **Verification event:** satu input publik berbasis GPS terhadap insiden dengan keputusan `valid` atau `invalid`.
- **Failed submission:** kegagalan syarat teknis (misalnya >2 km); **bukan** hasil `invalid` terhadap kejadian.
- **Solved claim:** checkbox pengisi bahwa kebakaran sudah selesai; **bukan** bukti penutupan resmi oleh BPBD.
- **Official response:** tindakan BPBD/damkar di luar cakupan pelacakan detail MVP.
- **TP/TN/FP/FN:** metrik klasifikasi memerlukan *ground truth independen*. Suara dari pemegang link tidak otomatis menjadi label ground truth.

## 6. Form, aturan UX, dan perlindungan dari ambiguitas
**Field:** ringkasan insiden (read-only), `verification_choice` [wajib: valid/invalid], `location` [wajib via browser], `description` [opsional], `photo` [opsional], `solved_checkbox` [opsional, hanya untuk valid].

**[REKOMENDASI]** Pengisi dapat melihat koordinat/perkiraan jarak setelah memberi izin; tombol Submit tampil tetapi disabled selama GPS belum siap; validasi jarak utama **tetap harus di server**. Jika GPS kurang akurat, beri kesempatan refresh, bukan mengubah jawaban valid menjadi invalid. Tidak perlu menawarkan manual override untuk publik pada versi lomba. Ini menjawab pertanyaan 'bagaimana verifikasi manual': mekanisme manual oleh admin tidak dibutuhkan di fitur publik; bila kelak diperlukan, pisahkan jalur admin yang diaudit, jangan menjadi pengecualian umum radius.

**[REKOMENDASI]** Jangan meminta nama/nomor wajib sekarang: itu bertentangan dengan akses terbuka yang dipilih dan menambah hambatan. Untuk mencegah klaim seolah diverifikasi MPA resmi, beri label `Konfirmasi pengguna di sekitar lokasi`, bukan `Verifikasi MPA terautentikasi`. Nama atau nomor opsional boleh jadi pengembangan setelah uji privasi/penyalahgunaan. Ketiadaan identitas membuat satu pengisi dapat mengirim lebih dari sekali dan hasil lebih rentan manipulasi.

**[RISET]** Browser `coords.accuracy` menunjukkan perkiraan tingkat akurasi GPS (meter), bukan bukti bebas spoofing. Uji threshold akurasi awal (contoh <= 100–200 m sebagai parameter pengujian, **bukan keputusan final**), batas usia fix lokasi (mis. <= 60 detik), dan bagaimana menangani sinyal buruk. Jangan menetapkan lokasi manual sebagai pengganti GPS wajib.

## 7. Model status dan aturan TRACK (rancangan ideal)
**Jangan satukan** status teknis laporan, status kebenaran, dan klaim penyelesaian:

| Dimensi | Nilai yang disarankan | Catatan |
|---|---|---|
| `delivery_status` | incomplete / held / forwarded / failed | Status sistem, bukan penanganan |
| `field_verification_summary` | none / supporting_valid / disputed / supporting_invalid | Hasil agregasi evidensi; tidak wajib |
| `solved_claim_status` | none / claimed_solved | Tidak menggunakan 'belum tertangani' sebagai input |
| `closure_status` | open / closed_claimed | `closed_claimed` perlu ditandai sebagai klaim publik kecuali ada konfirmasi otoritas |

**[REKOMENDASI]** Aturan MVP konservatif: satu `valid` dari pengisi publik hanya ditampilkan sebagai `ada konfirmasi valid berbasis lokasi`; satu `invalid` sebagai `ada konfirmasi tidak valid berbasis lokasi`; jika bertentangan tampilkan `konfirmasi lapangan berbeda`. Bila checkbox solved muncul, TRACK menampilkan `ada laporan bahwa kejadian telah selesai` + waktu, bukan `dipastikan selesai oleh BPBD`. Halaman link dapat menampilkan badge `Dilaporkan selesai` dengan sumber jelas. Pilihan alternatif **[RISET]**: angka minimal konfirmasi independen sebelum status solved diumumkan.

**Contoh TRACK:**
- Belum ada verifikasi: `Laporan Anda sudah diteruskan ke kanal tujuan. Belum ada konfirmasi kondisi lapangan pada sistem.`
- Ada validasi: `Laporan sudah diteruskan. Terdapat konfirmasi dari pengguna yang mengirim lokasi dalam radius pilot.`
- Konflik: `Laporan sudah diteruskan. Hasil konfirmasi lapangan berbeda-beda; belum ada kesimpulan.`
- Solved claim: `Laporan diteruskan; terdapat konfirmasi bahwa kebakaran telah selesai. Ini belum tentu merupakan konfirmasi resmi BPBD.`

## 8. Konflik paling penting: laporan palsu vs laporan darurat nyata
**Konteks keputusan:** tim ingin menjaga saluran tetap tepercaya di tengah potensi spam dan laporan terkoordinasi, tetapi penahanan semua laporan berisiko membuat kebakaran nyata terlambat diteruskan. **Tidak tepat memilih hanya salah satu tujuan secara mutlak.**

**[REKOMENDASI – belum disetujui tim]** Gunakan dua jalur yang berbeda:
- **Saluran informasi MPA (publik/komunitas):** hanya tampilkan laporan dengan bukti cukup kuat dan konsistensi minimum agar tidak dipenuhi informasi meragukan.
- **BPBD/damkar (otoritas):** lakukan eskalasi **terbatas** atas laporan berisiko tinggi walau confidence belum tinggi, dengan label **BELUM TERVERIFIKASI** dan indikator alasannya; bukan mempublikasikannya sebagai fakta. Hindari membanjiri otoritas: deduplikasi, rate-limit, prioritas, dan ringkasan berbasis insiden.
- **Low-risk, low-confidence:** masuk hold, minta bukti tambahan, beri nomor darurat kepada warga. Tetapkan SLA hold dan eskalasi manual bila perlu.
- **Risiko jiwa/permukiman:** anjurkan pelapor menghubungi layanan darurat secara langsung; bot tidak boleh menjadi satu-satunya jalur darurat.

**Alasan:** reputasi saluran dan keselamatan dapat dijaga dengan membedakan **siapa penerima** dan **bagaimana ketidakpastian diberi label**, bukan memberi skor tunggal yang memutus semua jalur. Ini kebijakan desain yang wajib dibahas dan diuji bersama calon pengguna, bukan SOP yang telah disetujui BPBD.

### 8.1 Saat AI dan verifikator lapangan berbeda
**[REKOMENDASI]** Pertahankan bukti mentah keduanya. Prediksi AI tidak boleh menghapus verifikasi lapangan; satu pengisi publik juga tidak boleh membatalkan AI atau laporan warga secara final. Agregasi mempertimbangkan: jarak & akurasi GPS, jumlah konfirmasi unik yang wajar, konsistensi waktu, bukti foto, kedekatan laporan warga lain, dan kecocokan FIRMS sebagai sinyal pendukung. Karena pengisi anonim, verifikasi publik **tidak layak diberikan otoritas penuh**. Bila ada konflik, tampilkan `disputed` dan arahkan ke pemeriksaan resmi bila berisiko tinggi.

## 9. Rekomendasi teknis dan skema data
### 9.1 Entitas minimum
- `reports`: report_id, incident_id, wa_sender_ref, consent_contact, media_refs, reported_fire_point, reporter_point_if_different, description, created_at, confidence, delivery_status.
- `incidents`: incident_id, public_slug_random, centroid_or_fire_point, category, first_seen_at, routing_region, field_summary, solved_claim_status.
- `verification_events`: verification_id, incident_id, choice_valid_invalid, latitude, longitude, accuracy_m, gps_fix_at, server_received_at, distance_m, description, optional_image_ref, solved_checked, source='public_link'.
- `delivery_events`: incident_id, destination_type/channel, destination_ref, delivered_at, delivery_result, retry_count.
- `report_incident_matches`: report_id, incident_id, match_score, distance_m, time_delta, model_version, reviewed_flag.
- `audit_events`: actor/source, action, timestamp, subject_id, outcome. Jangan simpan koordinat presisi selamanya tanpa alasan retensi.

### 9.2 Endpoint ilustratif (bukan kontrak API final)
- `GET /laporan/{slug_id}`: ringkasan publik teredaksi dan status yang sesuai.
- `POST /api/incidents/{id}/verifications`: menyimpan satu verifikasi setelah pemeriksaan GPS server-side; id internal tidak boleh menambah hak akses.
- `GET /api/track/{report_id}`: autentikasi memakai relasi dengan nomor pengirim WhatsApp, bukan URL publik.

**Pseudologic submit:** verifikasi slug & insiden -> validasi field -> lokasi izin aktif -> timestamp masih baru -> accuracy memenuhi threshold -> hitung jarak geodesik -> jika `distance > 2000m`: HTTP 422 (`OUT_OF_RADIUS`) -> jika `invalid`: `solved=false` -> simpan event -> update agregat konservatif -> balas hasil.

**[REKOMENDASI]** Jangan gunakan koordinat dari client sebagai jaminan keaslian; pengecekan ulang Haversine di server hanya memverifikasi konsistensi angka yang dikirim, tidak membuktikan perangkat benar-benar ada di sana. Penggunaan GPS palsu dan forwarding link tetap residual risk yang diterima sementara untuk pilot.

## 10. Pemeriksaan media dan metadata
**[FIX niat tim]** Pencocokan gambar internet, caption, dan metadata dipakai sebagai sinyal kualitas/duplikasi. **[BATAS TEKNIS]** Media WhatsApp bisa dikompresi dan metadata EXIF (termasuk waktu/GPS) sering tidak tersedia. Caption ditulis manusia sehingga bisa menyesatkan. Pencocokan gambar web dapat menemukan penggunaan ulang yang tersedia di internet, tetapi tidak menjamin foto baru asli, waktu baru, lokasi benar, ataupun deteksi semua gambar AI.

**[REKOMENDASI]** Laporkan tiga hasil terpisah: `(a) kemiripan media dalam database`, `(b) kemunculan mirip pada web jika layanan tersedia`, `(c) konsistensi isi/caption/lokasi/waktu`. Jangan memberi status `authentic` hanya karena web search nihil atau metadata kosong. Tandai atribut media `unavailable`, bukan `invalid`, saat tidak ada EXIF.

## 11. Penentuan duplikasi insiden
**[FIX]** AI membantu mencocokkan laporan dengan waktu berdekatan dan lokasi berdekatan. **[REKOMENDASI]** Mulai dengan kandidat berbasis radius dan jendela waktu (dapat dikonfigurasi), lalu gabungkan skor tipe kejadian, kesamaan visual/teks, dan lokasi spesifik. Jangan otomatis gabungkan dua kebakaran terpisah hanya karena sama desa/waktu. Simpan laporan sumber tetap terpisah dan kemampuan admin mengoreksi pengelompokan untuk pilot.

## 12. Eksperimen, validasi, dan analitik
**Kebutuhan utama:** Jangan menghitung confusion matrix dari suara verifikator publik saja. TP, TN, FP, FN baru bermakna jika dibandingkan dengan label referensi independen (misalnya rekaman kejadian resmi atau panel evaluator berwenang dengan bukti). Jika data referensi tidak tersedia, laporkan hanya `jumlah verifikasi valid/invalid`, `tingkat konflik`, `jarak`, `latensi verifikasi`, dan `rasio solved claim`, **bukan akurasi final AI**.

**Skenario tes minimum:**
1. Laporan nyata, media dan titik jelas -> lewat filter, disalurkan sekali.
2. Foto kebakaran lama dari internet dengan caption lokasi baru -> sistem memberi sinyal risiko, tidak memastikan palsu tanpa bukti.
3. Tanpa foto/video -> status belum lengkap; warga mendapat panduan keselamatan.
4. Dua laporan kejadian sama dari waktu/lokasi dekat -> satu insiden, dua report.
5. Dua insiden berbeda di radius berdekatan -> jangan salah digabung.
6. Verifikator pada jarak 1,5 km dengan GPS baik -> submit valid.
7. Verifikator pada jarak 2,4 km -> ditolak `OUT_OF_RADIUS`, **bukan** tercatat 'invalid'.
8. Izin GPS ditolak -> submit tidak bisa; tidak ada verifikasi tersimpan.
9. GPS akurasi sangat buruk -> minta refresh; tidak dipaksa lolos.
10. Pengisi memilih invalid -> checkbox solved tidak tampil.
11. Pengisi memilih valid + solved -> simpan solved claim; TRACK memberikan atribusi hati-hati.
12. Dua pengisi memberi jawaban berlawanan -> catat konflik, jangan otomatis ganti final truth.
13. Tak satu pun mengisi link -> alur pelaporan utama tetap normal.
14. Laporan risiko tinggi tetapi skor rendah -> uji kebijakan eskalasi terbatas ke BPBD.
15. Pengiriman ke channel/WA gagal -> retry terkontrol dan log kegagalan.
16. GPS spoofing simulasi -> dokumentasikan bahwa radius bukan bukti autentikasi.

**Metrik:** kelengkapan median waktu; routing akurat per wilayah; duplikasi tepat/salah gabung; false-positive routing; latency hingga kanal/otoritas; rasio verifikasi GPS lolos/ditolak; tingkat konflik publik; proporsi laporan terverifikasi; status klaim selesai; jumlah false alarm yang diterima petugas (dengan penilaian independen); usability form pada konektivitas terbatas.

## 13. Pertanyaan riset prioritas dan jawaban kerja
| Prioritas | Pertanyaan | Posisi kerja saat ini | Yang harus dibuktikan |
|---|---|---|---|
| P0 | Radius 2 km cocok dengan realitas Karhutla? | Pilot awal 2 km [FIX]. | Uji di medan jauh, titik api vs titik pelapor, sinyal GPS dan batas administratif. |
| P0 | Apakah GPS cukup untuk verifikasi 'nyata'? | Tidak; hanya kedekatan yang diklaim perangkat. | Uji spoofing, akurasi, kemudahan akses web. |
| P0 | Minta identitas/nomor pengisi? | [REKOMENDASI] Jangan wajib di MVP; klaim MPA terverifikasi tidak boleh dibuat. | Risiko spam vs hambatan partisipasi dan privasi. |
| P0 | AI tinggi vs 'invalid' dari link? | Simpan keduanya; konflik tidak membatalkan laporan otomatis. | Evaluasi dengan ground truth independen. |
| P0 | Skor rendah tetapi ancaman tinggi? | [REKOMENDASI] Eskalasi terlabel ke otoritas, tahan dari saluran publik. | Persetujuan calon BPBD dan pengukuran false alarm. |
| P0 | Apa arti 'solved'? | Hanya klaim checkbox pengisi, bukan status tindakan BPBD. | Copywriting, status TRACK, risiko false closure. |
| P1 | Bagaimana jika GPS jelek? | Ulangi pengambilan lokasi; jangan ada manual bypass publik. | Nilai threshold akurasi dan usability. |
| P1 | Bagaimana menentukan verifikasi independen? | Simpan event, tetapi identitas unik publik belum tersedia. | Rate-limit/duplikasi sebelum klaim konsensus. |
| P1 | Pencocokan gambar web/metadata bekerja? | Opsi implementasi tim; bukan bukti autentik. | Uji media WhatsApp dan sampel gambar lama/baru. |
| P1 | Apakah routing saluran menggunakan Baileys berhasil? | Keputusan tool demo sudah ada; fungsi harus dites. | Test end-to-end dan fallback delivery. |
| P1 | Integrasi BPBD via WhatsApp tanpa izin/kemitraan? | Prototipe harus gunakan nomor uji atau persetujuan eksplisit. | Pilot operasional dengan calon instansi. |
| P2 | Bagaimana menghadapi area blank spot/akses berbahaya? | Verifikasi publik bersifat opsional, tidak menghambat laporan. | Uji penggunaan nyata; jangan mendorong warga mendekati api. |

## 14. Scope untuk submission dan roadmap
**MVP demo:** (1) WhatsApp report; (2) foto/video wajib + lokasi tervalidasi; (3) AI/aturan confidence dan pencocokan duplikat sederhana; (4) routing ke nomor dummy BPBD dan channel/opsi cadangan; (5) link `/laporan/{slug_id}`; (6) form GPS radius 2 km dengan valid/invalid, deskripsi, foto opsional, checkbox solved pada valid; (7) database verification_events dan TRACK; (8) dashboard ringkas untuk melihat status dan logs.

**Tidak untuk MVP:** otentikasi MPA melalui keanggotaan channel; progress tugas pemadaman berulang; dashboard operasi BPBD lengkap; penanganan wilayah nasional produksi; mekanisme identitas petugas wajib; keputusan akhir resmi dari verifikasi publik; bypass GPS manual publik.

**Roadmap:** uji lapangan dengan calon mitra; SOP eskalasi disetujui BPBD; pemisahan verifikasi warga/MPA resmi bila dibutuhkan; proteksi manipulasi lanjutan; konektivitas rendah; integrasi WhatsApp resmi untuk produksi.

## 15. Research handoff: tugas tim
1. **Product/UX:** wireframe halaman laporan dan validasi error GPS; desain copy TRACK dan penjelasan sumber solved.
2. **Backend:** entitas `report` vs `incident`, random slug, logging event, haversine distance, threshold, status agregasi.
3. **AI/Data:** baseline confidence, dedup berbasis ruang/waktu, desain dataset ground truth, batas klaim image reverse search/metadata.
4. **Infrastructure:** PoC OpenClaw/Baileys untuk routing, retry, channel dan kontak uji, peta wilayah, privasi.
5. **Operations:** skenario simulasi BPBD/MPA, risiko false alarm, SOP eskalasi darurat, benchmark alternatif resmi.
6. **Paper:** klaim berdasarkan yang sudah terdemonstrasi; bedakan MVP, simulasi, rencana; terangkan batasan GPS publik serta keterbatasan satelit dan foto.

## 16. Catatan perubahan dari v2
- **Diganti:** 'link verifikasi MPA tidak dipakai' → kini link unik publik per insiden ada.
- **Diganti:** 'MPA hanya menerima satu arah' → pembaca saluran dapat berkontribusi lewat form web, tanpa verifikasi keanggotaan.
- **Diganti:** 'pelacakan progres tidak ada' → tetap tidak ada pelacakan berkala, **tetapi** ada checkbox klaim selesai opsional dan pembacaan via TRACK.
- **Dipertahankan:** media wajib untuk laporan awal; lokasi teks/shareloc; AI dan FIRMS sebagai sinyal; hold berisiko rendah menurut kebijakan final; nomor pelapor tak dipublikasi; BPBD/damkar sebagai otoritas; saluran MPA sebagai sarana informasi.
- **Belum diputuskan:** routing risiko tinggi berskor rendah; sumber ground truth evaluasi; akurasi lokasi; status publik solved setelah satu checkbox; agregasi konflik; deteksi anti-spam publik.

## 17. Referensi kerja
**Sumber internal:** `Knowledge Doc v2: Bot WhatsApp Pelaporan Karhutla` (20 Oktober 2026); rangkuman situs .id DeveloperDay 2026 dari materi pengguna; klarifikasi bernomor 1–33 pada diskusi 22 Oktober 2026.

**Referensi teknis (untuk dibaca tim):**
- MDN, Geolocation API, HTTPS dan permission: https://developer.mozilla.org/en-US/docs/Web/API/Geolocation_API
- MDN, `GeolocationCoordinates.accuracy`: https://developer.mozilla.org/en-US/docs/Web/API/GeolocationCoordinates/accuracy
- NASA FIRMS, keterbatasan hotspot: https://firms.modaps.eosdis.nasa.gov/map2/
- OpenClaw WhatsApp gateway: https://docs.openclaw.ai/whatsapp
- Google Cloud Vision Web Detection: https://cloud.google.com/vision/docs/detecting-web
- Halaman lomba: https://developerday.id/

**Peringatan akhir:** Semua threshold selain radius 2 km masih usulan riset, bukan keputusan tim. Radius 2 km pun adalah parameter pilot yang perlu divalidasi. Dokumen ini merupakan dasar diskusi dan implementasi prototipe, bukan SOP tanggap darurat resmi.
