# Product Requirements Document (PRD)
## Trolling Notepad

**Versi Dokumen:** 1.0
**Tujuan Dokumen:** Panduan pengembangan lanjutan (penambahan fitur baru, twist baru, perbaikan arsitektur)

---

## 1. Latar Belakang & Konsep Produk

Trolling Notepad adalah aplikasi desktop berbasis Tkinter yang menyamar sebagai aplikasi notepad biasa. Saat pengguna mengetik, secara diam-diam aplikasi memantau jumlah karakter yang diketik. Pada titik-titik tertentu (tersembunyi/acak), aplikasi memicu sebuah "twist" — mini-game atau gangguan interaktif yang harus diselesaikan pengguna sebelum bisa melanjutkan mengetik.

Tujuan akhir pengguna adalah menyelesaikan 3 twist (dipilih secara acak dari 7 twist yang tersedia) untuk mencapai "Victory Screen".

### Target Pengguna
- Pengguna yang ingin pengalaman hiburan/troll ringan saat menggunakan notepad
- Komunitas yang menyukai game "jumpscare ringan" / parody software

---

## 2. Arsitektur Saat Ini

Project mengikuti pola **MVC (Model-View-Controller)**:

```
├── main.py                     # Entry point
├── controller/
│   ├── game_controller.py      # (belum terpakai aktif, sample 3 twist)
│   └── twist_manager.py        # Mengatur state game: trigger, progres, objective
├── model/
│   ├── game_model.py           # State global game (belum terintegrasi penuh)
│   └── twist_model.py          # Model dasar twist (name, objective, completed)
├── view/
│   └── main_view.py            # UI utama notepad + overlay + orchestrasi twist
└── twists/
    ├── base_twist.py           # Kelas dasar twist (extends TwistModel)
    ├── teleport_button.py
    ├── bloodmoon.py
    ├── capslock_demon.py
    ├── self_aware_calculator.py
    ├── broken_calculator.py
    ├── lavaloon.py
    └── black_hole.py
```

### Alur Utama (Flow)
1. `main.py` membuat `TwistManager` → memilih 3 twist acak dari 7 yang tersedia, menentukan 3 trigger point (jumlah karakter) secara acak.
2. `MainView` menampilkan text area notepad. Setiap `KeyRelease`, `on_text_changed` mengecek jumlah karakter.
3. Jika jumlah karakter ≥ trigger point berikutnya → `trigger_twist()` dipanggil.
4. Overlay peringatan (judul twist + objective) muncul selama 2 detik.
5. Setelah itu, `fake_twist()` menginisialisasi twist sesuai nama (if-elif chain).
6. Twist berjalan; saat selesai, memanggil `finish_callback` (`finish_twist`).
7. `finish_twist()` menambah counter `completed_twists`, update status bar, sembunyikan overlay.
8. Jika `completed_twists >= 3` → tampilkan Victory Screen.
9. Beberapa twist (Lavaloon, Black Hole) memiliki mekanisme `retry_callback` jika pemain gagal/"mati".

---

## 3. Fitur Saat Ini (Existing Features)

### 3.1 Core Loop
| Fitur | Deskripsi | Status |
|---|---|---|
| Notepad area | Text area dasar dengan font Consolas | ✅ Implemented |
| Character counter trigger | Memantau jumlah karakter, memicu twist pada threshold acak | ✅ Implemented |
| Warning overlay | Overlay 2 detik sebelum twist dimulai, menampilkan nama & objective | ✅ Implemented |
| Status bar progres | Menampilkan "Twists Completed: x/3" | ✅ Implemented |
| Victory screen | Layar selesai setelah 3 twist tuntas, dengan opsi Continue/Close | ✅ Implemented |

### 3.2 Daftar Twist
| Nama Twist | Tipe | Objective | Mekanisme Retry |
|---|---|---|---|
| Teleporting Button | Klik | Klik tombol yang berpindah-pindah (15-20x) | Tidak |
| Bloodmoon | Pasif/Ambient | Survive 15 detik dengan tema visual berubah & pesan acak | Tidak |
| Capslock Demon | Mengetik | Ketik ulang kalimat dengan capslock yang toggle otomatis tiap 1 detik | Tidak |
| Self Aware Calculator | Kalkulasi | Selesaikan soal perkalian, kalkulator "meroasting" user | Tidak |
| Broken Calculator | Kalkulasi | Selesaikan soal pembagian, tombol kalkulator teracak setiap input | Tidak |
| Lavaloon | Skill/Reaksi | Hindari bola merah yang mengejar kursor, tahan tombol "HOLD HERE" hingga progress bar penuh, 3 nyawa | Ya (tekan R) |
| Black Hole | Skill/Reaksi | Gerakkan player ke garis finish, hindari black hole yang membesar | Ya (tekan R) |

---

## 4. Masalah & Catatan Teknis (Technical Debt)

Bagian ini penting untuk dev lanjutan agar tidak menambah fitur di atas fondasi yang rapuh.

1. **`fake_twist()` menggunakan if-elif chain berbasis string nama twist** — tidak scalable. Setiap twist baru menambah satu blok elif di `main_view.py`. **Rekomendasi:** gunakan registry/dictionary mapping `nama_twist -> class`.
2. **`GameController` (controller/game_controller.py) dan `GameModel` (model/game_model.py) tidak terpakai** dalam flow utama — duplikasi logika dengan `TwistManager`. Perlu konsolidasi: tentukan satu sumber kebenaran (single source of truth) untuk state game.
3. **`BaseTwist` (extends `TwistModel`) tidak digunakan oleh twist manapun** — semua twist class adalah class mandiri tanpa pewarisan. Jika ingin konsistensi (misalnya untuk fitur "Skip Twist" atau "Pause"), semua twist harus diseragamkan untuk extend `BaseTwist`.
4. **Penggunaan `eval()`** pada `broken_calculator.py` dan `self_aware_calculator.py` — risiko keamanan meski input terbatas dari tombol kalkulator sendiri (low risk, tapi sebaiknya diganti dengan parser aman jika ada rencana menerima input bebas).
5. **Trigger point dicetak ke console** (`print("Trigger Points:", ...)`) — harus dihapus/disembunyikan di build produksi karena membocorkan "jawaban" twist trigger.
6. **Tidak ada penanganan exit/quit yang bersih** saat overlay aktif — `close_session` hanya `root.destroy()`.
7. **Overlay frame di-reuse untuk semua twist** tanpa reset state konsisten — beberapa twist melakukan `widget.destroy()` manual, rawan memory leak `after()` job yang belum di-cancel (contoh: `toggle_job`, `message_job` sudah di-handle, tapi tidak semua twist konsisten).
8. **Tidak ada sistem save/load** — progres hilang jika aplikasi ditutup.
9. **Tidak ada test otomatis** sama sekali.

---

## 5. Rencana Fitur Baru (Proposed Features untuk Dev Lanjutan)

### 5.1 Prioritas Tinggi
| Fitur | Deskripsi | Estimasi Kompleksitas |
|---|---|---|
| **Twist Registry** | Refactor `fake_twist()` menjadi dictionary `{twist_name: TwistClass}` agar penambahan twist baru tidak perlu ubah `main_view.py` | Sedang |
| **Difficulty Settings** | Tambah level kesulitan (Easy/Normal/Hard) yang mempengaruhi `trigger_points` range dan parameter twist (misal jumlah teleport, durasi bloodmoon) | Sedang |
| **Sound Effects** | Tambah audio jumpscare/ambient saat warning overlay & saat twist tertentu aktif (gunakan `pygame.mixer` atau `playsound`) | Sedang |
| **Save Progress** | Simpan teks notepad + state game (twist mana yang sudah selesai) ke file lokal, agar bisa resume | Sedang-Tinggi |

### 5.2 Prioritas Menengah
| Fitur | Deskripsi |
|---|---|
| **Twist Baru: "Ghost Cursor"** | Kursor mouse pengguna "tertukar" dengan kursor hantu yang bergerak independen, user harus mengetik teks tertentu menggunakan keyboard navigation saja |
| **Twist Baru: "File Corruption"** | Simulasi file "corrupt" — teks pengguna berubah menjadi karakter acak secara bertahap, user harus mengetik ulang sebelum waktu habis |
| **Animasi Transisi** | Tambahkan fade in/out pada overlay alih-alih `place`/`place_forget` instan |
| **Statistik Akhir Permainan** | Victory screen menampilkan waktu total, jumlah retry, twist yang dimainkan |
| **Tema Visual Selectable** | Pilihan tema notepad (Dark/Light/Classic Windows) sebelum game mulai |

### 5.3 Prioritas Rendah (Nice to Have)
| Fitur | Deskripsi |
|---|---|
| **Leaderboard Lokal** | Simpan waktu tercepat menyelesaikan 3 twist |
| **Custom Twist Pool** | User bisa pilih twist mana saja yang ingin diaktifkan dari menu settings |
| **Easter Egg Tambahan** | Twist rahasia ke-8 yang hanya muncul dengan probabilitas kecil |
| **Multi-language Objective Text** | Dukungan bahasa Indonesia/Inggris untuk teks objective & UI |

---

## 6. Persyaratan Non-Fungsional

| Aspek | Persyaratan |
|---|---|
| **Platform** | Windows, macOS, Linux (Tkinter cross-platform) |
| **Performance** | Loop `after()` pada twist (Lavaloon, Black Hole) harus tetap responsif (≤16ms per frame) tanpa freeze UI |
| **Maintainability** | Setiap twist baru wajib mengikuti kontrak: konstruktor menerima `overlay_frame` (atau `main_view` untuk twist yang mengubah UI utama) + `finish_callback`, opsional `retry_callback` |
| **Resource Cleanup** | Setiap twist wajib membersihkan widget overlay dan membatalkan semua `after()` job sebelum memanggil `finish_callback`/`retry_callback` |

---

## 7. Kontrak Twist (Twist Interface Guideline)

Untuk pengembang yang menambah twist baru, ikuti kontrak berikut agar kompatibel dengan `TwistManager` dan `MainView`:

```python
class NewTwist:
    def __init__(self, overlay_frame, finish_callback, retry_callback=None):
        # overlay_frame: frame tempat UI twist ditempatkan
        # finish_callback: dipanggil saat twist berhasil diselesaikan
        # retry_callback: dipanggil jika twist memiliki mekanisme gagal/retry
        ...

    # Wajib: bersihkan semua widget di overlay_frame & cancel after() job
    # sebelum memanggil finish_callback()
```

Tambahan langkah saat menambah twist baru:
1. Tambahkan nama twist ke `TwistManager.available_twists`
2. Tambahkan objective di `TwistManager.objectives`
3. Registrasikan class di `fake_twist()` (atau di Twist Registry jika sudah direfactor — lihat 5.1)

---

## 8. Metrik Keberhasilan (untuk validasi fitur baru)

- Tidak ada crash/freeze saat transisi antar twist
- Trigger point twist tidak terlihat oleh user (tidak ada print/log di build final)
- Setiap twist baru dapat diselesaikan dalam waktu wajar (target rata-rata < 60 detik)
- Tidak ada widget/job sisa (`after()`) yang berjalan setelah twist selesai/diganti

---

## 9. Open Questions

- Apakah `GameController` dan `GameModel` akan dipertahankan dan diintegrasikan, atau dihapus karena redundant dengan `TwistManager`?
- Apakah diperlukan menu/settings screen sebelum game dimulai, atau game tetap "langsung jalan" saat aplikasi dibuka?
- Apakah ada batasan jumlah twist maksimum (saat ini hardcoded 3) yang perlu dikonfigurasi?