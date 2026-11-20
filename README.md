# Evidence Vault

A small digital evidence case manager written in Python. It registers evidence files with SHA-256 fingerprints, keeps a tamper-evident chain of custody, merges log files into one timeline, and lets you search it. It comes in two versions with the same features: a text (command-line) version and a Tkinter GUI version. Both use the same `core` package.

## Features

- Create cases; register, edit and delete evidence items
- SHA-256 hashing of evidence files on intake
- Chain of custody where each entry stores the hash of the one before it
- Integrity check: finds altered custody entries and modified or missing evidence files
- Import events from CSV and text logs; time zones converted to UTC; k-way merge into one timeline
- Keyword search (inverted index), filters, time-window search (binary search) and burst grouping
- Save and load cases as JSON; text report and CSV export

## Requirements

- Python 3.10 or newer
- Tkinter (installed with Python on Windows and Mac; on Linux install the `python3-tk` package)
- No other packages (`requirements.txt` explains this)

## How to run

Text version:

```
python cli.py
```

GUI version:

```
python gui.py
```

Run both from the project folder. Try the files in `sample_data/` (all made-up data).

## How to run the tests

```
python -m unittest discover tests
```

## Project structure

- `core/` shared logic (models, validation, hashing, chain, timeline, search, storage, report)
- `cli.py` text interface, `gui.py` Tkinter interface (no business logic in either)
- `tests/` unit tests
- `sample_data/` fake logs and an evidence note

## Limitations

- Single user, single case open at a time
- Deleting the newest custody entries is not detected by the chain check
- Timestamps are stored to the second

## GenAI acknowledgement

I acknowledge the use of Claude (Anthropic, https://claude.ai) to review the code in this project and to help with the README and Git workflow. 