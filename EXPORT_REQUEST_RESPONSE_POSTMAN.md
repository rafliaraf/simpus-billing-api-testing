# LAPORAN SIMULASI REQUEST & RESPONSE POSTMAN
**Sistem**: SIMPUS (Sistem Informasi Manajemen Puskesmas) - Modul Billing & Retribusi  
**Penguji**: Muhammad Rafli Aolia (Diskominfo - Bidang Aptika)  
**Alur**: Pembuatan / Pengambilan Invoice $\rightarrow$ Pelunasan Kasir (Tunai / QRIS) $\rightarrow$ Konfirmasi Pelunasan Sukses & Kwitansi

---

## 1. Tahap 1: Pengambilan & Kalkulasi Tagihan (Invoice)
Memverifikasi agregasi rincian biaya registrasi, tindakan medis, dan obat.

### Request:
- **Method**: `GET`
- **URL**: `http://127.0.0.1:8080/api/v1/billing/invoice/KJ-2026-001`
- **Headers**:
  ```http
  Accept: application/json
  ```

### Response (200 OK):
```json
{
  "success": true,
  "data": {
    "invoice_id": "INV-KJ-2026-001",
    "kunjungan_id": "KJ-2026-001",
    "pasien_nama": "Budi Santoso",
    "nik": "3201234567890001",
    "poli": "Poli Umum",
    "rincian": {
      "biaya_registrasi": 10000,
      "tindakan": [
        {
          "kode": "T01",
          "nama": "Pemeriksaan Dokter & Tensi",
          "tarif": 15000
        },
        {
          "kode": "T02",
          "nama": "Pembersihan Luka Ringan",
          "tarif": 10000
        }
      ],
      "subtotal_tindakan": 25000,
      "obat": [
        {
          "kode": "OB01",
          "nama": "Paracetamol 500mg (10 tab)",
          "harga": 7000,
          "qty": 1
        },
        {
          "kode": "OB02",
          "nama": "Amoxicillin 500mg (10 tab)",
          "harga": 8000,
          "qty": 1
        }
      ],
      "subtotal_obat": 15000
    },
    "total_tagihan": 50000,
    "status": "UNPAID",
    "kwitansi_id": null
  }
}
```
*Catatan Hasil: Registrasi (10.000) + Tindakan (25.000) + Obat (15.000) = Total Rp 50.000. Status awal terverifikasi UNPAID.*

---

## 2. Tahap 2: Proses Pelunasan di Kasir (Metode Tunai)
Menguji pelunasan di loket dengan uang tunai Rp 100.000 untuk tagihan Rp 50.000 (menghitung kembalian).

### Request:
- **Method**: `POST`
- **URL**: `http://127.0.0.1:8080/api/v1/billing/bayar`
- **Headers**:
  ```http
  Content-Type: application/json
  Idempotency-Key: IDEM-KEY-001
  ```
- **Body (raw JSON)**:
```json
{
  "kunjungan_id": "KJ-2026-001",
  "metode": "TUNAI",
  "nominal_bayar": 100000,
  "idempotency_key": "IDEM-KEY-001"
}
```

### Response (200 OK - Konfirmasi Pelunasan Sukses):
```json
{
  "success": true,
  "message": "Pembayaran berhasil diterima dan kwitansi diterbitkan.",
  "data": {
    "status_invoice": "PAID",
    "total_tagihan": 50000,
    "nominal_bayar": 100000,
    "kembalian": 50000,
    "kwitansi_id": "d73981a2",
    "nomor_kwitansi": "KWT/PKM/202609/0001",
    "waktu_bayar": "2026-09-10 11:35:40"
  }
}
```
*Catatan Hasil: Status berubah menjadi PAID, kembalian dihitung tepat Rp 50.000, dan nomor kwitansi unik berhasil diterbitkan.*

---

## 3. Tahap 2 (Alternatif): Proses Pelunasan Kasir (Metode QRIS Nontunai)
Menguji pelunasan nontunai dengan menyertakan referensi transaksi QRIS.

### Request:
- **Method**: `POST`
- **URL**: `http://127.0.0.1:8080/api/v1/billing/bayar`
- **Headers**:
  ```http
  Content-Type: application/json
  Idempotency-Key: IDEM-KEY-002
  ```
- **Body (raw JSON)**:
```json
{
  "kunjungan_id": "KJ-2026-002",
  "metode": "QRIS",
  "nominal_bayar": 10000,
  "ref_transaksi": "QRIS-BCA-992381230",
  "idempotency_key": "IDEM-KEY-002"
}
```

### Response (200 OK):
```json
{
  "success": true,
  "message": "Pembayaran berhasil diterima dan kwitansi diterbitkan.",
  "data": {
    "status_invoice": "PAID",
    "total_tagihan": 10000,
    "nominal_bayar": 10000,
    "kembalian": 0,
    "kwitansi_id": "2749922f",
    "nomor_kwitansi": "KWT/PKM/202609/0002",
    "waktu_bayar": "2026-09-10 11:35:40"
  }
}
```

---

## 4. Tahap 3: Verifikasi Kwitansi Elektronik yang Diterbitkan
Memverifikasi data kwitansi sah yang dapat dicetak oleh loket kasir.

### Request:
- **Method**: `GET`
- **URL**: `http://127.0.0.1:8080/api/v1/billing/kwitansi/d73981a2`

### Response (200 OK):
```json
{
  "success": true,
  "data": {
    "kwitansi_id": "d73981a2",
    "nomor_kwitansi": "KWT/PKM/202609/0001",
    "invoice_id": "INV-KJ-2026-001",
    "kunjungan_id": "KJ-2026-001",
    "pasien_nama": "Budi Santoso",
    "nik": "3201234567890001",
    "poli": "Poli Umum",
    "total_tagihan": 50000,
    "metode_bayar": "TUNAI",
    "nominal_bayar": 100000,
    "kembalian": 50000,
    "ref_transaksi": "-",
    "status": "LUNAS",
    "kasir": "Kasir Loket 1 (Petugas Diskominfo)",
    "waktu_bayar": "2026-09-10 11:35:40"
  }
}
```

---

## 5. Tahap 4: Pengujian Idempotensi (Cegah Duplikasi Transaksi)
Menguji jika kasir melakukan double click / request dikirim ulang dengan `Idempotency-Key` yang sama.

### Request:
- **Method**: `POST`
- **URL**: `http://127.0.0.1:8080/api/v1/billing/bayar`
- **Headers**: `Idempotency-Key: IDEM-KEY-001`
- **Body**: Sama seperti tahap 2

### Response (200 OK - Idempotent Replay):
```json
{
  "success": true,
  "is_idempotent_replay": true,
  "message": "Transaksi sudah diproses sebelumnya (Idempotent response)",
  "data": {
    "status_invoice": "PAID",
    "total_tagihan": 50000,
    "nominal_bayar": 100000,
    "kembalian": 50000,
    "kwitansi_id": "d73981a2",
    "nomor_kwitansi": "KWT/PKM/202609/0001",
    "waktu_bayar": "2026-09-10 11:35:40"
  }
}
```
*Catatan Hasil: Server tidak membuat kwitansi baru atau menduplikasi pemotongan, data transaksi tetap utuh 1 record.*
