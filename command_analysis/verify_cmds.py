
import socket
import time
import json
import re
import sys

HOST = "127.0.0.1"
PORT = 4000
COMMANDS_FILE = "commands_initial.json"
OUTPUT_FILE = "commands_verified.json"
LOG_FILE = "verification.log"

def log(msg):
    print(msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    return s

def read_until(s, patterns, timeout=5):
    buffer = b""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            s.settimeout(0.1)
            data = s.recv(1024)
            if not data:
                break
            buffer += data
            decoded = buffer.decode("utf-8", errors="ignore")  # MUD is likely Big5 or GBK, but try utf-8 first (user modified es2-utf8)
            
            for pattern in patterns:
                if pattern in decoded:
                    return decoded, pattern
        except socket.timeout:
            continue
        except Exception as e:
            log(f"Error reading: {e}")
            break
    return buffer.decode("utf-8", errors="ignore"), None

def send(s, msg):
    s.sendall((msg + "\r\n").encode("utf-8"))
    time.sleep(0.2)

def clean_ansi(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def login(s):
    log("Starting login sequence...")
    
    # Initial connect
    out, match = read_until(s, ["英文名字："], timeout=3)
    if "英文名字：" not in out:
         # Maybe verify if we need to hit enter first?
         send(s, "")
    
    send(s, "cmdtester")
    
    # Check if new or existing
    out, match = read_until(s, ["请输入密码：", "您确定吗(y/n)？"], timeout=3)
    
    if match == "请输入密码：":
        log("User exists, logging in...")
        send(s, "12345")
        
        # Check for double login kick
        out, match = read_until(s, ["赶出去", "连线进入"], timeout=3)
        if "赶出去" in out:
            send(s, "y")
            read_until(s, ["连线进入"], timeout=3)
            
    elif match == "您确定吗(y/n)？":
        log("Creating new user...")
        send(s, "y")
        read_until(s, ["中文名字："])
        send(s, "测试员")
        read_until(s, ["密码："])
        send(s, "12345")
        read_until(s, ["没记错："])
        send(s, "12345")
        read_until(s, ["地址："])
        send(s, "test@test.com")
        read_until(s, ["角色？"])
        send(s, "m")
        # Wait for entry
        time.sleep(2)
    else:
        log(f"Unexpected login state: {out}")
        return False
        
    return True

SKIP_EXECUTION = [
    "quit", "suicide", "edemote", "alias", "passwd", "vote", 
    "shutdown", "reboot", "update", "call", "eval"
]

def verify_commands(s, commands):
    for cmd_key, cmd_data in commands.items():
        if cmd_data["category"] not in ["std", "usr"]:
            continue
            
        log(f"Verifying {cmd_key}...")
        
        # 1. Capture Help Interaction
        help_input = f"help {cmd_key}"
        send(s, help_input)
        out, _ = read_until(s, ["指令格式", "未有详细说明", ">"], timeout=1)  # Search for common help markers or prompt
        out = clean_ansi(out)
        
        # Determine verification status based on help
        if "指令格式" in out or "这个指令" in out:
            log(f"  [PASS] Help found for {cmd_key}")
            cmd_data["verified"] = True
            cmd_data["verification_note"] = "Help text verified via MUD"
        elif "未有详细说明" in out:
            log(f"  [WARN] No help for {cmd_key}")
            cmd_data["verification_note"] = "No help text in MUD"
        else:
            log(f"  [?] Unknown response for {cmd_key}")
            cmd_data["verification_note"] = f"Response start: {out[:20]}"

        # 2. Capture Active Execution (Interaction)
        if cmd_key not in SKIP_EXECUTION:
            log(f"  [EXEC] Running {cmd_key}...")
            send(s, cmd_key)
            
            # We don't know exactly what to wait for, so we wait a bit and read everything.
            # A dynamic delay or reading until prompt '>' would be better if prompt is consistent.
            time.sleep(0.5) 
            exec_out, _ = read_until(s, [">"], timeout=1) 
            exec_out = clean_ansi(exec_out)
            
            # Clean up the output: remove the command echo if present, etc.
            # Usually MUDs echo the command. 
            # We will store the raw output.
            
            cmd_data["interaction"] = {
                "input": cmd_key,
                "output": exec_out.strip()
            }
        else:
             # For skipped commands, use help interaction as a fallback example
             cmd_data["interaction"] = {
                "input": help_input,
                "output": out.strip()
            }
            
    return commands

def main():
    try:
        with open(COMMANDS_FILE, 'r', encoding='utf-8') as f:
            commands = json.load(f)
            
        s = connect()
        if login(s):
            log("Login successful. Starting verification...")
            time.sleep(1) # Let welcome messages pass
            
            # Clear buffer before starting
            s.setblocking(0)
            try:
                s.recv(4096)
            except:
                pass
            s.setblocking(1)
             
            verified_cmds = verify_commands(s, commands)
            
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(verified_cmds, f, indent=4, ensure_ascii=False)
            log(f"Verification complete. Saved to {OUTPUT_FILE}")
            
        else:
            log("Login failed.")
            
        s.close()
        
    except Exception as e:
        log(f"Fatal error: {e}")

if __name__ == "__main__":
    main()
