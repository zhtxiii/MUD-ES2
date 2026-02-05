import os
import re
import json

# Configuration
PROJECT_ROOT = "/path/to/es2-utf8-master"
MUDLIB_ROOT = os.path.join(PROJECT_ROOT, "mudlib")
SEARCH_DIR = os.path.join(MUDLIB_ROOT, "d")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "mud_map.json")

room_files = {}

def resolve_path(current_file_path, link_expr):
    """
    Resolves a path expression from an LPC file to an absolute filesystem path.
    Handles __DIR__ and absolute MUD paths (starting with /).
    """
    current_dir = os.path.dirname(current_file_path)
    link_expr = link_expr.strip()

    # Remove potential trailing comma
    if link_expr.endswith(','):
        link_expr = link_expr[:-1]

    path = ""
    
    # Handle string concatenation like __DIR__"file"
    # We'll simple replace __DIR__ with the current directory path
    # and strip quotes.
    
    # Naive tokenization: check for __DIR__
    if "__DIR__" in link_expr:
        # Replace __DIR__ with actual dir path, but strictly speaking __DIR__ is a string prefix in LPC usually concatenating
        # Example: "west" : __DIR__"canyon4"
        # We want to treat __DIR__ as current_dir
        
        # Remove __DIR__
        remainder = link_expr.replace("__DIR__", "")
        # Remove quotes and + signs if any
        remainder = remainder.replace('"', '').replace("'", "").replace("+", "").strip()
        
        path = os.path.join(current_dir, remainder)
    else:
        # Regular string "path/to/file"
        clean_path = link_expr.replace('"', '').replace("'", "").strip()
        
        if clean_path.startswith('/'):
            # Absolute MUD path: /d/canyon/camp1 -> MUDLIB_ROOT/d/canyon/camp1
            # Note: MUD paths start from root, so /d/... maps to mudlib/d/...
            # But wait, does / refer to mudlib root? Yes, usually.
            path = os.path.join(MUDLIB_ROOT, clean_path.lstrip('/'))
        else:
            # Relative path without __DIR__? Rare but possible.
            path = os.path.join(current_dir, clean_path)

    # Normalize path
    path = os.path.normpath(path)
    
    # Append .c if missing
    if not path.endswith('.c'):
        path += '.c'
        
    return path

def process_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Check for matching "inherit ROOM;" or similar
        # Some files might inherit "/std/room" or "ROOM"
        if not re.search(r'inherit\s+ROOM;', content) and not re.search(r'inherit\s+"/std/room";', content):
            return

        # Extract short description
        short_match = re.search(r'set\("short"\s*,\s*"([^"]+)"\)', content)
        short_desc = short_match.group(1) if short_match else os.path.basename(file_path)

        # Extract long description
        long_match = re.search(r'set\("long"\s*,\s*@LONG(.*?)LONG', content, re.DOTALL)
        long_desc = long_match.group(1).strip() if long_match else ""

        # Extract exits
        exits = {}
        # Match the exits map: set("exits", ([ ... ]) );
        exits_match = re.search(r'set\("exits"\s*,\s*\(\[\s*(.*?)\s*\]\)\s*\)', content, re.DOTALL)
        
        if exits_match:
            exits_body = exits_match.group(1)
            # Find all key-value pairs. 
            # Key is usually "direction"
            # Value can be __DIR__"file", "/path/file", etc.
            
            # Regex to find "key" : value,
            # We match "key" : 
            # Then we assume the value ends at a comma or end of string.
            # This is slightly tricky with general regex but generally values don't contain commas in this context usually?
            # Actually filenames won't have commas.
            
            pairs = re.findall(r'"([^"]+)"\s*:\s*([^,]+)', exits_body)
            for direction, dest_expr in pairs:
                # dest_expr might contain newlines or spaces
                dest_expr = dest_expr.strip()
                full_dest_path = resolve_path(file_path, dest_expr)
                exits[direction] = full_dest_path

        room_files[file_path] = {
            "short": short_desc,
            "long": long_desc,
            "exits": exits
        }
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def main():
    print(f"Scanning {SEARCH_DIR}...")
    for root, dirs, files in os.walk(SEARCH_DIR):
        for file in files:
            if file.endswith(".c"):
                process_file(os.path.join(root, file))

    print(f"Found {len(room_files)} rooms.")

    # Prepare data for JSON
    nodes = []
    edges = []
    
    # Map file paths to numeric IDs for the graph
    path_to_id = {}
    next_id = 1
    
    # First pass: Create IDs for all scanned rooms
    for path in room_files:
        path_to_id[path] = next_id
        next_id += 1
        
    # Helper to get or create ID (for external links)
    def get_id(path):
        nonlocal next_id
        if path not in path_to_id:
            path_to_id[path] = next_id
            next_id += 1
        return path_to_id[path]

    # Generate Nodes
    for path, data in room_files.items():
        node_id = get_id(path)
        rel_path = os.path.relpath(path, MUDLIB_ROOT)
        
        # Determine group (area/directory)
        parts = rel_path.split(os.sep)
        group_name = "unknown"
        if len(parts) > 1 and parts[0] == 'd':
            group_name = parts[1]
        elif len(parts) > 0:
            group_name = parts[0]

        nodes.append({
            "id": node_id,
            "label": data["short"],
            "title": f"{data['short']}\n{rel_path}\n\n{data['long'][:100]}...",
            "group": group_name, 
            "path": rel_path
        })

    # Abbreviation map
    dir_map = {
        "north": "n", "south": "s", "east": "e", "west": "w",
        "northeast": "ne", "northwest": "nw", "southeast": "se", "southwest": "sw",
        "up": "u", "down": "d", "enter": "in", "out": "out",
        "northup": "nu", "northdown": "nd", "southup": "su", "southdown": "sd",
        "eastup": "eu", "eastdown": "ed", "westup": "wu", "westdown": "wd"
    }

    # Generate Edges with merging
    # We use a set of keys to track added edges: tuple(sorted((id1, id2)))
    # But wait, we need to know if it's single or bidirectional.
    # Let's map (id1, id2) -> label
    
    raw_edges = [] 
    
    for path, data in room_files.items():
        src_id = get_id(path)
        for direction, dest_path in data["exits"].items():
            dest_id = get_id(dest_path)
            short_dir = dir_map.get(direction, direction)
            raw_edges.append({
                "from": src_id,
                "to": dest_id,
                "label": short_dir
            })
            
    # Merging logic
    # Store edges in a directed dict: src -> dest -> label
    adj = {}
    for e in raw_edges:
        u, v, label = e['from'], e['to'], e['label']
        if u not in adj: adj[u] = {}
        adj[u][v] = label
        
    processed = set()
    
    for e in raw_edges:
        u, v, label_uv = e['from'], e['to'], e['label']
        
        # Check if we already processed this pair (u, v) or (v, u)
        pair_key = tuple(sorted((u, v)))
        if pair_key in processed:
            continue
            
        # Check if reverse edge exists
        is_bi = False
        label_vu = ""
        if v in adj and u in adj[v]:
            is_bi = True
            label_vu = adj[v][u]
            
        processed.add(pair_key)
        
        edge_data = {
            "from": u,
            "to": v,
            "color": {"color": "#848484"} 
        }
        
        # Check if destination is external (only for u->v direction logic really, but if bi-directional, v must be internal essentially?)
        # Actually v could be external if u->v exists. But v->u won't exist if v is external (not scanned).
        # So bidirectional implies both are scanned.
        
        # Node lookup for external check
        # We can check if v is in room_files keys nodes. 
        # Easier: check if v matches a known path? 
        # We constructed nodes earlier.
        
        if is_bi:
            edge_data["arrows"] = "to;from"
            # Combine labels? e.g. "n" and "s". Just show "n" or nothing?
            # User output: "n" implies u->v is n. v->u is likely s.
            # Showing "n/s" is explicit.
            # Showing nothing reduces clutter.
            # User request: "south->s", "southeast->se".
            # Let's merge labels: "n/s"
            edge_data["label"] = f"{label_uv}/{label_vu}"
            # Optimization: If they are standard opposites, maybe hide?
            # For now, show abbreviated.
        else:
            edge_data["arrows"] = "to"
            edge_data["label"] = label_uv
            
            # Check external color
            # If v is an external node ID?
            # We don't have easy lookup here without map.
            # Reconstruct is_external check:
            # dest_path for this edge... lookup usage is tricky with IDs.
            # Let's just create nodes map by ID
            pass 

        edges.append(edge_data)

    # External nodes check (re-add external nodes logic)
    # We need to know which IDs are external.
    # existing nodes have 'group' != 'external'?
    # Actually we just add all nodes from path_to_id that aren't in room_files
    
    # ... (previous code for external nodes) ...

    # Add external nodes if they were created referenced
    # We iterate path_to_id and verify if we added them to nodes
    added_ids = set(n["id"] for n in nodes)
    for path, id_ in path_to_id.items():
        if id_ not in added_ids:
            # This is an external/unscanned node
            rel_path = os.path.relpath(path, MUDLIB_ROOT) if path.startswith("/") else path
            nodes.append({
                "id": id_,
                "label": os.path.basename(path).replace(".c", ""),
                "title": f"External: {path}",
                "group": "external",
                "shape": "box"
            })

    output = {
        "nodes": nodes,
        "edges": edges
    }

    # Output as JS file for local browser compatibility (CORS fix)
    output_js_file = OUTPUT_FILE.replace('.json', '.js')
    with open(output_js_file, 'w', encoding='utf-8') as f:
        f.write("window.mudData = ")
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write(";")

    print(f"Map data saved to {output_js_file}")

if __name__ == "__main__":
    main()
