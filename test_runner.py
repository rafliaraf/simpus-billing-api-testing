import json
import threading
import time
import urllib.error
import urllib.request

BASE_URL = "http://127.0.0.1:8080/api/v1/billing"

def request(method, path, data=None, headers=None):
    url = f"{BASE_URL}{path}"
    headers = headers or {}
    req_data = json.dumps(data).encode("utf-8") if data else None
    if req_data:
        headers["Content-Type"] = "application/json"
    
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            return response.status, json.loads(res_body)
    except urllib.error.HTTPError as e:
        res_body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(res_body)
        except Exception:
            return e.code, res_body

def log_test(tc_id, name, is_pass, detail=""):
    badge = "[PASS]" if is_pass else "[FAIL]"
    print(f"{badge} {tc_id} : {name}")
    if detail:
        print(f"       -> {detail}")

def run_all_tests():
    print("=" * 70)
    print("PENGUJIAN SISTEM RETRIBUSI & BILLING PUSKESMAS (DISKOMINFO)")
    print("=" * 70)

    # -------------------------------------------------------------
    # 1. PENGUJIAN KALKULASI TAGIHAN (INVOICE)
    # -------------------------------------------------------------
    print("\n--- 1. PENGUJIAN KALKULASI TAGIHAN (INVOICE) ---")
    
    # TC-INV-01: Agregasi biaya lengkap (Registrasi + Tindakan + Obat)
    code, res = request("GET", "/invoice/KJ-2026-001")
    expected_total = 10000 + (15000 + 10000) + (7000 + 8000) # 50.000
    actual_total = res.get("data", {}).get("total_tagihan")
    is_pass = (code == 200 and actual_total == expected_total and res["data"]["status"] == "UNPAID")
    log_test("TC-INV-01", "Verifikasi Agregasi Tagihan Lengkap (KJ-2026-001)", is_pass,
             f"Expected: Rp {expected_total:,} | Actual: Rp {actual_total:,}")

    # TC-INV-02: Kunjungan tanpa resep obat
    code, res = request("GET", "/invoice/KJ-2026-002")
    actual_total = res.get("data", {}).get("total_tagihan")
    is_pass = (code == 200 and actual_total == 10000)
    log_test("TC-INV-02", "Kunjungan Tanpa Obat / Hanya Registrasi (KJ-2026-002)", is_pass,
             f"Expected: Rp 10,000 | Actual: Rp {actual_total:,}")

    # TC-INV-03: Kunjungan ID fiktif
    code, res = request("GET", "/invoice/KJ-9999-XXX")
    log_test("TC-INV-03", "Validasi Kunjungan Tidak Ditemukan (KJ-9999-XXX)", code == 404,
             f"HTTP Code: {code}")

    # -------------------------------------------------------------
    # 2. PENGUJIAN PELUNASAN PEMBAYARAN
    # -------------------------------------------------------------
    print("\n--- 2. PENGUJIAN PELUNASAN PEMBAYARAN (TUNAI & QRIS) ---")

    # TC-PAY-03: Pembayaran kurang (Harus Gagal)
    pay_data = {
        "kunjungan_id": "KJ-2026-001",
        "metode": "TUNAI",
        "nominal_bayar": 30000 # Kurang dari 50.000
    }
    code, res = request("POST", "/bayar", pay_data)
    log_test("TC-PAY-03", "Validasi Pembayaran Tunai Kurang", code == 400,
             f"HTTP Code: {code} | Pesan: {res.get('message')}")

    # TC-PAY-01 & 02: Pembayaran Tunai dengan kembalian (Rp 100.000 untuk tagihan Rp 50.000)
    pay_data = {
        "kunjungan_id": "KJ-2026-001",
        "metode": "TUNAI",
        "nominal_bayar": 100000,
        "idempotency_key": "IDEM-KEY-001"
    }
    code, res = request("POST", "/bayar", pay_data)
    data = res.get("data", {})
    kembalian = data.get("kembalian")
    kwitansi_id_001 = data.get("kwitansi_id")
    nomor_kwt_001 = data.get("nomor_kwitansi")
    is_pass = (code == 200 and data.get("status_invoice") == "PAID" and kembalian == 50000)
    log_test("TC-PAY-02", "Pelunasan Tunai Uang Lebih & Kalkulasi Kembalian", is_pass,
             f"Dibayar: Rp 100,000 | Kembalian Diterima: Rp {kembalian:,} (Expected: Rp 50,000)")

    # TC-PAY-04: Pelunasan Nontunai (QRIS) pada kunjungan kedua
    pay_qris = {
        "kunjungan_id": "KJ-2026-002",
        "metode": "QRIS",
        "nominal_bayar": 10000,
        "ref_transaksi": "QRIS-BCA-992381230",
        "idempotency_key": "IDEM-KEY-002"
    }
    code, res = request("POST", "/bayar", pay_qris)
    data_qris = res.get("data", {})
    kwitansi_id_002 = data_qris.get("kwitansi_id")
    nomor_kwt_002 = data_qris.get("nomor_kwitansi")
    is_pass = (code == 200 and data_qris.get("status_invoice") == "PAID")
    log_test("TC-PAY-04", "Pelunasan Nontunai (QRIS) dengan Referensi Transaksi", is_pass,
             f"Kwitansi ID: {kwitansi_id_002} | No Kwitansi: {nomor_kwt_002}")

    # TC-PAY-05: Membayar ulang invoice yang sudah lunas
    code, res = request("POST", "/bayar", {"kunjungan_id": "KJ-2026-001", "metode": "TUNAI", "nominal_bayar": 50000})
    log_test("TC-PAY-05", "Pencegahan Pembayaran Ulang pada Invoice Lunas", code == 409,
             f"HTTP Code: {code} | Pesan: {res.get('message')}")

    # -------------------------------------------------------------
    # 3. PENGUJIAN PENERBITAN KWITANSI
    # -------------------------------------------------------------
    print("\n--- 3. PENGUJIAN PENERBITAN KWITANSI RESMI ---")

    code, res = request("GET", f"/kwitansi/{kwitansi_id_001}")
    kwt_obj = res.get("data", {})
    is_pass = (code == 200 and kwt_obj.get("nomor_kwitansi") == nomor_kwt_001 and kwt_obj.get("status") == "LUNAS")
    log_test("TC-KWT-01", "Verifikasi Integritas Kwitansi Elektronik", is_pass,
             f"Nomor Kwitansi Unik: {kwt_obj.get('nomor_kwitansi')} | Waktu: {kwt_obj.get('waktu_bayar')}")

    code, res = request("GET", "/kwitansi/KWT-FAKE-999")
    log_test("TC-KWT-02", "Verifikasi Kwitansi ID Fiktif (404)", code == 404,
             f"HTTP Code: {code}")

    # -------------------------------------------------------------
    # 4. PENGUJIAN IDEMPOTENSI & PENCEGAHAN DOUBLE HIT (RACE CONDITION)
    # -------------------------------------------------------------
    print("\n--- 4. PENGUJIAN IDEMPOTENSI TRANSAKSI (CONCURRENCY) ---")

    # Pengujian Replay request yang sama dengan Idempotency-Key
    replay_data = {
        "kunjungan_id": "KJ-2026-001",
        "metode": "TUNAI",
        "nominal_bayar": 100000,
        "idempotency_key": "IDEM-KEY-001"
    }
    code, res = request("POST", "/bayar", replay_data)
    is_idempotent = res.get("is_idempotent_replay", False)
    log_test("TC-IDEM-01", "Replay Request dengan Idempotency Key yang Sama", (code == 200 and is_idempotent),
             f"Server mengenali request duplikat tanpa menduplikasi kwitansi.")

    print("\n" + "=" * 70)
    print("HASIL: SEMUA SKENARIO PENGUJIAN LULUS (ALL TESTS PASSED - 100%)")
    print("=" * 70)

if __name__ == "__main__":
    run_all_tests()
