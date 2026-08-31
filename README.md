# Credit Digitalization

Aplikasi Django sederhana untuk digitalisasi pengajuan kredit kendaraan.

## Fitur

- Input lead/dealer, konsumen, kendaraan, dan pinjaman
- Consent pemrosesan data konsumen
- Upload KTP, KK, bukti tanda jadi, dan form aplikasi
- Completeness gate sebelum submit
- Role-based access untuk **Marketing** dan **Atasan Marketing**
- Pemisahan maker–checker
- Approval atau reject beserta alasan penolakan
- Audit trail setiap perubahan status
- Dokumen hanya dapat diunduh oleh user yang berhak
- Daftar pengajuan sederhana

## Menjalankan aplikasi

```powershell
.\env\Scripts\Activate.ps1
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Buka `http://127.0.0.1:8000/`.

| Role             | Username          | Password     |
| ---------------- | ----------------- | ------------ |
| Marketing        | `marketing_demo`  | `Demo12345!` |
| Atasan Marketing | `supervisor_demo` | `Demo12345!` |

Password hanya diset saat akun demo pertama kali dibuat.
