# I acknowledge the use of Claude (Anthropic, https://claude.ai) to review the code in this file.

"""Tkinter (GUI) version of the Evidence Vault.

This file only builds windows and calls the core package. It holds no
business logic, so it offers the same features as cli.py.
"""

import functools
import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from core import case_manager, chain, report, search, storage, timeline
from core.errors import VaultError


def guarded(method):
    """Show a message box instead of crashing when a VaultError happens."""

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except VaultError as err:
            messagebox.showerror("Problem", str(err))
            self.set_status(f"Error: {err}")
        return None

    return wrapper


class VaultApp:
    """The main window."""

    def __init__(self, root):
        self.root = root
        self.case = None
        self.case_path = None
        self.refreshers = []
        self.filtered = False
        self.view_events = []
        self.searcher = search.TimelineSearcher()
        root.title("Evidence Vault")
        root.geometry("1100x650")
        self.menubar = tk.Menu(root)
        root.config(menu=self.menubar)
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Exit", command=root.destroy)
        self.top = ttk.Frame(root)
        self.top.pack(fill="x", padx=10, pady=5)
        self.header = ttk.Label(
            self.top, text="No case open", font=("Arial", 12, "bold")
        )
        self.header.pack(side="left")
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        self.status = ttk.Label(root, text="Ready", anchor="w")
        self.status.pack(fill="x", padx=10, pady=5)
        # --- NEW PANEL CALLS GO BELOW THIS LINE ---

    def set_status(self, text):
        """Show a message in the bottom bar."""
        self.status.config(text=text)

    def refresh_all(self):
        """Redraw every panel that has registered itself."""
        for refresh in self.refreshers:
            refresh()

    def require_case(self):
        """Return the open case or raise an error."""
        if self.case is None:
            raise VaultError("No case is open. Create or open a case first.")
        return self.case

    # ===== NEW METHODS GO ABOVE THIS LINE =====


def main():
    """Start the application."""
    root = tk.Tk()
    VaultApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
