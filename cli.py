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
