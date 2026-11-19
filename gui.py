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
        self.build_evidence_tab()
        self.build_timeline_tab()
        self.build_integrity_widgets()
        self.build_custody_tab()

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
            anchor="w", padx=10, pady=10
        )
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
            text = (
                f"Case ID: {case.case_id}\nTitle: {case.title}\n"
                f"Investigator: {case.investigator}\nCreated: {case.created_at}\n"
                f"Evidence items: {len(case.evidence)}\n"
                f"Custody entries: {len(case.custody_log)}\n"
                f"Timeline events: {len(case.events)}"
            )
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
        investigator = simpledialog.askstring(
            "New case", "Investigator:", parent=self.root
        )
        if investigator is None:
            return
        self.case = case_manager.create_case(case_id, title, investigator)
        self.case_path = None
        self.filtered = False
        self.refresh_all()
        self.set_status(f"Created case {self.case.case_id}.")

    def build_evidence_tab(self):
        """Create the Evidence tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Evidence")
        buttons = ttk.Frame(tab)
        buttons.pack(fill="x", padx=10, pady=10)
        ttk.Button(
            buttons, text="Register evidence...", command=self.open_register_form
        ).pack(side="left", padx=5)
        ttk.Button(
            buttons, text="Edit description...", command=self.edit_selected_evidence
        ).pack(side="left", padx=5)
        ttk.Button(
            buttons, text="Delete selected", command=self.delete_selected_evidence
        ).pack(side="left", padx=5)
        columns = ("id", "description", "source", "collector", "sha256")
        self.evidence_tree = ttk.Treeview(tab, columns=columns, show="headings")
        for name, width in zip(columns, (80, 280, 140, 120, 360)):
            self.evidence_tree.heading(name, text=name.upper())
            self.evidence_tree.column(name, width=width)
        self.evidence_tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.refreshers.append(self.refresh_evidence_tab)

    def refresh_evidence_tab(self):
        """Redraw the evidence table."""
        self.evidence_tree.delete(*self.evidence_tree.get_children())
        if self.case is None:
            return
        for item in sorted(self.case.evidence.values(), key=lambda i: i.evidence_id):
            self.evidence_tree.insert(
                "",
                tk.END,
                iid=item.evidence_id,
                values=(
                    item.evidence_id,
                    item.description,
                    item.source,
                    item.collector,
                    item.sha256,
                ),
            )

    @guarded
    def open_register_form(self):
        """Open a form window for registering evidence."""
        self.require_case()
        win = tk.Toplevel(self.root)
        win.title("Register evidence")
        labels = ["Evidence ID", "Description", "Source", "Collector", "File path"]
        entries = {}
        for row, label in enumerate(labels):
            ttk.Label(win, text=label).grid(
                row=row, column=0, sticky="w", padx=8, pady=4
            )
            entry = ttk.Entry(win, width=50)
            entry.grid(row=row, column=1, padx=8, pady=4)
            entries[label] = entry

        def browse():
            path = filedialog.askopenfilename(parent=win)
            if path:
                entries["File path"].delete(0, tk.END)
                entries["File path"].insert(0, path)

        def submit():
            try:
                chain.register_and_log(
                    self.case,
                    entries["Evidence ID"].get(),
                    entries["Description"].get(),
                    entries["Source"].get(),
                    entries["Collector"].get(),
                    entries["File path"].get(),
                )
            except VaultError as err:
                messagebox.showerror("Cannot register", str(err), parent=win)
                return
            win.destroy()
            self.refresh_all()
            self.set_status("Evidence registered.")

        ttk.Button(win, text="Browse...", command=browse).grid(row=4, column=2, padx=4)
        ttk.Button(win, text="Register", command=submit).grid(
            row=5, column=1, sticky="e", padx=8, pady=10
        )

    def selected_evidence_id(self):
        """Return the ID selected in the evidence table."""
        selection = self.evidence_tree.selection()
        if not selection:
            raise VaultError("Click an evidence row first.")
        return selection[0]

    @guarded
    def edit_selected_evidence(self):
        """Change the description of the selected evidence."""
        self.require_case()
        evidence_id = self.selected_evidence_id()
        new_text = simpledialog.askstring(
            "Edit description",
            "New description:",
            parent=self.root,
            initialvalue=self.case.evidence[evidence_id].description,
        )
        if new_text is None:
            return
        case_manager.edit_evidence_description(self.case, evidence_id, new_text)
        self.refresh_all()
        self.set_status("Description updated.")

    @guarded
    def delete_selected_evidence(self):
        """Delete the selected evidence after asking."""
        self.require_case()
        evidence_id = self.selected_evidence_id()
        if messagebox.askyesno("Delete", f"Delete evidence {evidence_id}?"):
            case_manager.delete_evidence(self.case, evidence_id)
            self.refresh_all()
            self.set_status("Evidence deleted.")

    def build_timeline_tab(self):
        """Create the Timeline tab with a table of events."""
        self.timeline_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.timeline_tab, text="Timeline")
        buttons = ttk.Frame(self.timeline_tab)
        buttons.pack(fill="x", padx=10, pady=10)
        ttk.Button(
            buttons, text="Import events...", command=self.import_events_dialog
        ).pack(side="left", padx=5)
        self.timeline_body = ttk.Frame(self.timeline_tab)
        self.timeline_body.pack(fill="both", expand=True, padx=10, pady=10)
        columns = ("time", "source", "evidence", "description")
        self.timeline_tree = ttk.Treeview(
            self.timeline_body, columns=columns, show="headings"
        )
        for name, width in zip(columns, (190, 100, 90, 620)):
            self.timeline_tree.heading(name, text=name.upper())
            self.timeline_tree.column(name, width=width)
        scroll = ttk.Scrollbar(self.timeline_body, command=self.timeline_tree.yview)
        self.timeline_tree.config(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.timeline_tree.pack(fill="both", expand=True)
        self.refreshers.append(self.refresh_timeline_tab)

    def refresh_timeline_tab(self):
        """Redraw the timeline table (all events, or the current filter)."""
        self.timeline_tree.delete(*self.timeline_tree.get_children())
        if self.case is None:
            return
        events = self.view_events if self.filtered else self.case.events
        for event in events:
            self.timeline_tree.insert(
                "",
                tk.END,
                values=(
                    event.timestamp,
                    event.source,
                    event.evidence_id,
                    event.description,
                ),
            )

    @guarded
    def import_events_dialog(self):
        """Pick a log file and import its events."""
        self.require_case()
        path = filedialog.askopenfilename(
            title="Choose a log file",
            filetypes=[("Logs", "*.csv *.txt *.log"), ("All files", "*.*")],
        )
        if not path:
            return
        default_name = os.path.splitext(os.path.basename(path))[0]
        source = simpledialog.askstring(
            "Source name",
            "Name for this source:",
            parent=self.root,
            initialvalue=default_name,
        )
        if source is None:
            return
        evidence_id = (
            simpledialog.askstring(
                "Evidence ID",
                "Evidence ID it came from (leave blank for none):",
                parent=self.root,
            )
            or ""
        )
        if evidence_id.strip():
            case_manager.get_evidence(self.case, evidence_id)
        events, skipped = timeline.import_events(path, source, evidence_id.strip())
        added = timeline.add_events(self.case, events)
        self.filtered = False
        self.refresh_all()
        self.set_status(f"Imported {added} events, skipped {skipped} bad lines.")

    def build_integrity_widgets(self):
        """Add the Verify button and the PASS/FAIL label to the top bar."""
        ttk.Button(
            self.top, text="Verify integrity", command=self.verify_integrity
        ).pack(side="right", padx=5)
        self.integrity_label = tk.Label(
            self.top,
            text="Integrity: not checked",
            fg="gray",
            font=("Arial", 12, "bold"),
        )
        self.integrity_label.pack(side="right", padx=10)
        self.refreshers.append(self.reset_integrity_label)

    def reset_integrity_label(self):
        """Show 'not checked' (anything may have changed since the last check)."""
        self.integrity_label.config(text="Integrity: not checked", fg="gray")

    @guarded
    def verify_integrity(self):
        """Run the integrity checks and show the result."""
        ok, messages = chain.check_integrity(self.require_case())
        if ok:
            self.integrity_label.config(text="Integrity: PASS", fg="green")
            messagebox.showinfo("Integrity PASS", "\n".join(messages))
        else:
            self.integrity_label.config(text="Integrity: FAIL", fg="red")
            messagebox.showwarning("Integrity FAIL", "\n".join(messages))
        self.set_status("Integrity check finished.")

    def build_custody_tab(self):
        """Create the Custody log tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Custody log")
        buttons = ttk.Frame(tab)
        buttons.pack(fill="x", padx=10, pady=10)
        ttk.Button(
            buttons, text="Record custody action...", command=self.record_custody_action
        ).pack(side="left", padx=5)
        columns = ("no", "evidence", "action", "actor", "time")
        self.custody_tree = ttk.Treeview(tab, columns=columns, show="headings")
        for name, width in zip(columns, (50, 90, 200, 150, 220)):
            self.custody_tree.heading(name, text=name.upper())
            self.custody_tree.column(name, width=width)
        self.custody_tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.refreshers.append(self.refresh_custody_tab)

    def refresh_custody_tab(self):
        """Redraw the custody table."""
        self.custody_tree.delete(*self.custody_tree.get_children())
        if self.case is None:
            return
        for entry in self.case.custody_log:
            self.custody_tree.insert(
                "",
                tk.END,
                values=(
                    entry.entry_id,
                    entry.evidence_id,
                    entry.action,
                    entry.actor,
                    entry.timestamp,
                ),
            )

    @guarded
    def record_custody_action(self):
        """Ask for the details and add a custody entry."""
        self.require_case()
        evidence_id = simpledialog.askstring(
            "Custody", "Evidence ID (leave blank for the whole case):", parent=self.root
        )
        if evidence_id is None:
            return
        action = simpledialog.askstring(
            "Custody", "Action (e.g. TRANSFERRED):", parent=self.root
        )
        if action is None:
            return
        actor = simpledialog.askstring("Custody", "Who did it:", parent=self.root)
        if actor is None:
            return
        chain.append_entry(self.case, evidence_id, action, actor)
        self.refresh_all()
        self.set_status("Custody entry recorded.")

    # ===== NEW METHODS GO ABOVE THIS LINE =====


def main():
    """Start the application."""
    root = tk.Tk()
    VaultApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
