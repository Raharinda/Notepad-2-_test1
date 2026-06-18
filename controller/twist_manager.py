import random
import time


class TwistManager:
    """
    Single source of truth untuk state game.
    Twist berjalan looping selamanya — setiap kali satu twist selesai,
    twist baru (full random, boleh berulang) dan trigger point baru
    (random) langsung disiapkan.
    
    Adaptive Difficulty:
    - Difficulty naik saat player win streak meningkat + completion time cepat.
    - Difficulty reset ke base saat gagal 3x berturut-turut.
    - Current difficulty dipass ke twist untuk scaling internal.
    """

    AVAILABLE_TWISTS = [
        "Lavaloon",
        "Self Aware Calculator",
        "Broken Calculator",
        "Teleporting Button",
        "Bloodmoon",
        "Capslock Demon",
        "Black Hole",
    ]

    OBJECTIVES = {
        "Lavaloon": (
            "Hold the button until the progress bar is full.\n"
            "Don't let it touch you!"
        ),
        "Self Aware Calculator": "Solve the multiplication problem.",
        "Broken Calculator": "Solve the division problem.",
        "Teleporting Button": "Click the button.",
        "Bloodmoon": "Survive the Bloodmoon.",
        "Capslock Demon": "Type the sentence correctly.",
        "Black Hole": (
            "Reach the finish line before the singularity consumes everything.\n"
            "Your cursor is your joystick."
        ),
    }

    # Range jarak antar trigger (dalam jumlah karakter tambahan dari trigger sebelumnya)
    TRIGGER_GAP_MIN = 85
    TRIGGER_GAP_MAX = 250

    def __init__(self):
        self.completed_twists: int = 0

        self._current_twist: str = random.choice(self.AVAILABLE_TWISTS)
        self._base_trigger_count: int = 0
        self._next_trigger_point: int = self._roll_trigger_point(base=0)

        # Adaptive difficulty state
        self._current_difficulty: int = 0
        self._win_streak: int = 0
        self._fail_count: int = 0
        self._twist_start_time: float = time.time()

        print(f"[TwistManager] Twist pertama: {self._current_twist}")
        print(f"[TwistManager] Trigger point: {self._next_trigger_point}")
        print(f"[TwistManager] Difficulty: {self._current_difficulty}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _roll_trigger_point(self, base: int) -> int:
        gap = random.randint(self.TRIGGER_GAP_MIN, self.TRIGGER_GAP_MAX)
        return base + gap

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_current_twist(self) -> str:
        return self._current_twist

    def get_current_objective(self) -> str:
        return self.OBJECTIVES.get(self._current_twist, "")

    def get_trigger_progress(self, character_count: int) -> tuple[int, int]:
        progress = max(0, character_count - self._base_trigger_count)
        target = max(0, self._next_trigger_point - self._base_trigger_count)
        return progress, target

    def should_trigger_twist(self, character_count: int) -> bool:
        return character_count >= self._next_trigger_point

    def get_difficulty(self) -> int:
        """Current difficulty level untuk twist scaling."""
        return self._current_difficulty

    def get_difficulty_display(self) -> str:
        """Display string untuk UI (e.g., '🔥🔥🔥')."""
        if self._current_difficulty == 0:
            return "Normal"
        elif self._current_difficulty == 1:
            return "Hard 🔥"
        elif self._current_difficulty == 2:
            return "Harder 🔥🔥"
        else:
            return f"Insane 🔥🔥🔥 (×{self._current_difficulty})"

    # ------------------------------------------------------------------
    # State mutation
    # ------------------------------------------------------------------

    def complete_current_twist(self, character_count: int = 0) -> None:
        """
        Dipanggil saat twist selesai. Update win streak & difficulty,
        lalu siapkan twist & trigger point berikutnya.
        """
        self.completed_twists += 1
        self._base_trigger_count = character_count
        self._fail_count = 0  # Reset fail count on success

        # Calculate completion time (untuk adaptive scaling)
        completion_time = time.time() - self._twist_start_time

        # Update win streak & difficulty
        self._win_streak += 1
        if completion_time < 8.0 and self._win_streak >= 2:
            # Kecepatan + win streak → naik difficulty
            self._current_difficulty = min(self._current_difficulty + 1, 5)
            print(f"[TwistManager] ⬆️ Difficulty naik! Streak: {self._win_streak}, Time: {completion_time:.1f}s")
        elif self._win_streak >= 3:
            # 3 kali menang → naik difficulty
            self._current_difficulty = min(self._current_difficulty + 1, 5)
            print(f"[TwistManager] ⬆️ Difficulty naik! Win streak: {self._win_streak}")

        # Siapkan twist berikutnya
        self._current_twist = random.choice(self.AVAILABLE_TWISTS)
        self._next_trigger_point = self._roll_trigger_point(base=character_count)
        self._twist_start_time = time.time()

        print(f"[TwistManager] Twist selesai. Total: {self.completed_twists}")
        print(f"[TwistManager] Win streak: {self._win_streak}, Difficulty: {self._current_difficulty}")
        print(f"[TwistManager] Twist berikutnya: {self._current_twist}")
        print(f"[TwistManager] Trigger point: {self._next_trigger_point}")

    def fail_current_twist(self, character_count: int = 0) -> bool:
        """
        Dipanggil saat twist gagal. Increment fail counter.
        Return True jika harus reset difficulty (fail 3x).
        """
        self._fail_count += 1
        self._win_streak = 0

        should_reset = self._fail_count >= 3
        if should_reset:
            self._current_difficulty = 0
            self._fail_count = 0
            print(f"[TwistManager] ⬇️ Difficulty reset ke normal (3x gagal)")
        else:
            print(f"[TwistManager] ❌ Gagal. Fail count: {self._fail_count}/3")

        return should_reset

    def start_twist_timer(self) -> None:
        """Mulai timer untuk tracking completion time."""
        self._twist_start_time = time.time()
