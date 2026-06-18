# Adaptive Difficulty System

## Implementasi

Sistem adaptive difficulty telah diimplementasikan untuk semua 7 twists. Difficulty mulai dari **0 (Normal)** dan naik berdasarkan **win streak + completion speed**, dengan **reset ke 0 setelah 3x gagal**.

### Difficulty Levels Display

- **Difficulty 0**: "Normal"
- **Difficulty 1**: "Hard 🔥"
- **Difficulty 2**: "Harder 🔥🔥"
- **Difficulty 3+**: "Insane 🔥🔥🔥 (×N)"

Status bar menampilkan difficulty indicator di sebelah progress bar, update realtime saat twist selesai/gagal.

---

## Controller: TwistManager (`controller/twist_manager.py`)

### Perubahan Utama

1. **Tracking State Adaptif**:
   - `_current_difficulty`: Level kesulitan (0-5+)
   - `_win_streak`: Jumlah kemenangan berturut-turut
   - `_fail_count`: Jumlah kegagalan berturut-turut
   - `_twist_start_time`: Timer untuk tracking completion time

2. **Methods Baru**:
   - `get_difficulty()`: Return difficulty level saat ini
   - `get_difficulty_display()`: Return string display dengan emoji
   - `complete_current_twist()`: Update win streak & calculate difficulty naik
   - `fail_current_twist()`: Track kegagalan, reset ke 0 saat 3x gagal
   - `start_twist_timer()`: Mulai timer tracking

### Logika Difficulty Naik

- **Kondisi 1**: Win streak ≥ 2 + completion time < 8 detik → naik 1 level
- **Kondisi 2**: Win streak ≥ 3 (any time) → naik 1 level
- **Cap maksimal**: Difficulty 5
- **Reset**: Saat fail 3x berturut-turut, difficulty kembali ke 0

---

## View: MainView (`view/main_view.py`)

### Perubahan UI

1. **Status Bar Baru**:
   - Tambah `difficulty_label` di status bar dengan warna orange
   - Display: "Difficulty: [Normal/Hard 🔥/Harder 🔥🔥/Insane...]"

2. **Method Baru**:
   - `update_difficulty_display()`: Update label dengan difficulty saat ini

3. **Initialization**:
   - Call `update_difficulty_display()` di `__init__` untuk initial state

---

## View Components: TwistOrchestrator (`view/components/twist_orchestrator.py`)

### Perubahan Logika

1. **Launch Twist**:
   - Call `twist_manager.start_twist_timer()` untuk mulai tracking waktu
   - Pass `difficulty = twist_manager.get_difficulty()` (bukan `completed_twists`)

2. **Finish Twist** (Win):
   - Call `twist_manager.complete_current_twist(char_count)`
   - Call `update_difficulty_display()` untuk update UI

3. **Retry Twist** (Fail/User Retry):
   - Call `twist_manager.fail_current_twist(char_count)` untuk track kegagalan
   - Kalau 3x gagal (difficulty reset), call `update_difficulty_display()`
   - Show warning overlay lagi sebelum re-launch twist

---

## Twists: Adaptive Scaling

Setiap twist menggunakan `difficulty` parameter untuk scale challenge. Difficulty dipass dari `TwistManager` ke twist constructor.

### 1. **Lavaloon** (`twists/lavaloon.py`)

| Aspect | Scaling |
|--------|---------|
| **Enemy Speed** | `3 + difficulty × 0.6` (cap 8.0) |
| **Lives** | 3 → 2 saat difficulty ≥ 2 |
| **Fill Rate** | `max(0.4, 1.0 - difficulty × 0.08)` (lebih sulit drain progress) |
| **Drain Rate** | `min(0.3 + difficulty × 0.04, 0.7)` (progress menurun lebih cepat) |
| **Clone Interval** | `max(3000ms, 9000ms - difficulty × 800)` (musuh spawn lebih sering) |
| **Button Shift** | Aktif sejak difficulty ≥ 2 (sebelumnya difficulty ≥ 5) |
| **Max Enemies** | `min(5 + difficulty, 10)` (cap musuh lebih tinggi) |

### 2. **Self Aware Calculator** (`twists/self_aware_calculator.py`)

| Aspect | Scaling |
|--------|---------|
| **Number Range** | Difficulty 0: 1000-9999 → Difficulty 1+: 5000-49999 → Difficulty 3+: 10000-99999 → Difficulty 5+: 100000-999999 |
| **Time Limit** | `max(8000ms, 25000ms - difficulty × 1800)` (waktu lebih pendek) |
| **Button Shuffle** | Aktif sejak difficulty ≥ 1 (sebelumnya ≥ 3) |
| **Spicy Roasts** | Aktif sejak difficulty ≥ 1 (sebelumnya ≥ 2) |
| **Idle Taunt Delay** | `max(3500ms, 6000ms - difficulty × 300)` (taunt lebih sering) |

### 3. **Broken Calculator** (`twists/broken_calculator.py`)

| Aspect | Scaling |
|--------|---------|
| **Number Range** | Difficulty 0: (10-200, 10-99) → Difficulty 1+: (50-400, 20-150) → Difficulty 3+: (100-600, 30-200) → Difficulty 5+: (300-1000, 60-250) |
| **Fake Equals Chance** | `min(0.20 + difficulty × 0.08, 0.55)` (fake answer lebih sering) |
| **Idle Taunt Delay** | `max(3000ms, 6500ms - difficulty × 400)` |

### 4. **Teleporting Button** (`twists/teleport_button.py`)

| Aspect | Scaling |
|--------|---------|
| **Clicks Required** | `15-25 + min(difficulty × 3, 25)` (lebih banyak klik) |
| **Button Size** | `max(40px, 110px - difficulty × 8)` (tombol lebih kecil, susah diklik) |
| **Decoy Chance** | `min(0.20 + difficulty × 0.06, 0.65)` (tombol fake lebih sering) |
| **Flee Chance** | `min(0.15 + difficulty × 0.08, 0.75)` (tombol kabur dari cursor) |
| **Auto-jump Timer** | `max(1000ms, 3000ms - difficulty × 200)` (tombol pindah sendiri lebih cepat) |

### 5. **Bloodmoon** (`twists/bloodmoon.py`)

| Aspect | Scaling |
|--------|---------|
| **Duration** | `min(12000ms + difficulty × 2000, 35000ms)` (bertahan lebih lama) |
| **Silence Tolerance** | `max(1500ms, 4500ms - difficulty × 300)` (diam sedikit langsung dihukum) |
| **Message Interval** | `max(800ms, 3000ms - difficulty × 200)` (pesan lebih sering) |
| **New Messages** | Difficulty tinggi tambah 2 pesan lebih seram |

### 6. **Capslock Demon** (`twists/capslock_demon.py`)

| Aspect | Scaling |
|--------|---------|
| **Toggle Interval** | `max(300ms, 1000ms - difficulty × 120)` (capslock toggle lebih cepat) |
| **Jitter** | `min(100ms + difficulty × 50, 400ms)` (timing kurang konsisten) |
| **Hard Sentences** | Aktif sejak difficulty ≥ 2 (sebelumnya ≥ 3) |
| **Double Toggle** | Aktif sejak difficulty ≥ 2 (sebelumnya ≥ 4) dengan chance `min(0.05 + difficulty × 0.06, 0.5)` |

### 7. **Black Hole** (`twists/black_hole.py`)

| Aspect | Scaling |
|--------|---------|
| **Growth Rate** | `min(0.60 + difficulty × 0.10, 1.4)` (black hole membesar lebih cepat) |
| **Gravity Pull** | `0.0 (difficulty < 1) → min(0.020 + difficulty × 0.007, 0.08)` (player ditarik lebih kuat) |
| **Spawn Distance** | `min(100px + difficulty × 15px, 220px)` (spawn lebih dekat dengan black hole) |

---

## Testing Checklist

- [x] Syntax check: semua files compile tanpa error
- [ ] Runtime test: jalankan app dan trigger twist pertama (difficulty 0)
- [ ] Win first twist: check bahwa difficulty naik atau tetap sesuai win streak
- [ ] Fail 3x twist yang sama: check bahwa difficulty reset ke 0
- [ ] UI update: check bahwa difficulty indicator update di status bar
- [ ] All 7 twists: verify setiap twist merespons difficulty dengan benar

---

## Notes

- Semua scaling values dirancang supaya tetap **winnable** tapi **challenging**
- Difficulty cap 5 mencegah game menjadi impossible
- Reset policy (fail 3x) memberikan pemain kesempatan recovery
- Win streak + speed tracking membuat progression terasa natural & rewarding
