# Task 3 — pemeriksaan bukti dan distribusi uji

Implementasi menambahkan ekstraksi bahasa alami, pekerjaan analisis persisten, observasi semua media (maksimal tiga frame/video), pencarian web, indeks media laporan terpisah, FIRMS, batas wilayah, keputusan beralasan, kandidat insiden, serta outbox distribusi. Kelengkapan data, pemeriksaan awal, dan keberhasilan pengiriman adalah status yang berbeda. Tidak ada klaim autentik/palsu berdasarkan skor AI.

Audit Knowledge v3 dan keputusan pengguna tanggal 24 Oktober dirinci dalam [audit kesesuaian bisnis](audit-knowledge-v3-2026-10-24.md). Teks lokasi hanya untuk klarifikasi; pin/koordinat terkonfirmasi tetap wajib dan geocoding tidak diwajibkan. EXIF opsional; ketiadaannya saja tidak menahan laporan. Sesuai keputusan pengguna, demo tidak menambahkan pemberitahuan atau persetujuan khusus pemrosesan laporan/AI; izin berbagi nomor tetap eksplisit, opsional, dan default tidak diberikan. Kekurangan yang tersisa: metadata baru dicatat, belum ada pemeriksaan konsistensi lintas media/keterangan/lokasi/waktu yang tersendiri; panduan keselamatan belum muncul dalam balasan. Panduan ini tidak menyatakan seluruh ketentuan bisnis sudah diimplementasikan.

Pengiriman saat ini **nonaktif**: dua nomor penerima belum tersedia. Kandidat batas Kota Malang telah diunduh dari OpenStreetMap, bukan sertifikasi batas pemerintah. Hash persetujuannya masih kosong. Snapshot NASA FIRMS nyata tersedia secara privat; perlu diperbarui saat demo.

## Menjalankan

Dari `D:\sigapi`, hentikan lalu jalankan ulang proses layanan milikmu setelah migrasi. Proses yang sedang berjalan tidak otomatis menggunakan kode baru. Jangan menjalankan dua gateway untuk akun yang sama.

```powershell
cd D:\sigapi
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m backend.cli db-start
.\.venv\Scripts\python.exe -m backend.cli migrate
.\.venv\Scripts\python.exe -m backend.cli task3-init
.\.venv\Scripts\python.exe -m backend.cli task3-status
```

Jalankan masing-masing pada terminal terpisah:

```powershell
.\.venv\Scripts\python.exe -m backend.cli serve
.\.venv\Scripts\python.exe -m backend.cli worker
.\.venv\Scripts\python.exe -m backend.cli analysis-worker
.\.venv\Scripts\python.exe -m backend.cli openclaw -- gateway run
```

`worker` menerima input dan memeriksa apakah media dapat dibuka. `analysis-worker` melakukan ekstraksi dan pemeriksaan provider. Provider lambat tidak menghalangi penerimaan pesan. Groq menggunakan model privat yang sudah dikonfigurasi; `GROQ_TEXT_MODEL` opsional, default mengikuti `GROQ_VISION_MODEL`. Ada satu panggilan Groq aktif, jarak mulai minimal 35 detik, dan maksimal tiga percobaan HTTP per operasi tersimpan melintasi restart. Status unavailable tidak disamarkan sebagai hasil negatif. Budget/cache SerpApi dan Vision sebelumnya tetap digunakan; Vision default nonaktif.

Migrasi tidak menganalisis laporan lama. Untuk uji baru: kirim `REPORT`, lalu `BARU` jika bot menanyakan laporan aktif. Kirim foto dengan caption `Terjadi kebakaran hutan hari ini`, lanjutkan `Mulai terlihat pukul 20.00 malam`, kirim pin, lalu `KONFIRMASI LOKASI 1`. Sesuaikan waktu dengan kejadian simulasi; jangan gunakan contoh masa depan. Tidak perlu `KETERANGAN:`. Kontak tetap tidak dibagikan tanpa `IZIN KONTAK YA`; pencabutan memakai `IZIN KONTAK TIDAK`. `STATUS` membaca pemeriksaan dan status pengiriman yang tercatat.

## Data dan aktivasi routing

Konfigurasi privat: `.runtime/task3/config.json`; jangan commit atau membagikan isinya. `distribution_enabled` tetap `false` sampai setup selesai. Dua penerima uji harus berbeda satu sama lain, nomor bot, dan seluruh pelapor uji.

```json
"destinations": {
  "community": {"number": "+62NOMOR_UJI_KOMUNITAS", "account_id": "default"},
  "authority": {"number": "+62NOMOR_UJI_OTORITAS", "account_id": "default"}
}
```

Ganti contoh dengan E.164 yang valid. Cocokkan `inbound_senders` dengan daftar pelapor sebenarnya serta `bot_number` dengan akun bot. Pada konfigurasi privat OpenClaw, tambahkan kedua nomor hanya ke `plugins.entries.sigapi-validation-demo.config.outboundRecipients`. Jangan menambahkannya ke `allowSenders` atau `channels.whatsapp.allowFrom`: izin masuk dan keluar berbeda. Restart gateway setelah perubahan plugin.

```powershell
.\.venv\Scripts\python.exe -m backend.cli task3-fetch region
.\.venv\Scripts\python.exe -m backend.cli task3-fetch firms
```

Periksa GeoJSON `.runtime/task3/kota-malang.geojson`, sumber relation OSM, bentuk batas, kode 35.73, dan lokasi uji. Unduhan ulang menghapus persetujuan sebelumnya. Jika sesuai, catat persetujuan hash file yang ditampilkan:

```powershell
.\.venv\Scripts\python.exe -m backend.cli task3-approve-region --sha256 HASH_FILE --reason "Batas Kota Malang telah diperiksa terhadap lokasi demo"
```

Setelah kedua kontak dan persetujuan batas siap, operator dapat mengubah `distribution_enabled` menjadi `true`. Konfigurasi dibaca kembali ketika pengiriman dimulai. Jika wilayah/titik tidak valid, data tetap disimpan tanpa menebak penerima. Batas persis polygon ditahan untuk tinjauan.

FIRMS memakai CSV VIIRS 48 jam dari NASA. Pencocokan radius 3 km dan selisih pengamatan maksimum 24 jam; usia pengambilan dan sumber maksimum 24 jam. Periode yang diperiksa berakhir pada waktu sumber, bukan waktu download; kejadian yang lebih baru daripada cakupan sumber ditahan. Awal cakupan harus mencakup 24 jam sebelum kejadian. Tidak ada hotspot tidak membuktikan kejadian palsu. Metadata sumber, hash, cakupan, dan waktu unduhan disimpan. Snapshot ini perlu diunduh ulang saat demo, bukan diberi timestamp baru secara manual.

## Tinjauan operator

Gunakan UUID lengkap dari database lokal. Ekspor inspeksi mengandung data pribadi; simpan di `.runtime`, jangan dipublikasikan.

```powershell
.\.venv\Scripts\python.exe -m backend.cli report-inspect UUID_LAPORAN --output .runtime/task3/inspection.json
.\.venv\Scripts\python.exe -m backend.cli analyze UUID_LAPORAN
```

`analyze` adalah opt-in operator eksplisit untuk laporan lama, bukan tindakan otomatis migrasi. Untuk konflik web, referensikan `evidence_key` frame yang benar, alasan, dan bukti pendukung. Pernyataan pelapor “foto asli” tidak menghapus konflik.

```powershell
.\.venv\Scripts\python.exe -m backend.cli review-evidence UUID_LAPORAN --key UUID_MEDIA:0 --reason "Alasan hasil pemeriksaan operator" --reference https://sumber-bukti.example/halaman
.\.venv\Scripts\python.exe -m backend.cli review-incident UUID_LAPORAN --merge-into UUID_KANDIDAT --reason "Bukti kejadian yang sama telah diperiksa"
.\.venv\Scripts\python.exe -m backend.cli review-incident UUID_LAPORAN --reason "Kejadian terpisah telah diperiksa"
```

Kandidat 500 meter/enam jam tidak digabung otomatis. AI memberi saran yang disimpan terpisah; operator menentukan penggabungan. Tanpa `--merge-into`, tindakan mengonfirmasi insiden terpisah atau memisahkan laporan dari kelompok lama. Koreksi pengelompokan membatalkan antrean lama yang belum dikirim; bukti, laporan sumber, dan audit tetap disimpan. Slug 128-bit disiapkan tanpa tautan publik sebelum Task 4.

```powershell
.\.venv\Scripts\python.exe -m backend.cli reconcile-delivery UUID_OUTBOX --receipt ID_PESAN_WHATSAPP --reason "Receipt WhatsApp telah diperiksa operator"
.\.venv\Scripts\python.exe -m backend.cli reconcile-delivery UUID_OUTBOX --retry --reason "Riwayat WhatsApp diperiksa dan pesan dipastikan belum terkirim"
```

`unknown` tidak diulang otomatis. Retry hanya setelah pemeriksaan operator, tetap harus lolos pemeriksaan revisi, tujuan, keputusan, dan consent saat mulai kirim. Maksimal lima distribusi per sepuluh menit per tujuan; selebihnya mengantre. Pelapor baru menerima status berhasil setelah receipt provider tercatat. Pesan keluar berupa kartu terstruktur; tidak memuat teks mentah atau media asli. Kontak hanya ditambahkan pada kartu otoritas ketika consent masih aktif.

## Verifikasi dan batas penerimaan

Tes otomatis memakai PostgreSQL terpisah dari `TEST_DATABASE_URL`, HTTP lokal, transport Node, dan fixture provider untuk kegagalan. Jangan arahkan test database ke data demo. Uji langsung Groq ekstraksi dua pesan sudah berhasil; hasil privat `.runtime/task3/live-extraction.json`. Unduhan OSM/NASA nyata tersimpan privat. Itu belum membuktikan seluruh alur WhatsApp Task 3.

Task 3 baru selesai setelah WhatsApp nyata membuktikan percakapan alami, bukti provider tersimpan, konflik menahan komunitas, eskalasi **BELUM TERVERIFIKASI** mencapai otoritas uji, dan laporan layak terkirim sekali. Dua nomor belum tersedia, jadi gate pengiriman nyata masih pending. Dashboard, form GPS, tautan publik, dan TRACK mengikuti tahap berikutnya.

Review akhir menemukan tiga masalah penting pada fencing worker dan acuan insiden; ketiganya diperbaiki dengan uji regresi. Dua keterbatasan minor masih dicatat: kandidat dapat mencakup insiden provisional tanpa laporan setelah penggabungan (menambah kebutuhan review operator), dan exception tak terduga pada satu frame dapat menghentikan sisa frame video tersebut. Kasus kedua ditandai pemeriksaan parsial/gagal dan menahan distribusi, bukan diperlakukan sebagai pemeriksaan lengkap.

Verifikasi terakhir: **105 tes Python lulus tanpa skip**, termasuk PostgreSQL/HTTP lokal, dan **13 tes Node lulus**. Pemeriksaan sintaks dan `git diff --check` lulus (peringatan konversi baris Windows saja). Migrasi melewati versi yang sudah diterapkan sehingga tidak mengulang DDL ketika intake aktif. Tidak ada proses pengguna yang dimatikan atau gateway yang dinyalakan ulang otomatis.
