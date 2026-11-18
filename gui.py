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
        self.build_case_tab()

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

    def build_case_tab(self):
        """Create the Case tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Case")
        ttk.Button(tab, text="New case...", command=self.new_case).pack(
            anchor="w", padx=10, pady=10)
        self.case_info = tk.Text(tab, height=12, state="disabled")
        self.case_info.pack(fill="both", expand=True, padx=10, pady=10)
        self.refreshers.append(self.refresh_case_tab)

    def refresh_case_tab(self):
        """Update the header and the case details text."""
        if self.case is None:
            self.header.config(text="No case open")
            text = "Create a new case or open a saved one from the File menu."
        else:
            case = self.case
            self.header.config(text=f"Case {case.case_id}: {case.title}")
            text = (f"Case ID: {case.case_id}\nTitle: {case.title}\n"
                    f"Investigator: {case.investigator}\nCreated: {case.created_at}\n"
                    f"Evidence items: {len(case.evidence)}\n"
                    f"Custody entries: {len(case.custody_log)}\n"
                    f"Timeline events: {len(case.events)}")
        self.case_info.config(state="normal")
        self.case_info.delete("1.0", tk.END)
        self.case_info.insert("1.0", text)
        self.case_info.config(state="disabled")

    @guarded
    def new_case(self):
        """Ask for case details and create a case."""
        case_id = simpledialog.askstring("New case", "Case ID:", parent=self.root)
        if case_id is None:
            return
        title = simpledialog.askstring("New case", "Title:", parent=self.root)
        if title is None:
            return
        investigator = simpledialog.askstring("New case", "Investigator:", parent=self.root)
        if investigator is None:
            return
        self.case = case_manager.create_case(case_id, title, investigator)
        self.case_path = None
        self.filtered = False
        self.refresh_all()
        self.set_status(f"Created case {self.case.case_id}.")
    
    # ===== NEW METHODS GO ABOVE THIS LINE =====


def main():
    """Start the application."""
    root = tk.Tk()
    VaultApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
