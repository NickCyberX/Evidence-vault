# I acknowledge the use of Claude (Anthropic, https://claude.ai) to review the code in this file.

"""Text (command-line) version of the Evidence Vault.

This file only asks questions and prints answers. All real work is done
by the modules in the core package.
"""

from core import case_manager, chain, report, search, storage, timeline
from core.errors import VaultError


class Session:
    """Holds the case that is currently open."""

    def __init__(self):
        self.case = None
        self.path = None
        self.searcher = search.TimelineSearcher()


SESSION = Session()
ACTIONS = {}


def ask(prompt):
    """Ask a question and return the answer without spaces at the ends."""
    return input(prompt).strip()


def ask_int(prompt):
    """Keep asking until the user types a whole number."""
    while True:
        answer = ask(prompt)
        try:
            return int(answer)
        except ValueError:
            print("Please type a whole number, for example 30.")


def need_case():
    """Return the open case, or raise an error if there is none."""
    if SESSION.case is None:
        raise VaultError("No case is open. Create or load a case first.")
    return SESSION.case


def print_menu():
    """Show every menu option."""
    print("\n--- MENU ---")
    for key in sorted(ACTIONS, key=int):
        print(f"{key:>2}. {ACTIONS[key][0]}")
    print(" 0. Exit")


def print_events(events):
    """Print timeline events, one per line."""
    if not events:
        print("(no events)")
    for number, event in enumerate(events, start=1):
        tag = f" [{event.evidence_id}]" if event.evidence_id else ""
        print(
            f"{number:>3}. {event.timestamp} | {event.source}{tag} | {event.description}"
        )


def action_create_case():
    """Menu: create a new case."""
    case_id = ask("Case ID: ")
    title = ask("Title: ")
    investigator = ask("Investigator: ")
    SESSION.case = case_manager.create_case(case_id, title, investigator)
    SESSION.path = None
    print(f"Created case {SESSION.case.case_id}.")


def action_show_case():
    """Menu: show details of the open case."""
    case = need_case()
    print(f"Case {case.case_id}: {case.title}")
    print(f"Investigator: {case.investigator}   Created: {case.created_at}")
    print(f"Evidence items: {len(case.evidence)}")
    for item in sorted(case.evidence.values(), key=lambda i: i.evidence_id):
        print(f"  {item.evidence_id}: {item.description} ({item.file_path})")
        print(f"      SHA-256: {item.sha256}")
    print(f"Custody entries: {len(case.custody_log)}")
    print(f"Timeline events: {len(case.events)}")


ACTIONS["1"] = ("Create a new case", action_create_case)
ACTIONS["2"] = ("Show case details", action_show_case)


def action_register_evidence():
    """Menu: register an evidence file."""
    case = need_case()
    evidence_id = ask("Evidence ID (letters, digits, hyphens): ")
    description = ask("Description: ")
    source = ask("Source (where it came from): ")
    collector = ask("Collector (your name): ")
    file_path = ask("Path to the evidence file: ")
    item = chain.register_and_log(
        case, evidence_id, description, source, collector, file_path
    )
    print(f"Registered {item.evidence_id}. SHA-256: {item.sha256}")


def action_edit_evidence():
    """Menu: change an evidence description."""
    case = need_case()
    evidence_id = ask("Evidence ID to edit: ")
    new_text = ask("New description: ")
    case_manager.edit_evidence_description(case, evidence_id, new_text)
    print("Description updated.")


def action_delete_evidence():
    """Menu: delete an evidence item after confirmation."""
    case = need_case()
    evidence_id = ask("Evidence ID to delete: ")
    case_manager.get_evidence(case, evidence_id)
    if ask("Type YES to confirm deletion: ") == "YES":
        case_manager.delete_evidence(case, evidence_id)
        print("Evidence deleted.")
    else:
        print("Nothing was deleted.")


ACTIONS["3"] = ("Register evidence", action_register_evidence)
ACTIONS["4"] = ("Edit evidence description", action_edit_evidence)
ACTIONS["5"] = ("Delete evidence", action_delete_evidence)


def action_custody():
    """Menu: record a custody action."""
    case = need_case()
    evidence_id = ask("Evidence ID (leave blank for the whole case): ")
    action = ask("Action (for example TRANSFERRED): ")
    actor = ask("Who did it: ")
    entry = chain.append_entry(case, evidence_id, action, actor)
    print(f"Recorded custody entry {entry.entry_id}.")


def action_verify():
    """Menu: check the custody chain and the evidence files."""
    ok, messages = chain.check_integrity(need_case())
    print("INTEGRITY: PASS" if ok else "INTEGRITY: FAIL")
    for message in messages:
        print(f"  - {message}")


ACTIONS["6"] = ("Record a custody action", action_custody)
ACTIONS["7"] = ("Verify integrity", action_verify)


def action_import():
    """Menu: import events from a CSV or text log."""
    case = need_case()
    path = ask("Path to the log file (.csv or text): ")
    source = ask("Name for this source (for example auth): ")
    evidence_id = ask("Evidence ID it came from (blank for none): ")
    if evidence_id:
        case_manager.get_evidence(case, evidence_id)
    events, skipped = timeline.import_events(path, source, evidence_id)
    added = timeline.add_events(case, events)
    print(f"Imported {added} events. Skipped {skipped} bad lines.")


def action_timeline():
    """Menu: show the whole timeline."""
    print_events(need_case().events)


ACTIONS["8"] = ("Import events from a file", action_import)
ACTIONS["9"] = ("View timeline", action_timeline)

# ===== NEW COMMANDS GO ABOVE THIS LINE =====


def main():
    """Run the menu loop."""
    print("=== Evidence Vault (text version) ===")
    while True:
        print_menu()
        choice = ask("Choose an option: ")
        if choice == "0":
            print("Goodbye.")
            break
        action = ACTIONS.get(choice)
        if action is None:
            print("That is not a menu option.")
            continue
        try:
            action[1]()
        except VaultError as err:
            print(f"Error: {err}")


if __name__ == "__main__":
    main()
