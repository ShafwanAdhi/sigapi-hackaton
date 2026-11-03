# Fallback pemeriksaan foto demo

Keputusan pengguna 23 Oktober 2026: memakai beberapa opsi fallback menggantikan keharusan Google Vision. Berlaku sebagai perubahan terbatas pada Task 1 dan 3 dari rencana lima task; urutan implementasi lain tetap.

## Pendekatan

Google Vision tunggal memerlukan billing yang belum ingin diaktifkan pengguna. Pencocokan lokal saja murah tetapi tidak mencari internet. Pendekatan yang dipilih pengguna: Groq tetap untuk observasi, SerpApi Google Lens untuk pencarian web, pencocokan lokal dan pemeriksaan manual sebagai pelengkap/fallback. Pilihan teknis pelaksana: Vision tetap tersedia **hanya opt-in**, default mati; tidak ada pemanggilan Google berbayar otomatis.

## Alur dan hasil

1. Decode media. SHA-256 dan dHash dibandingkan dengan koleksi lokal yang pernah diperiksa; dHash hanya kandidat kemiripan. Catat referensi dan versi algoritme, jangan menyebutnya hasil pencarian web atau deteksi tahan crop.
2. SerpApi menerima turunan JPEG tanpa EXIF, <=450.000 byte, sisi <=1280 px; unggah melalui Image API untuk memperoleh image_id. Media tidak dihosting publik. Cari exact_matches, lalu visual_matches bila exact kosong. Exact candidate menghentikan pencarian lanjutan dan memerlukan klarifikasi; visual match hanya sinyal lemah. Tidak ada hasil bukan foto asli.
3. Fallback hanya ketika layanan gagal/tidak dikonfigurasi/kuota habis, bukan untuk mencari hasil yang lebih menguntungkan. Vision dipanggil hanya bila ENABLE_GOOGLE_VISION=true. Seluruh hasil dan kegagalan sebelumnya dipertahankan.
4. Semua web provider gagal: outcome unavailable, manual_review=pending (operator dapat memakai Lens/TinEye lewat browser), hold publik. Hash lokal atau pending manual tidak menyelesaikan pemeriksaan web. Tidak mengotomatiskan scraping browser TinEye. Task 3 tetap menerapkan eskalasi ancaman tinggi lengkap dengan label BELUM TERVERIFIKASI.

Lingkup sekarang adalah CLI smoke; belum ada intake WhatsApp persisten, UI operator, penyimpanan hasil review manusia, atau routing. CLI hanya menandai kebutuhan review; tidak menyatakan pemeriksaan manual sudah dikerjakan. Koleksi lokal ini diberi scope operator_smoke, bukan laporan warga.

## Batas

Cache sukses per SHA asli dan versi provider. Anggaran Vision 50 yang sudah ada dipertahankan; anggaran SerpApi terpisah 50 HTTP request total termasuk upload/retry (lebih ketat daripada kuota vendor), atomik/persisten. Maksimal tiga percobaan per operasi, jeda 2/5 detik untuk timeout/429/5xx saja. Secret dan raw response vendor tidak masuk log/hasil; gunakan whitelist link/title/source, sumber, waktu, versi dan hash turunan. Link tidak di-fetch oleh backend. Hanya HTTP(S) tanpa credential diterima sebagai referensi.

Gerbang Task 1 direvisi: web provider nyata yang terkonfigurasi harus lulus; Google billing tidak wajib. Unit tests/hasil lokal/manual pending tidak menggantikan uji SerpApi nyata. SerpApi key belum dikonfirmasi, tidak mengarang keberhasilan.

Sumber diperiksa 23 Oktober 2026: [Image API](https://serpapi.com/image-api), [upload Lens](https://serpapi.com/google-lens-upload-an-image), [exact matches](https://serpapi.com/google-lens-exact-matches-api), [pricing](https://serpapi.com/pricing).
