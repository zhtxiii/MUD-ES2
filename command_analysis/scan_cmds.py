import os
import re
import json

MUDLIB_DIR = "/path/to/es2-utf8-master/mudlib"
CMDS_DIR = os.path.join(MUDLIB_DIR, "cmds")
OUTPUT_FILE = "commands_initial.json"

def extract_help(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Look for help() function
        help_match = re.search(r'int help\s*\(.*?\)\s*\{(.*?)return 1;\s*\}', content, re.DOTALL)
        if help_match:
            help_body = help_match.group(1)
            # Extract content between write(@HELP ... HELP);
            text_match = re.search(r'write\s*\(\s*@HELP(.*?)HELP\s*\);', help_body, re.DOTALL)
            if text_match:
                return text_match.group(1).strip()
            
            # Fallback for simple write("...");
            simple_match = re.search(r'write\s*\(\s*"(.*?)"\s*\);', help_body, re.DOTALL)
            if simple_match:
                return simple_match.group(1).strip()
                
        return None
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def parse_metadata(help_text):
    if not help_text:
        return None, None
        
    format_str = None
    example_str = None
    
    # Extract Format
    # Common patterns: "指令格式 :", "指令格式:"
    format_match = re.search(r'(?m)^指令格式\s*[:：]\s*(.*)$', help_text)
    if format_match:
        format_str = format_match.group(1).strip()
        
    # Extract Example
    # Common patterns: "□例 :", "Example:"
    # This is trickier as it might be multi-line. We'll grab the line.
    example_match = re.search(r'(?m)^[□]?例\s*[:：]\s*(.*)$', help_text)
    if not example_match:
         example_match = re.search(r'(?m)^Example\s*[:：]\s*(.*)$', help_text)
         
    if example_match:
        example_str = example_match.group(1).strip()
        
    return format_str, example_str

def scan_commands():
    commands = {}
    
    for root, dirs, files in os.walk(CMDS_DIR):
        category = os.path.basename(root)
        if category == "cmds": continue
        
        for file in files:
            if file.endswith(".c"):
                cmd_name = file[:-2]
                file_path = os.path.join(root, file)
                
                help_text = extract_help(file_path)
                cmd_format, cmd_example = parse_metadata(help_text)
                
                commands[cmd_name] = {
                    "name": cmd_name,
                    "category": category,
                    "file_path": file_path,
                    "help": help_text,
                    "format": cmd_format,
                    "example": cmd_example,
                    "verified": False
                }
                
    return commands

def main():
    print(f"Scanning commands in {CMDS_DIR}...")
    cmds = scan_commands()
    print(f"Found {len(cmds)} commands.")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(cmds, f, indent=4, ensure_ascii=False)
    
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
