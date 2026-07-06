### pkaction Rules Generator

This project creates a Polkit `.rules` file from terminal output saved in `pkaction.txt`.

The script reads each section in `pkaction.txt`, finds entries whose `implicit active` value is `auth_admin` or `auth_admin_keep`, and writes those entries to a dated rules file named `pkaction.{date}.rules`.

### Files

- `main.py` — Runs the parser and creates the rules file.
- `pkaction.txt` — Input file containing the output from `pkaction -v`.
- `FormatSample.rules` — Example of the expected rules file format.
- `pkaction.{date}.rules` — Output file created by the script.
- `test_main.py` — Unit tests for the parser and file creation logic.

### How to Use

1. Open a terminal in the same directory as `main.py`.
2. Create or replace `pkaction.txt` with the output from this command:

```bash
pkaction -v > pkaction.txt
```

3. Run the script:

```bash
python3 main.py
```

4. When the script finishes, it creates a rules file in the same directory using the current date in the filename, for example:

```text
pkaction.2026-07-05.rules
```

5. The terminal also shows how many entries were found for each matching value:

```text
Created pkaction.2026-07-05.rules
implicit active: auth_admin: 43
implicit active: auth_admin_keep: 120
```

### Input Requirements

- The input file must be named `pkaction.txt`.
- `pkaction.txt` must be in the same directory as `main.py`.
- The file should contain the terminal output from `pkaction -v`.
- Sections should be separated by blank lines, as produced by `pkaction -v`.

### What Gets Included

Only sections with one of these `implicit active` values are included in the generated rules file:

- `auth_admin`
- `auth_admin_keep`

Spacing does not matter when matching these values. For example, both of these lines are treated as matches:

```text
implicit active:   auth_admin
implicit    active:auth_admin_keep
```

### Running Tests

To run the included tests, use:

```bash
python3 -m unittest -v
```
