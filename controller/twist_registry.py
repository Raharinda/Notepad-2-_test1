"""
Twist Registry
==============
Pemetaan nama twist → kelas twist.

Menambah twist baru cukup:
  1. Buat kelas di twists/
  2. Import di sini
  3. Tambah satu baris di REGISTRY
  4. Daftarkan nama + objective di TwistManager

Tidak perlu menyentuh MainView sama sekali.

Semua twist sekarang menerima parameter `difficulty` (int, default 0)
yang dipakai untuk scaling kesulitan internal masing-masing twist.
Nilai ini diisi dari `twist_manager.completed_twists` oleh
TwistOrchestratorMixin — makin banyak twist yang sudah diselesaikan,
makin tinggi nilainya.
"""

from twists.teleport_button import TeleportButtonTwist
from twists.bloodmoon import BloodmoonTwist
from twists.capslock_demon import CapslockDemonTwist
from twists.self_aware_calculator import SelfAwareCalculatorTwist
from twists.broken_calculator import BrokenCalculatorTwist
from twists.lavaloon import LavaloonTwist
from twists.black_hole import BlackHoleTwist

# ---------------------------------------------------------------------------
# Twist yang menerima (overlay_frame, finish_cb, difficulty)
# ---------------------------------------------------------------------------
_OVERLAY_TWISTS: dict[str, type] = {
    "Teleporting Button": TeleportButtonTwist,
    "Capslock Demon": CapslockDemonTwist,
    "Self Aware Calculator": SelfAwareCalculatorTwist,
    "Broken Calculator": BrokenCalculatorTwist,
}

# Twist yang menerima (overlay_frame, finish_cb, retry_cb, difficulty)
_OVERLAY_RETRY_TWISTS: dict[str, type] = {
    "Lavaloon": LavaloonTwist,
    "Black Hole": BlackHoleTwist,
}

# Twist yang menerima (main_view, finish_cb, difficulty) — mengakses UI root langsung
_MAINVIEW_TWISTS: dict[str, type] = {
    "Bloodmoon": BloodmoonTwist,
}


def launch(
    twist_name: str,
    main_view,          # MainView instance
    finish_callback,
    retry_callback,
    difficulty: int = 0,
) -> bool:
    """
    Instantiate dan jalankan twist yang sesuai.

    Returns:
        True  — twist berhasil di-launch
        False — twist tidak dikenali (caller bisa log / skip)
    """
    if twist_name in _OVERLAY_TWISTS:
        _OVERLAY_TWISTS[twist_name](
            main_view.overlay_frame,
            finish_callback,
            difficulty=difficulty,
        )
        return True

    if twist_name in _OVERLAY_RETRY_TWISTS:
        _OVERLAY_RETRY_TWISTS[twist_name](
            main_view.overlay_frame,
            finish_callback,
            retry_callback,
            difficulty=difficulty,
        )
        return True

    if twist_name in _MAINVIEW_TWISTS:
        _MAINVIEW_TWISTS[twist_name](
            main_view,
            finish_callback,
            difficulty=difficulty,
        )
        return True

    return False