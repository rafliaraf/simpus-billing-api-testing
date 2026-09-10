# Laporan Pengujian Billing & Retribusi Pelayanan Puskesmas

**Nama Penyusun**: Muhammad Rafli Aolia  
**Unit Magang**: Dinas Komunikasi dan Informatika (Diskominfo)  
**Topik Tugas**: Pengujian API Retribusi Layanan, Kasir (Tunai / QRIS), Kwitansi, dan Idempotensi  

---

## A. Tujuan & Ringkasan Pengujian
Tujuan dari pengujian ini adalah memastikan sistem kasir dan tagihan Puskesmas berjalan dengan benar, tidak ada salah hitung tarif retribusi, status pelunasan ter-update dengan aman, serta kwitansi resmi terbit secara unik tanpa risiko dobel transaksi.

Pengujian mencakup 4 hal utama:
1. **Perhitungan Invoice**: Memastikan tarif registrasi, tindakan medis, dan obat dijumlahkan dengan tepat.
2. **Pelunasan di Kasir**: Menguji pembayaran tunai (termasuk validasi kembalian dan uang kurang) serta QRIS.
3. **Penerbitan Kwitansi**: Memastikan status invoice berubah jadi `PAID` dan nomor kwitansi otomatis keluar secara unik.
4. **Idempotensi**: Mencegah dobel transaksi jika tombol bayar diklik berkali-kali atau terjadi request serentak.

---

## B. Hasil Skenario Pengujian

Berikut tabel skenario pengujian yang sudah saya jalankan menggunakan Postman:

| No | Skenario Pengujian | Endpoint & Method | Input Data | Hasil yang Diharapkan | Status |
|:--:|---|---|---|---|:---:|
| 1 | Cek kalkulasi tagihan pasien umum (Lengkap) | `GET /api/v1/billing/invoice/KJ-2026-001` | ID Kunjungan: `KJ-2026-001` | Status 200 OK, total tagihan pas Rp 50.000 (Reg 10rb + Tindakan 25rb + Obat 15rb) | **PASS** |
| 2 | Cek invoice kunjungan tanpa resep obat | `GET /api/v1/billing/invoice/KJ-2026-002` | ID Kunjungan: `KJ-2026-002` | Status 200 OK, total tagihan pas Rp 10.000 (Hanya registrasi & konsultasi) | **PASS** |
| 3 | Cek kunjungan fiktif / tidak ada | `GET /api/v1/billing/invoice/KJ-9999-XXX` | ID Kunjungan salah | Status 404 Not Found, muncul pesan data tidak ditemukan | **PASS** |
| 4 | Coba bayar tunai tapi uangnya kurang | `POST /api/v1/billing/bayar` | Tagihan: 50.000, Bayar: 30.000 | Status 400 Bad Request, ditolak karena nominal pembayaran kurang | **PASS** |
| 5 | Bayar tunai uang lebih (Cek kembalian) | `POST /api/v1/billing/bayar` | Tagihan: 50.000, Bayar: 100.000 | Status 200 OK, invoice berubah `PAID`, kembalian pas Rp 50.000 | **PASS** |
| 6 | Bayar menggunakan nontunai (QRIS) | `POST /api/v1/billing/bayar` | Metode: QRIS, Ref: `QRIS-BCA-992381230` | Status 200 OK, invoice berubah `PAID`, kembalian 0 | **PASS** |
| 7 | Coba bayar invoice yang sudah lunas | `POST /api/v1/billing/bayar` | Bayar ke invoice yang sudah PAID | Status 409 Conflict, ditolak karena invoice sudah lunas | **PASS** |
| 8 | Ambil data kwitansi sah | `GET /api/v1/billing/kwitansi/{id}` | ID Kwitansi hasil transaksi | Status 200 OK, nomor kwitansi unik resmi Puskesmas tampil | **PASS** |
| 9 | Uji Idempotensi (Double click / Replay) | `POST /api/v1/billing/bayar` | Kirim request kembar dengan `Idempotency-Key` sama | Request kedua tidak membuat transaksi baru/ganda, sistem aman dari double charging | **PASS** |

---

## C. Kesimpulan Pengujian
Berdasarkan seluruh skenario pengujian di atas:
- Kalkulasi tarif retribusi dan obat sudah akurat 100%.
- Alur pelunasan kasir (Tunai & QRIS) berjalan sesuai aturan bisnis.
- Nomor kwitansi tercatat unik dan status invoice terkunci aman setelah dibayar.
- Fitur idempotensi sukses mencegah duplikasi data pembayaran.

Semua request dan response pengujian telah diexport dan disimpan pada file Postman Collection.
