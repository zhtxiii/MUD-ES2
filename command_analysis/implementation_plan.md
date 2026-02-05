# Implementation Plan - Command Analysis and Verification

## Goal Description
Analyze all MUD command files in `mudlib/cmds` to extract metadata (usage, description, etc.) into a JSON file (`commands.json`). Then, verify this information by actually logging into the MUD and testing the commands.

## Proposed Changes

### [NEW] [scan_cmds.py](file:///Users/example/.gemini/antigravity/brain/1adfe31c-d838-4b15-b10f-2b82ba55b252/scan_cmds.py)
- A Python script to recursively scan `mudlib/cmds`.
- Parses `.c` files to extract:
    - Command Name
    - Category
    - Help Text (from `help()` function)
- Generates `commands_initial.json`.

### [NEW] [verify_cmds.py](file:///Users/example/.gemini/antigravity/brain/1adfe31c-d838-4b15-b10f-2b82ba55b252/verify_cmds.py)
- A Python script to connect to the MUD server via Telnet.
- Logs in as a test user (`cmdtester`).
- Iterates through commands found in `commands_initial.json`.
- Executes each command (or `help <command>`).
- Captures output and verifies against extracted data.
- Updates the JSON with verification results, producing `commands_verified.json`.

### [NEW] [commands.json](file:///Users/example/.gemini/antigravity/brain/1adfe31c-d838-4b15-b10f-2b82ba55b252/commands.json)
- The final output file containing all command metadata and verification status.

## Verification Plan

### Automated Tests
1. **Run Parser**: Execute `python3 scan_cmds.py` and check if `commands_initial.json` is generated with valid data.
2. **Run Verifier**: Execute `python3 verify_cmds.py`.
    - Ensure MUD server is running (User needs to ensure this, or I can check).
    - The script will log in and run commands.
    - Check `verification.log` (intermediate document) and the final JSON.

### Manual Verification
- Review `commands.json` to ensure the format is correct and descriptions are meaningful.
- Spot check a few commands in the MUD manually if the automated verification reports errors.
