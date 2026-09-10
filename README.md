# [SIMPUS-API] Uji Billing, Kasir & Kwitansi Pelayanan

Repository ini berisi hasil penugasan pengujian API Sistem Retribusi dan Billing Puskesmas (SIMPUS) di Dinas Komunikasi dan Informatika (Diskominfo).

**Penyusun**: Muhammad Rafli Aolia  
**Unit**: Diskominfo - Bidang Aptika  
**Status**: All Tests Passed (100% Lulus)

---

## 🔗 Tautan Hasil Pengujian
- **Postman Runner Result**:  
  [Klik di sini untuk melihat Hasil Run Postman](https://muhammadrafli0876-301798.postman.co/workspace/Muhammad-Rafli-aolia's-Workspac~5857143a-80c0-455e-8d05-c21f3943e962/run/58110220-58b3f2e7-f2c4-40b2-8f0e-36932af9413e?action=share&creator=58110220)

---

## 📌 Ringkasan Pengujian

1. **Kalkulasi Tagihan (Invoice)**:
   - Endpoint: `GET /api/v1/billing/invoice/{kunjungan_id}`
   - Memastikan rumus agregasi: `Registrasi + Tindakan Medis + Obat` terhitung tepat (Rp 50.000).
2. **Pelunasan Pembayaran**:
   - Endpoint: `POST /api/v1/billing/bayar`
   - Menguji metode **Tunai** (validasi uang kurang & kalkulasi kembalian) serta **QRIS** (nontunai dengan nomor referensi).
3. **Penerbitan Kwitansi**:
   - Endpoint: `GET /api/v1/billing/kwitansi/{id}`
   - Status invoice ter-update menjadi `PAID` dan menerbitkan nomor kwitansi unik resmi Puskesmas (`KWT/PKM/YYYYMM/XXXX`).
4. **Idempotensi Transaksi**:
   - Memastikan proteksi request kembar (*double-click* atau *race condition*) agar tidak terjadi duplikasi pencatatan pembayaran.

---

## 📊 Matriks Kasus Uji (Test Results)

| No | Kode Uji | Skenario Pengujian | Hasil | Status |
|:--:|---|---|---|:---:|
| 1 | `TC-INV-01` | Agregasi tagihan lengkap (Reg + Tindakan + Obat) | Total Rp 50.000, status UNPAID | **PASS** |
| 2 | `TC-INV-02` | Kunjungan hanya registrasi (tanpa obat) | Total Rp 10.000 | **PASS** |
| 3 | `TC-INV-03` | Validasi kunjungan tidak terdaftar | 404 Not Found | **PASS** |
| 4 | `TC-PAY-03` | Validasi pembayaran tunai kurang | 400 Bad Request | **PASS** |
| 5 | `TC-PAY-02` | Pelunasan tunai uang lebih & kembalian | Status PAID, Kembalian Rp 50.000 | **PASS** |
| 6 | `TC-PAY-04` | Pelunasan QRIS nontunai | Status PAID, Ref Transaksi tercatat | **PASS** |
| 7 | `TC-PAY-05` | Pencegahan bayar ulang invoice lunas | 409 Conflict | **PASS** |
| 8 | `TC-KWT-01` | Pengambilan kwitansi elektronik unik | Nomor Kwitansi Resmi Valid | **PASS** |
| 9 | `TC-IDEM-01` | Uji Idempotensi (Request kembar bersamaan) | Tidak ada duplikasi transaksi | **PASS** |

---

## 📁 Berkas dalam Repository
- `Postman_Collection_Billing_Puskesmas.json` : Export collection Postman lengkap dengan script assertion otomatis dan mock response.
- `server.py` : Mock server API backend simulasi.
- `test_runner.py` : Script automated test runner berbasis Python.
- `DOKUMEN_PENGUJIAN_BILLING.md` : Dokumentasi matriks pengujian lengkap.
