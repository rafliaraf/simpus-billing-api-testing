import http.server
import json
import re
import threading
import time
import uuid
from urllib.parse import urlparse

# Database Simulasi In-Memory
DATABASE = {
    "kunjungan": {
        "KJ-2026-001": {
            "id": "KJ-2026-001",
            "pasien_nama": "Budi Santoso",
            "nik": "3201234567890001",
            "poli": "Poli Umum",
            "biaya_registrasi": 10000,
            "tindakan": [
                {"kode": "T01", "nama": "Pemeriksaan Dokter & Tensi", "tarif": 15000},
                {"kode": "T02", "nama": "Pembersihan Luka Ringan", "tarif": 10000}
            ],
            "obat": [
                {"kode": "OB01", "nama": "Paracetamol 500mg (10 tab)", "harga": 7000, "qty": 1},
                {"kode": "OB02", "nama": "Amoxicillin 500mg (10 tab)", "harga": 8000, "qty": 1}
            ],
            "status": "UNPAID"
        },
        "KJ-2026-002": {
            "id": "KJ-2026-002",
            "pasien_nama": "Siti Rahma",
            "nik": "3201234567890002",
            "poli": "Poli Gigi",
            "biaya_registrasi": 10000,
            "tindakan": [],
            "obat": [],
            "status": "UNPAID"
        }
    },
    "invoices": {},
    "pembayaran": {},
    "kwitansi": {},
    "processed_idempotency_keys": {}
}

# Generate Initial Invoices
for k_id, k_data in DATABASE["kunjungan"].items():
    total_reg = k_data["biaya_registrasi"]
    total_tindakan = sum(t["tarif"] for t in k_data["tindakan"])
    total_obat = sum(o["harga"] * o["qty"] for o in k_data["obat"])
    grand_total = total_reg + total_tindakan + total_obat

    inv_id = f"INV-{k_id}"
    DATABASE["invoices"][k_id] = {
        "invoice_id": inv_id,
        "kunjungan_id": k_id,
        "pasien_nama": k_data["pasien_nama"],
        "nik": k_data["nik"],
        "poli": k_data["poli"],
        "rincian": {
            "biaya_registrasi": total_reg,
            "tindakan": k_data["tindakan"],
            "subtotal_tindakan": total_tindakan,
            "obat": k_data["obat"],
            "subtotal_obat": total_obat
        },
        "total_tagihan": grand_total,
        "status": "UNPAID",
        "kwitansi_id": None
    }

lock = threading.Lock()
kwitansi_counter = 1

class PuskesmasBillingHandler(http.server.BaseHTTPRequestHandler):
    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Idempotency-Key")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def do_OPTIONS(self):
        self._send_json(200, {"status": "ok"})

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 1. Endpoint Kalkulasi Invoice: GET /api/v1/billing/invoice/{kunjungan_id}
        m_inv = re.match(r"^/api/v1/billing/invoice/([^/]+)$", path)
        if m_inv:
            kunjungan_id = m_inv.group(1)
            invoice = DATABASE["invoices"].get(kunjungan_id)
            if not invoice:
                self._send_json(404, {
                    "success": False,
                    "message": f"Data kunjungan '{kunjungan_id}' tidak ditemukan"
                })
                return
            self._send_json(200, {
                "success": True,
                "data": invoice
            })
            return

        # 3. Endpoint Cetak Kwitansi: GET /api/v1/billing/kwitansi/{id}
        m_kwt = re.match(r"^/api/v1/billing/kwitansi/([^/]+)$", path)
        if m_kwt:
            kwitansi_id = m_kwt.group(1)
            kwitansi = DATABASE["kwitansi"].get(kwitansi_id)
            if not kwitansi:
                self._send_json(404, {
                    "success": False,
                    "message": f"Kwitansi dengan ID '{kwitansi_id}' tidak ditemukan"
                })
                return
            self._send_json(200, {
                "success": True,
                "data": kwitansi
            })
            return

        self._send_json(404, {"success": False, "message": "Endpoint tidak ditemukan"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 2 & 4. Endpoint Pelunasan & Idempotensi: POST /api/v1/billing/bayar
        if path == "/api/v1/billing/bayar":
            content_length = int(self.headers.get("Content-Length", 0))
            body_str = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
            try:
                body = json.loads(body_str)
            except Exception:
                self._send_json(400, {"success": False, "message": "Invalid JSON Body"})
                return

            kunjungan_id = body.get("kunjungan_id")
            metode = body.get("metode", "").upper()
            nominal_bayar = body.get("nominal_bayar", 0)
            ref_transaksi = body.get("ref_transaksi")
            idempotency_key = self.headers.get("Idempotency-Key") or body.get("idempotency_key")

            if not kunjungan_id or not metode:
                self._send_json(400, {"success": False, "message": "kunjungan_id dan metode wajib diisi"})
                return

            if metode not in ["TUNAI", "QRIS"]:
                self._send_json(400, {"success": False, "message": "Metode pembayaran harus TUNAI atau QRIS"})
                return

            # CRITICAL SECTION - Menguji Idempotensi & Concurrency
            with lock:
                # Cek Idempotency Cache
                if idempotency_key and idempotency_key in DATABASE["processed_idempotency_keys"]:
                    cached_response = DATABASE["processed_idempotency_keys"][idempotency_key]
                    self._send_json(200, {
                        "success": True,
                        "is_idempotent_replay": True,
                        "message": "Transaksi sudah diproses sebelumnya (Idempotent response)",
                        "data": cached_response
                    })
                    return

                invoice = DATABASE["invoices"].get(kunjungan_id)
                if not invoice:
                    self._send_json(404, {"success": False, "message": "Invoice tidak ditemukan"})
                    return

                if invoice["status"] == "PAID":
                    self._send_json(409, {
                        "success": False,
                        "message": "Invoice ini sudah lunas sebelumnya!",
                        "kwitansi_id": invoice.get("kwitansi_id")
                    })
                    return

                total_tagihan = invoice["total_tagihan"]

                if nominal_bayar < total_tagihan:
                    self._send_json(400, {
                        "success": False,
                        "message": f"Nominal pembayaran kurang. Tagihan: Rp {total_tagihan:,}, Dibayar: Rp {nominal_bayar:,}"
                    })
                    return

                kembalian = nominal_bayar - total_tagihan if metode == "TUNAI" else 0

                # Generate Nomor Kwitansi Unik Resmi
                global kwitansi_counter
                nomor_kwitansi = f"KWT/PKM/{time.strftime('%Y%m')}/{kwitansi_counter:04d}"
                kwitansi_counter += 1
                kwitansi_id = str(uuid.uuid4())[:8]

                kwitansi_data = {
                    "kwitansi_id": kwitansi_id,
                    "nomor_kwitansi": nomor_kwitansi,
                    "invoice_id": invoice["invoice_id"],
                    "kunjungan_id": kunjungan_id,
                    "pasien_nama": invoice["pasien_nama"],
                    "nik": invoice["nik"],
                    "poli": invoice["poli"],
                    "total_tagihan": total_tagihan,
                    "metode_bayar": metode,
                    "nominal_bayar": nominal_bayar,
                    "kembalian": kembalian,
                    "ref_transaksi": ref_transaksi if metode == "QRIS" else "-",
                    "status": "LUNAS",
                    "kasir": "Kasir Loket 1 (Petugas Diskominfo)",
                    "waktu_bayar": time.strftime("%Y-%m-%d %H:%M:%S")
                }

                # Update Status Invoice
                invoice["status"] = "PAID"
                invoice["kwitansi_id"] = kwitansi_id

                DATABASE["kwitansi"][kwitansi_id] = kwitansi_data

                result_data = {
                    "status_invoice": "PAID",
                    "total_tagihan": total_tagihan,
                    "nominal_bayar": nominal_bayar,
                    "kembalian": kembalian,
                    "kwitansi_id": kwitansi_id,
                    "nomor_kwitansi": nomor_kwitansi,
                    "waktu_bayar": kwitansi_data["waktu_bayar"]
                }

                if idempotency_key:
                    DATABASE["processed_idempotency_keys"][idempotency_key] = result_data

                self._send_json(200, {
                    "success": True,
                    "message": "Pembayaran berhasil diterima dan kwitansi diterbitkan.",
                    "data": result_data
                })
                return

        self._send_json(404, {"success": False, "message": "Endpoint tidak ditemukan"})

def run_server(port=8080):
    server = http.server.HTTPServer(("127.0.0.1", port), PuskesmasBillingHandler)
    print(f"Mock Server Puskesmas Billing aktif di http://127.0.0.1:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
