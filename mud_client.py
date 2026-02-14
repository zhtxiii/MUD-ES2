import threading
import readline
import socket
import sys
import os

# Telnet protocol constants
IAC  = 255  # Interpret As Command
DONT = 254
DO   = 253
WONT = 252
WILL = 251
SB   = 250  # Subnegotiation Begin
SE   = 240  # Subnegotiation End

def filter_telnet_commands(data):
    """
    Filter out Telnet IAC commands from the data stream.
    Returns cleaned data.
    """
    result = bytearray()
    i = 0
    while i < len(data):
        if data[i] == IAC:
            if i + 1 < len(data):
                cmd = data[i + 1]
                if cmd == IAC:
                    # Escaped 0xFF, output single 0xFF
                    result.append(IAC)
                    i += 2
                elif cmd in (WILL, WONT, DO, DONT):
                    # 3-byte command: IAC + CMD + OPTION
                    i += 3
                elif cmd == SB:
                    # Subnegotiation: skip until IAC SE
                    i += 2
                    while i < len(data) - 1:
                        if data[i] == IAC and data[i + 1] == SE:
                            i += 2
                            break
                        i += 1
                else:
                    # 2-byte command
                    i += 2
            else:
                # Incomplete IAC at end, skip
                i += 1
        else:
            result.append(data[i])
            i += 1
    return bytes(result)

def receive_loop(sock):
    """
    Handles receiving data from the server and printing it to stdout.
    """
    import codecs
    decoder = codecs.getincrementaldecoder("utf-8")(errors='replace')
    
    while True:
        try:
            data = sock.recv(4096)
            if not data:
                print("\n[Client] Disconnected from server.")
                sock.close()
                sys.exit(0)
            
            # Filter out Telnet protocol commands
            clean_data = filter_telnet_commands(data)
            if clean_data:
                # Use incremental decoder to handle split UTF-8 characters across packets
                text = decoder.decode(clean_data, final=False)
                if text:
                    sys.stdout.write(text)
                    sys.stdout.flush()
        except OSError:
            break
        except Exception as e:
            print(f"\n[Client] Error receiving data: {e}")
            break

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 mud_client.py <host> <port>")
        print("Example: python3 mud_client.py 127.0.0.1 4000")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"[Client] Connecting to {host}:{port}...")
        s.connect((host, port))
        print("[Client] Connected! You can start typing commands.")
        print("-" * 40)
    except Exception as e:
        print(f"[Client] Connection failed: {e}")
        sys.exit(1)

    # Start the receiver thread
    # Daemon=True ensures it dies when the main thread dies
    t = threading.Thread(target=receive_loop, args=(s,), daemon=True)
    t.start()

    try:
        while True:
            # Read from stdin
            # usage of sys.stdin.readline allows us to handle input line by line
            line = input()

            if line.startswith(':'):
                line = line[1:]
                match line:
                    case 'clear' | 'cls':
                        os.system('cls' if os.name == 'nt' else 'clear')
                    case _:
                        print('未知客户端指令!')

                continue
            
            # Send the line to the server
            # Encode as UTF-8 (standard for this project)
            try:
                s.sendall((line + '\n').encode('utf-8'))
            except (BrokenPipeError, OSError):
                # Server closed connection
                break
    except KeyboardInterrupt:
        print("\n[Client] Exiting...")
    finally:
        try:
            s.close()
        except:
            pass

if __name__ == "__main__":
    # Force line buffering for smoother output if needed, 
    # but normally stdout.flush() in loop is enough.
    main()
