# Skenario sintetis SIGAPI — Kota Malang

Seluruh peristiwa, laporan, dan pengamatan dalam skenario ini dibuat untuk demonstrasi. Tidak ada kebakaran nyata, pelapor nyata, atau tindakan instansi yang direpresentasikan.

## Insiden contoh

| Elemen | Isi demo |
| --- | --- |
| Referensi publik | `SIGAPI-DEMO-001` |
| Tautan frontend | `/laporan/demo-malang-001` |
| Kategori | Kebakaran hutan/lahan |
| Lokasi publik | Area lahan terbuka, Kota Malang, Jawa Timur |
| Waktu dilaporkan | 24 Oktober 2026, 14.20 WIB |
| Laporan awal | Warga melaporkan asap dan api pada sebagian lahan berumput kering. |
| Kondisi terkini | Belum dikonfirmasi |
| Konfirmasi publik awal | Belum ada |
| Klaim selesai awal | Belum ada; tidak menyatakan api masih aktif |
| Bukti visual | Ilustrasi AI, bukan dokumentasi kejadian nyata |
| Peta | Skema jalan dan titik ilustratif; bukan peta navigasi atau titik insiden nyata |

Tidak ditetapkan alamat nyata, koordinat pribadi, luas kebakaran, penyebab, korban, probabilitas AI, hasil satelit, atau keterlibatan petugas. Waktu pelaporan tidak dinyatakan sebagai waktu api mulai menyala.

## Narasi untuk menyamakan visual tim

Contoh pesan warga untuk mockup WhatsApp:

> Saya melihat asap dan api pada lahan berumput kering. Saya mengamati dari jalan yang aman. Saya kirim foto dan pin lokasi kejadiannya.

Pin pada visual WhatsApp nanti harus ditandai simulasi. Pada sistem fungsional, pin merupakan titik kejadian yang dikonfirmasi pelapor. Gambar di frontend dibuat khusus untuk prototipe menggunakan ImageGen, lalu dikompresi menjadi WebP berukuran 1200 × 800 piksel. Tidak menggunakan dokumentasi warga atau foto kebakaran nyata.

Kartu Channel dan alur penyaluran merupakan visual yang akan dibuat terpisah. Frontend ini tidak membuktikan laporan telah dianalisis, diteruskan, atau dibaca oleh otoritas.

## Keadaan form yang bisa dicoba

1. Buka tautan demo dan baca overview, foto, serta peta.
2. Tekan `Berikan konfirmasi` untuk menuju form.
3. Pilih simulasi lokasi dalam radius 850 m, lalu jalankan simulasi lokasi. Akurasi 25 m adalah angka fixture.
4. Pilih `Ya, benar terjadi`. Checkbox selesai tampil tanpa dicentang.
5. Isi keterangan, misalnya: `Asap masih terlihat dari jalan. Saya mengamati dari tempat yang aman.`
6. Tambahkan foto lokal bila diperlukan; preview tidak diunggah.
7. Tekan `Coba kirim konfirmasi`. Halaman menjelaskan bahwa interaksi selesai dalam simulasi dan tidak ada data yang dikirim/disimpan.

Untuk variasi screenshot: pilih invalid untuk menyembunyikan dan mereset checkbox selesai; pilih izin ditolak atau jarak 2,8 km lalu jalankan simulasi untuk melihat pengiriman terblokir. Jawaban mengenai kejadian tidak berubah hanya karena simulasi lokasi gagal.

Checkbox selesai dapat dicoba sebagai keadaan alternatif. Itu merepresentasikan klaim pengisi, bukan status penanganan resmi atau penutupan insiden oleh BPBD.
