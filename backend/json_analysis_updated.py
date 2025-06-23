#!/usr/bin/env python3
import json
import re
import argparse

def extract_entries(data, key_path):
    """Safely traverse a nested key path in dict `data` to return a list."""
    entry = data
    for key in key_path:
        entry = entry.get(key, {})
    return entry if isinstance(entry, list) else []

def get_file_cc(file_entry):
    """Return the 'sum' of cyclomatic_complexity, or 0."""
    cc = file_entry.get('cyclomatic_complexity', 0)
    if isinstance(cc, dict):
        return cc.get('sum', 0)
    return cc if isinstance(cc, (int, float)) else 0

def get_file_depth(file_entry):
    """
    Extract *all* 'branching depth of X' occurrences from homplexity_output
    and return the maximum X. Handles:
     - file_entry['homplexity_output'] as a raw string (with real newlines or '\\n')
     - or as a dict with 'output_text'.
    """
    homplexity_analysis = file_entry.get('homplexity_analysis', {})
    raw = homplexity_analysis.get('homplexity_output', '')
    
    if isinstance(raw, dict):
        raw = raw.get('output_text', '')

    # Normalize literal backslash-n to real newlines so splitlines() works
    if '\\n' in raw and '\n' not in raw:
        raw = raw.replace('\\n', '\n')

    max_depth = 0
    for line in raw.splitlines():
        if ":SrcLoc" not in line:
            continue
        
        # drop the prefix up through :SrcLoc
        _, rest = line.split(":SrcLoc", 1)
        rest = rest.lstrip()

        # isolate the message text
        m = re.match(r'^"[^"]*"\s+\d+\s+\d+:\s*(.+)$', rest)
        if not m:
            continue
        msg = m.group(1).lower()

        if "branching depth" not in msg:
            continue

        # capture the integer after 'branching depth of'
        m2 = re.search(r'branching depth of\s+(\d+)', msg)
        if m2:
            depth = int(m2.group(1))
            max_depth = max(max_depth, depth)

    return max_depth

def main():
    parser = argparse.ArgumentParser(
        description="Compare LOC, CC, and Branching Depth per file (pre/post), showing totals."
    )
    parser.add_argument("json_path", help="Path to the JSON analysis file")
    args = parser.parse_args()

    with open(args.json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    pre_files  = extract_entries(data, ['analysis', 'pre_refactor', 'files'])
    post_files = extract_entries(
        data,
        ['analysis', 'post_refactor', 'hybrid', 'one_shot', 'files']
    )

    # Build lookup tables
    pre_locs    = {f['file_name']: f.get('lines_of_code', 0) for f in pre_files}
    post_locs   = {f['file_name']: f.get('lines_of_code', 0) for f in post_files}
    pre_ccs     = {f['file_name']: get_file_cc(f)          for f in pre_files}
    post_ccs    = {f['file_name']: get_file_cc(f)          for f in post_files}
    pre_depths  = {f['file_name']: get_file_depth(f)       for f in pre_files}
    post_depths = {f['file_name']: get_file_depth(f)       for f in post_files}

    # Header
    print(f"{'File':50} {'Pre-LOC':>8} {'Post-LOC':>9} "
          f"{'Pre-CC':>8} {'Post-CC':>9} {'Pre-Depth':>10} {'Post-Depth':>11}  Note")
    print("-" * 115)

    # Totals
    tot_pre_loc = tot_post_loc = 0
    tot_pre_cc  = tot_post_cc  = 0
    tot_pre_dp  = tot_post_dp  = 0

    for path in sorted(pre_locs):
        loc_pre  = pre_locs[path]
        loc_post = post_locs.get(path, loc_pre)
        cc_pre   = pre_ccs.get(path, 0)
        cc_post  = post_ccs.get(path, cc_pre)
        dp_pre   = pre_depths.get(path, 0)
        dp_post  = post_depths.get(path, dp_pre)
        note     = "ONLY PRE-REFACTOR" if path not in post_locs else ""
        print(f"{path:50} {loc_pre:8} {loc_post:9} "
              f"{cc_pre:8} {cc_post:9} {dp_pre:10} {dp_post:11}  {note}")

        tot_pre_loc  += loc_pre
        tot_post_loc += loc_post
        tot_pre_cc   += cc_pre
        tot_post_cc  += cc_post
        tot_pre_dp   += dp_pre
        tot_post_dp  += dp_post

    # Totals row
    print("\n" + "-" * 115)
    print(f"{'TOTAL':50} {tot_pre_loc:8} {tot_post_loc:9} "
          f"{tot_pre_cc:8} {tot_post_cc:9} {tot_pre_dp:10} {tot_post_dp:11}")

if __name__ == "__main__":
    main()
