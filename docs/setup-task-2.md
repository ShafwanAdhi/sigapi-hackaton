# Task 2: intake WhatsApp persisten

Task 2 selesai dan uji penerimaan WhatsApp nyata lulus pada 23 Oktober 2026 pukul 22:51 WIB; hasil lengkap diverifikasi langsung di PostgreSQL. Pengujian lokal juga memakai PostgreSQL nyata, HTTP nyata dan plugin Node. Task 2 tidak menjalankan AI, mendistribusikan laporan, atau menerbitkan laporan. `complete` hanya berarti data minimum lengkap.

## Menjalankan di komputer ini

Di setiap terminal gunakan `Set-Location D:\sigapi`. `.env` sudah memiliki `DATABASE_URL` dan `TEST_DATABASE_URL` privat; jangan menyalinnya ke chat. Database demo `sigapi_demo` dan database pengujian `sigapi_test` memakai role aplikasi tanpa hak superuser. Cluster terpisah berada di `.runtime/postgres-intake/data`, hanya mendengarkan loopback port 55432; PostgreSQL lama port 5432 tidak diubah. Cluster demo belum dipasang sebagai Windows service.

Hentikan backend lama dan gateway lama dengan **Ctrl+C pada terminal masing-masing**, lalu jalankan persiapan berikut sekali:

```powershell
Set-Location D:\sigapi
.\.venv\Scripts\python.exe -m backend.cli db-start
.\.venv\Scripts\python.exe -m backend.cli migrate
```

Terminal 1, API privat:

```powershell
Set-Location D:\sigapi
.\.venv\Scripts\python.exe -m backend.cli serve
```

Terminal 2, worker persisten:

```powershell
Set-Location D:\sigapi
.\.venv\Scripts\python.exe -m backend.cli worker
```

Terminal 3, gateway WhatsApp:

```powershell
Set-Location D:\sigapi
.\.venv\Scripts\python.exe -m backend.cli openclaw -- gateway run
```

Tunggu gateway menampilkan `Listening for WhatsApp inbound messages`. Login/pairing yang tersimpan tetap dipakai. CLI menambahkan FFmpeg lokal ke PATH proses secara otomatis. `serve --smoke` hanya untuk memeriksa API metadata Task 1; plugin utama sekarang memerlukan API intake persisten.

## Uji penerimaan Task 2

Dari nomor pengirim yang sudah diizinkan, kirim satu per satu dan tunggu balasannya:

1. `REPORT`. Jika sudah ada draft, bot menawarkan `LANJUT` atau `BARU`; gunakan `BARU` untuk sampel baru.
2. Kirim foto atau video uji. Foto maksimal 10 MB; video maksimal 20 MB dan durasi 30 detik. File harus benar-benar dapat didekode.
3. `KETERANGAN: Terlihat api membakar pepohonan sejak sore, ini sampel demo.` Minimal 10 karakter setelah tanda titik dua.
4. Kirim pin melalui **Lampiran > Lokasi**. Titik harus dimaksudkan sebagai lokasi kejadian. Tautan teks Google Maps belum diparsing dalam Task 2.
5. Ketik `KONFIRMASI LOKASI 1`, atau versi yang disebut bot. Pin pengganti membatalkan konfirmasi sebelumnya dan menaikkan versi.
6. Opsional: `IZIN KONTAK TIDAK` atau `IZIN KONTAK YA`. Tidak memberi izin tidak menghalangi kelengkapan laporan; default tidak berbagi kontak.

Hasil yang diharapkan: balasan dengan **ID laporan yang sama** menyatakan “Data minimum lengkap; belum diverifikasi dan belum dipublikasikan.” Foto hutan dan pin permukiman tidak otomatis dianggap cocok; Task 3 akan memeriksa konflik bukti.

Periksa jumlah/status tanpa mencetak identitas atau isi laporan:

```powershell
.\.venv\Scripts\python.exe -m backend.cli intake-status
```

Restart API dan worker, kemudian kirim `STATUS`: draft tetap ada. `TRACK` belum tersedia pada Task 2. Setelah empat pertanyaan tanpa tambahan fakta, draft ditahan; kirim data baru untuk melanjutkan.

## Jaminan dan batas operasional

- Plugin menyalin media ke spool privat sebelum meneruskan pesan. API memberi receipt HTTP 202 setelah event dan job berhasil commit dalam satu transaksi. Pesan berulang dengan identitas sama tidak membuat laporan/job/balasan ganda.
- Jika API mati, bot menyatakan pesan berada di antrean lokal, bukan sudah diterima server. Spool diputar ulang sesuai urutan penerimaan. Pesan yang belum diterima gateway tidak dijamin oleh spool ini.
- Media API memakai ID buatan server, bukan path/URL yang dipilih pelapor. Jenis media diperiksa dari hasil decode; ekstensi atau header dari pengirim saja tidak cukup.
- Worker mengurutkan perubahan per akun/pengirim; lease token mencegah worker lama menulis setelah diambil alih. Hasil analisis dengan revisi lama ditolak.
- Balasan diproses melalui outbox. Jika pengiriman sudah dimulai tetapi receipt WhatsApp tidak pasti, status menjadi `unknown` dan tidak dikirim ulang otomatis. Operator harus memeriksa WhatsApp/log sebelum tindak lanjut; status ini dapat terjadi saat koneksi terputus atau kanal belum siap. Pesan berikutnya tetap dapat diproses.
- Spool pending dibatasi 500 pesan/256 MB; teks maksimal 4.000 karakter, maksimal 10 media per pesan. Input yang gagal disimpan tidak diakui sebagai laporan tersimpan. Payload ditolak permanen tetap perlu pemeriksaan operator; pengirim lain tidak tertahan oleh kegagalan satu pengirim.
- Data/media dan receipt spool tetap privat di disk; ini demo lokal, belum memiliki kebijakan retensi/backup produksi atau UI penanganan antrean gagal. Jangan menghapus `.runtime` untuk mencoba restart.

## Verifikasi otomatis

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.runtime\node\package\bin\node.exe --test openclaw-plugin/index.test.js openclaw-plugin/intake.test.js
```

Tes database memerlukan `TEST_DATABASE_URL` ke database terpisah; data uji memakai akun acak. Tes transport memakai HTTP loopback, plugin Node, foto sintetis dan PostgreSQL nyata, termasuk receipt hilang dan restart transport/worker. Tidak mengirim WhatsApp atau memanggil provider AI. Bukti ini tidak menggantikan uji WhatsApp di atas.
