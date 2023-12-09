"""Main module for the application."""
from tkinter import Tk

from gui import AppGUI


def main():
    """Main function for the application."""
    root = Tk()
    AppGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
