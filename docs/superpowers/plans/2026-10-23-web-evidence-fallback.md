# Pelaksanaan perubahan fallback di Task 1

Spec: [fallback pemeriksaan foto](../specs/2026-10-23-web-evidence-fallback-design.md). Kerjakan sendiri berurutan sebagai bagian Task 1, bukan mengganti rencana lima task.

1. Tulis dan jalankan tes gagal: metadata dibuang/ukuran upload, exact vs visual/no-match, retry dan cache, gagal semua -> manual/hold, Vision tidak dipanggil tanpa opt-in, konflik tidak ditimpa fallback, indeks lokal persisten dan gambar polos tidak menjadi mirip palsu.
2. Implementasikan adapter SerpApi, indeks lokal SHA/dHash, coordinator fallback. Pertahankan budget Vision lama; tambahkan budget SerpApi terpisah. Tidak menambah dependencies.
3. Hubungkan CLI/readiness/config default ke jalur baru, simpan hasil saat web unavailable dan Groq gagal secara terpisah. Tambah SERPAPI_API_KEY dan ENABLE_GOOGLE_VISION=false tanpa mengubah secret lain. Perbarui panduan/rencana asli dengan perubahan pengguna.
4. Jalankan seluruh suite Python, tes plugin dan syntax, smoke CLI lokal tanpa provider, serta review perubahan. Jika key SerpApi belum ada, catat blocker uji nyata; jangan lanjut Task 2 atau mengklaim fallback web nyata sudah berhasil.
