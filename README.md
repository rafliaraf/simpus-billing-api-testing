# Laporan Hasil Pekerjaan Magang: [SIMPUS-API] Uji Billing, Kasir & Kwitansi Pelayanan

**Nama Pembuat**: Muhammad Rafli Aolia  
**Unit Kerja**: Dinas Komunikasi dan Informatika (Diskominfo) - Bidang Aptika  
**Modul Sistem**: Sistem Informasi Manajemen Puskesmas (SIMPUS) - Modul Kasir & Billing  
**Status Pengujian**: 100% Selesai & Lulus Pengujian (All Tests Passed)

---

## 1. Tautan & Berkas Pengumpulan
- **Tautan Hasil Uji (Postman Runner)**:  
  `https://muhammadrafli0876-301798.postman.co/workspace/Muhammad-Rafli-aolia's-Workspac~5857143a-80c0-455e-8d05-c21f3943e962/run/58110220-58b3f2e7-f2c4-40b2-8f0e-36932af9413e?action=share&creator=58110220`
- **File Arsip (ZIP)**: `Pengujian_Billing_Puskesmas_Muhammad_Rafli_Aolia.zip` (Berisi Collection Postman, script otomatis, mock server API, dan dokumen teknis).

---

## 2. Ringkasan Hasil Pengujian Sesuai Kriteria Penugasan

### A. Kalkulasi Tagihan (Invoice) - `GET /api/v1/billing/invoice/{kunjungan_id}`
- **Hasil**: Sistem berhasil menghitung agregasi biaya layanan secara presisi.
- **Rincian Validasi**:
  - Biaya Registrasi: Rp 10.000
  - Total Tarif Tindakan Medis: Rp 25.000 (Pemeriksaan Dokter Rp 15.000 + Pembersihan Luka Rp 10.000)
  - Total Harga Obat: Rp 15.000 (Paracetamol Rp 7.000 + Amoxicillin Rp 8.000)
  - **Grand Total**: Tepat **Rp 50.000** dengan status awal `UNPAID`.
  - Penanganan kasus negatif: Kunjungan tidak terdaftar menghasilkan response `404 Not Found`.

### B. Pelunasan Pembayaran - `POST /api/v1/billing/bayar`
- **Metode Tunai**:
  - Validasi pembayaran kurang: Nominal di bawah tagihan otomatis ditolak dengan response `400 Bad Request`.
  - Validasi pembayaran lebih: Tagihan Rp 50.000 dibayar Rp 100.000 sukses menghitung kembalian tepat Rp 50.000.
- **Metode Nontunai (QRIS)**:
  - Pembayaran QRIS sukses mencatat nomor referensi transaksi (`ref_transaksi`) dari acquirer/bank dan kembalian diset Rp 0.

### C. Penerbitan Kwitansi - `GET /api/v1/billing/kwitansi/{id}`
- Status invoice berhasil ter-update dari `UNPAID` menjadi **`PAID`**.
- Sistem menerbitkan nomor kwitansi unik dengan format penomoran resmi Pemda: `KWT/PKM/202609/XXXX` beserta timestamp pelunasan dan identitas kasir loket.

### D. Idempotensi Transaksi (Pencegahan Double-Payment)
- Pengujian simulasi *double-click* / *concurrency* dengan mengirimkan request kembar (`Idempotency-Key` sama).
- **Hasil**: Server mengenali transaksi berulang dan tidak menduplikasi pencatatan pembayaran maupun nomor kwitansi (*Zero Double-Deduction*).

---

## 3. Matriks Hasil Pengujian (Semua Lulus / PASS)

| No | Kode Uji | Skenario | Expected | Actual | Status |
|:--:|---|---|---|---|:---:|
| 1 | `TC-INV-01` | Agregasi Invoice Pasien Umum (Lengkap) | Total Rp 50.000, status UNPAID | Sesuai | **PASS** |
| 2 | `TC-INV-02` | Kunjungan Tanpa Resep Obat | Total Rp 10.000 | Sesuai | **PASS** |
| 3 | `TC-INV-03` | Validasi Kunjungan Fiktif | 404 Not Found | Sesuai | **PASS** |
| 4 | `TC-PAY-03` | Validasi Pembayaran Tunai Kurang | 400 Bad Request | Sesuai | **PASS** |
| 5 | `TC-PAY-02` | Pelunasan Tunai Uang Lebih & Kembalian | 200 OK, Status PAID, Kembalian Rp 50k | Sesuai | **PASS** |
| 6 | `TC-PAY-04` | Pelunasan QRIS dengan No Referensi | 200 OK, Status PAID, Ref tersimpan | Sesuai | **PASS** |
| 7 | `TC-PAY-05` | Pencegahan Bayar Ulang Invoice Lunas | 409 Conflict | Sesuai | **PASS** |
| 8 | `TC-KWT-01` | Pengambilan Kwitansi Elektronik Sah | 200 OK, Format No Kwitansi Unik Valid | Sesuai | **PASS** |
| 9 | `TC-IDEM-01` | Uji Idempotensi (Double Request Bersamaan) | 1 Record Kwitansi, Tanpa Duplikasi | Sesuai | **PASS** |

---
*Dibuat untuk memenuhi tugas magang instansi Diskominfo - Bidang Aplikasi Informatika (Aptika).*
