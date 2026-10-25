# Audit UI SIGAPI

Status: delapan temuan dalam lingkup tampilan, bahasa, dan interaksi sudah ditangani. Build, 3 pengujian reducer, dan 4 pengujian browser lulus setelah perubahan akhir. Penilaian visual didukung inspeksi browser dan bukti sebelum/sesudah, dengan batas prototipe tetap dicatat.

## Lingkup dan arah

Audit berdasarkan empat kriteria pengguna: tampilan generik, bahasa tidak alami, aset tidak masuk akal, serta interaksi yang tampak selesai tetapi tidak bekerja. Ini halaman konfirmasi kejadian untuk warga, bukan landing page pemasaran. Pola form yang lazim tidak otomatis merupakan AI slop.

Pendekatan: penyempurnaan identitas yang sudah disetujui, dengan variasi desain 3/10, gerak 2/10, dan kepadatan 5/10. Tidak mengganti logo, enam warna SIGAPI, font Inter lokal, header hutan, footer kontur, urutan isian, atau URL. CSS/React yang sudah ada tetap menjadi fondasi; tidak menambah library untuk mengganti gaya.

## Kondisi sebelum perubahan

- Palet: `#C84B1B`, `#1F4D45`, `#FFFCF8`, `#FBE8DE`, `#26332F`, `#66736D`.
- Halaman: header, informasi dan foto kejadian, peta, pemeriksaan lokasi, jawaban, checkbox bersyarat, keterangan, foto tambahan, pengiriman nonaktif, pesan keselamatan, footer.
- Desktop dua kolom; mobile satu kolom. Screenshot awal: `artifacts/anti-slop-before-390.png` dan `anti-slop-before-1440.png`.
- Tidak ada tiga kartu fitur pemasaran, klaim statistik palsu, testimoni fiktif, slogan bombastis, efek neon, atau navigasi kosong. Kedua tautan yang ada memiliki tujuan nyata.
- Header dan foto kejadian merupakan citra generatif yang sudah didokumentasikan, bukan bukti kejadian nyata. Peta adalah skema, bukan geografi Kota Malang yang terverifikasi.
- Batas fungsi tetap: tidak ada GPS perangkat, upload, penyimpanan, atau pengiriman nyata. Pada revisi setelah audit, pengguna memilih agar tombol lokasi halaman utama kembali berwarna Oranye Bara dengan fungsi tetap nonaktif.
- Route utama dan alias dipertahankan. Metadata judul/deskripsi serta `noindex, nofollow` tetap sesuai penggunaan lokal.

## Temuan yang diperbaiki

| Temuan | Dampak | Perbaikan |
| --- | --- | --- |
| Tombol lokasi oranye tampak aktif meskipun disabled | Membingungkan | Pertahankan keterangan keterbatasan. Sesuai revisi pengguna setelah audit, warna oranye dikembalikan sementara fungsi tetap nonaktif |
| Bahasa mencampur kamu/Anda, badge Inggris generik | Identitas dan instruksi tidak konsisten | Gunakan Anda, kalimat konkret, dan nomor laporan pada header |
| Informasi dan peta memiliki bingkai terpisah dengan bobot yang sama | Pengelompokan konteks lemah | Satukan keduanya dalam satu permukaan dengan pemisah bagian |
| Area unggah besar bergaris putus-putus, tanpa dukungan drop | Menjanjikan interaksi yang tidak tersedia | Gunakan pemilih berkas ringkas dengan batas format/ukuran yang jelas |
| Preview foto memakai crop 16:9 | Detail bukti dapat hilang dari preview | Tampilkan seluruh foto dengan `object-fit: contain` |
| Fokus hilang setelah tombol hapus foto dihapus dari DOM | Alur keyboard terputus | Kembalikan fokus ke pemilih foto |
| Petunjuk keterangan hanya berupa placeholder; fokus textarea terlalu lembut | Instruksi hilang saat mengetik; fokus sulit dilihat | Petunjuk permanen terhubung melalui ARIA dan outline keyboard yang solid |
| Label titik peta berada di sudut, jauh dari pin | Hubungan label dan titik kurang jelas | Tempatkan label di dekat pin; pertahankan peringatan bahwa peta bukan navigasi |

## Hal yang sengaja dipertahankan

Logo asli, palet, foto hutan tajam, footer hijau berpola kontur, serta pesan keselamatan dan keterbatasan konfirmasi publik adalah pilihan pengguna dan fungsi yang relevan. Inter cocok untuk form layanan publik; tidak diganti hanya untuk terlihat berbeda. Setelah audit, pengguna meminta ikon antarmuka diganti menggunakan Lucide Icons. Seluruh ikon antarmuka kini berasal dari keluarga outline Lucide melalui komponen bersama, tanpa menambah animasi dekoratif. Radio, fieldset, label, dan batas unggah tetap menggunakan perilaku native.

Peta skematis dan kontrol nonaktif merupakan batas prototipe yang diketahui, bukan bukti bahwa integrasi sudah selesai. Audit ini tidak mengubahnya menjadi layanan produksi dan tidak mengarang koordinat atau hasil pengiriman. Penanda pengembangan tetap di mode `?dev=1` serta dokumentasi sesuai permintaan screenshot bersih pengguna.

## Pemeriksaan akhir

- Putaran 1: audit kode dan tampilan awal, inventaris tautan/tombol, serta screenshot sebelum perubahan. Pengguna mengonfirmasi tombol lokasi tetap disabled.
- Putaran 2: inspeksi halaman setelah perbaikan pada mobile dan desktop; jawaban valid/tidak sesuai, preview foto, dan error unggah. Ring fokus kartu jawaban dibatasi ke interaksi keyboard agar klik mouse tidak memberi penekanan ganda.
- Putaran 3: pemeriksaan ulang reflow, kontras, ARIA, fokus, dan regresi interaksi. Informasi dan peta berada pada satu bingkai; pengujian layout menggunakan batas bingkai tersebut, bukan batas bagian internalnya.
- Revisi setelah audit: pengguna mengoreksi preferensi tampilan tombol Aktifkan Lokasi dan Kirim Konfirmasi. Keduanya kembali berwarna Oranye Bara di halaman utama, dengan atribut disabled tetap dipertahankan. Teks pengiriman belum tersedia di bawah tombol Kirim Konfirmasi hanya tampil pada mode pengembangan sesuai permintaan screenshot bersih.
- `anti-slop-review.json`: sembilan lebar 320–1920px tanpa overflow; tiga keadaan (awal, valid dengan foto, tidak sesuai) lolos pemeriksaan sampel teks di luar header, minimum 4,62:1. Tidak ditemukan ID ganda, referensi ARIA yang tidak terselesaikan, atau tautan kosong.
- `anti-slop-header-review.json`: sebelas lebar 320–2560px; sampel piksel teks header minimum 4,81:1. Header tetap memakai foto responsif tanpa blur.
- Pemilih berkas membuka file chooser; foto besar/rusak ditolak; preview/hapus bekerja; fokus kembali ke pemilih; pilihan tidak sesuai menghapus checkbox selesai; keterangan tetap terjaga.
- Build lulus; 3 pengujian reducer lulus; 4 pengujian browser lulus. Regresi mencakup layout satu/dua kolom, lokasi simulasi dan pembatalannya, kedua jawaban, reset checkbox, file besar/rusak, preview/hapus foto dan fokus, route alias/tidak tersedia, keyboard, reduced motion, landscape, dan reflow CSS zoom 2x.

Preview utama: `artifacts/anti-slop-after-390.png`, `anti-slop-after-1440.png`, `anti-slop-filled-mobile.png`, serta `anti-slop-error-mobile.png`. Header dan footer berpola tetap mengikuti persetujuan pengguna. Tidak dilakukan commit, push, atau merge dalam audit ini.

## Rujukan

- [W3C WAI: Form Instructions](https://www.w3.org/WAI/tutorials/forms/instructions/) untuk instruksi yang tetap tersedia dan terhubung dengan kontrol.
- [W3C: Focus Appearance](https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance.html) sebagai rujukan desain indikator fokus, tanpa mengklaim sertifikasi WCAG.

Tidak ada alat yang dapat membuktikan "nol AI slop" secara objektif. Kesimpulan audit dibatasi pada temuan visual, bahasa, aset, dan interaksi yang benar-benar diperiksa.
