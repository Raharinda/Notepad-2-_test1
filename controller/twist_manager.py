import random


class TwistManager:
    """
    Single source of truth untuk state game.
    Menggantikan GameController + GameModel yang sebelumnya redundant.
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

    # Berapa twist yang harus diselesaikan dalam satu sesi
    REQUIRED_TWISTS = 3

    def __init__(self):
        self.selected_twists: list[str] = random.sample(
            self.AVAILABLE_TWISTS, self.REQUIRED_TWISTS
        )
        self.completed_twists: int = 0

        # Trigger threshold (jumlah karakter) — disembunyikan dari console di produksi
        self._trigger_points: list[int] = [
            random.randint(85, 100),
            random.randint(200, 250),
            random.randint(399, 500),
        ]

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_current_twist(self) -> str | None:
        """Nama twist yang sedang aktif, atau None jika semua sudah selesai."""
        if self.completed_twists < len(self.selected_twists):
            return self.selected_twists[self.completed_twists]
        return None

    def get_current_objective(self) -> str:
        twist = self.get_current_twist()
        return self.OBJECTIVES.get(twist, "")

    def all_completed(self) -> bool:
        return self.completed_twists >= self.REQUIRED_TWISTS

    def should_trigger_twist(self, character_count: int) -> bool:
        if self.all_completed():
            return False
        next_trigger = self._trigger_points[self.completed_twists]
        return character_count >= next_trigger

    # ------------------------------------------------------------------
    # State mutation
    # ------------------------------------------------------------------

    def complete_current_twist(self) -> None:
        self.completed_twists += 1

