# Skenario sintetis SIGAPI — Kota Malang

Seluruh peristiwa, laporan, dan pengamatan dibuat untuk demonstrasi. Tidak ada kebakaran nyata, pelapor nyata, atau tindakan instansi yang direpresentasikan.

## Insiden contoh

| Elemen | Isi demo |
| --- | --- |
| Referensi publik | `SIGAPI-001` |
| Tautan utama | `/laporan/demo-insiden-sigapi` |
| Tautan lama yang tetap didukung | `/laporan/demo-malang-001` |
| Judul | Laporan Kebakaran Lahan |
| Lokasi publik | Kota Malang, Jawa Timur |
| Waktu kejadian di tampilan screenshot | Belum tersedia |
| Status | Belum dikonfirmasi resmi |
| Jawaban awal | Belum ada pilihan |
| Klaim selesai awal | Tidak dicentang |
| Bukti visual | Ilustrasi AI, bukan dokumentasi kejadian nyata |
| Peta | Susunan jalan dan titik ilustratif, bukan lokasi insiden nyata |

Skenario: warga mengamati asap dan api pada sebagian lahan berumput dari tempat aman. Sesuai permintaan screenshot terbaru, halaman menampilkan waktu sebagai **Belum tersedia**. Jam pelaporan sintetis pada rancangan sebelumnya tidak ditampilkan sebagai waktu kejadian. Sifat sintetis data dan provenance foto tetap didokumentasikan di repo meskipun label pengembangan disembunyikan dari tampilan utama.

Tidak ditetapkan alamat nyata, koordinat pribadi, luas, penyebab, korban, probabilitas AI, hasil satelit, atau keterlibatan petugas.

## Narasi untuk menyamakan visual tim

Contoh pesan warga untuk mockup WhatsApp:

> Saya melihat asap dan api pada lahan berumput kering. Saya mengamati dari jalan yang aman. Saya kirim foto dan pin lokasi kejadiannya.

Pin WhatsApp pada visual berikutnya harus ditandai simulasi. Pada sistem fungsional, pin merupakan titik kejadian yang dikonfirmasi pelapor.

Foto dibuat khusus untuk prototipe menggunakan ImageGen dan disimpan sebagai WebP 1200 × 800 piksel. UI menampilkannya dalam bingkai 16:9 dengan object-fit cover. Tidak menggunakan dokumentasi warga atau foto kebakaran nyata. Peta kejadian dan lokasi pengguna adalah dua hal berbeda.

Kartu Channel dan alur penyaluran dibuat terpisah. Frontend ini tidak membuktikan laporan telah dianalisis, diteruskan, atau dibaca otoritas.

## Mencoba halaman

Gunakan tautan utama untuk screenshot bersih. Tambahkan `?dev=1` untuk mencoba langkah GPS di bawah ini beserta kontrol pengembang. Pada tampilan screenshot, GPS tidak dijalankan dan status tetap belum diperiksa.

1. Baca informasi, foto, dan peta kejadian.
2. Pada Konfirmasi Lokasi Anda, tekan Aktifkan Lokasi. Indikator loading mencontohkan proses selama 750 ms.
3. Hasil default menampilkan lokasi memenuhi syarat sebagai **simulasi**: jarak 850 m, akurasi 25 m. Tidak ada GPS perangkat atau server yang dipanggil.
4. Buka Pengaturan simulasi lokasi untuk mencoba izin ditolak, jarak 2,8 km, atau akurasi 140 m. Pilih kondisi lalu tekan Aktifkan Lokasi.
5. Pilih Ya, kejadian benar terjadi. Checkbox Kebakaran sudah tertangani muncul tanpa dicentang.
6. Tambahkan keterangan dan foto lokal bila diperlukan; foto tidak diunggah.
7. Pilih Tidak, informasi kejadian tidak sesuai untuk memeriksa reset checkbox. Jawaban ini sah dan tidak ditampilkan sebagai error form.
8. Tombol Kirim Konfirmasi tetap nonaktif, termasuk ketika simulasi lokasi lolos dan jawaban sudah dipilih. Pengiriman menunggu backend nyata.

Tidak ada simulasi receipt penyimpanan atau toast sukses. Jawaban dan keterangan tetap terjaga ketika simulasi lokasi gagal.

Checkbox selesai merepresentasikan klaim pengisi, bukan status penanganan resmi atau penutupan insiden oleh BPBD.
