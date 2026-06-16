import tkinter as tk
from dotenv import load_dotenv

load_dotenv()

from view.main_view import MainView
from controller.twist_manager import TwistManager


def main():
    root = tk.Tk()
    manager = TwistManager()
    MainView(root, manager)
    root.mainloop()


if __name__ == "__main__":
    main()

