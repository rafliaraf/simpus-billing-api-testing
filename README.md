# Pengujian API Billing & Kasir SIMPUS (Puskesmas)

Repo ini isinya hasil pengerjaan tugas magang saya di Diskominfo (Bidang Aptika) buat nguji endpoint billing, kasir, dan kwitansi di SIMPUS.

- **Nama**: Muhammad Rafli Aolia
- **Tugas**: Pengujian kalkulasi tagihan pelayanan, integrasi tarif tindakan dan obat, proses pelunasan kasir (Tunai / QRIS), serta pembuatan invoice elektronik.
- **Hasil**: Semua skenario pengujian aman / lulus (100% Passed).

---

### Link Hasil Pengujian di Postman
Hasil run pengujian otomatisnya bisa langsung dicek di sini:  
👉 [Link Postman Run Result](https://muhammadrafli0876-301798.postman.co/workspace/Muhammad-Rafli-aolia's-Workspac~5857143a-80c0-455e-8d05-c21f3943e962/run/58110220-58b3f2e7-f2c4-40b2-8f0e-36932af9413e?action=share&creator=58110220)

---

### Apa Aja yang Diuji?

1. **Kalkulasi Tagihan (Invoice)**  
   Uji `GET /api/v1/billing/invoice/{kunjungan_id}` buat mastiin hitungan total tagihannya bener (Biaya Registrasi + Tindakan Dokter + Obat). Pas dites, total tagihannya pas Rp 50.000 dan status awalnya `UNPAID`. Kalau ID kunjungan ngasal, sistem nolak dan keluar 404.

2. **Pelunasan di Kasir (Tunai & QRIS)**  
   Uji `POST /api/v1/billing/bayar`:
   - Kalau bayar tunai tapi uangnya kurang, request otomatis ditolak (400 Bad Request).
   - Kalau uangnya lebih (misal bayar 100rb buat tagihan 50rb), kembaliannya pas Rp 50.000 dan status berubah jadi `PAID`.
   - Untuk QRIS, sistem nerima nomor referensi pembayaran dan kembalian diset 0.

3. **Penerbitan Kwitansi Elektronik**  
   Uji `GET /api/v1/billing/kwitansi/{id}` buat mastiin nomor kwitansinya unik dan resmi (`KWT/PKM/202609/XXXX`). Ga ada kwitansi kembar.

4. **Uji Idempotensi (Cegah Dobel Bayar)**  
   Ngetes kalau tombol bayar keklik 2x barengan (double hit / sinyal ngelag). Karena ada `Idempotency-Key`, request kedua ga bakal bikin kwitansi baru atau motong pembayaran dua kali.

---

### Ringkasan Test Case

| No | Skenario | Expected | Hasil |
|:--:|---|---|:---:|
| 1 | Hitung total invoice lengkap | Total Rp 50.000 | **PASS** |
| 2 | Invoice tanpa resep obat | Total Rp 10.000 | **PASS** |
| 3 | Cek kunjungan fiktif | 404 Not Found | **PASS** |
| 4 | Bayar tunai tapi uangnya kurang | 400 Bad Request | **PASS** |
| 5 | Bayar tunai uang lebih (cek kembalian) | Status PAID, kembalian pas | **PASS** |
| 6 | Bayar pakai QRIS | Status PAID & ref kesimpan | **PASS** |
| 7 | Coba bayar lagi tagihan yang udah lunas | 409 Conflict | **PASS** |
| 8 | Cetak kwitansi sah | Nomor unik kwitansi keluar | **PASS** |
| 9 | Uji double click / request kembar | Transaksi ga kedobelan | **PASS** |

---

### Isi File di Repo
- `Postman_Collection_Billing_Puskesmas.json` : Export collection Postman (udah ada request, response sukses, dan script test-nya).
- `server.py` : Mock server sederhana buat ngetes endpoint-nya.
- `test_runner.py` : Script Python buat jalanin semua test case secara otomatis.
