import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from src.app import App


def main():
    root = tk.Tk()
    root.withdraw()
    app = App(root)
    root.deiconify()
    root.mainloop()


if __name__ == '__main__':
    main()