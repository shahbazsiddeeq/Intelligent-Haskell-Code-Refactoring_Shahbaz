import streamlit as st
import json
import re
import pandas as pd

st.title("Refactor Analysis Metrics with Improvement %")

# File uploader
uploaded_file = st.file_uploader("Upload analysis JSON", type="json")
if not uploaded_file:
    st.info("Please upload a JSON file to begin.")
    st.stop()

# Load JSON
data = json.load(uploaded_file)

def extract_entries(data, key_path):
    entry = data
    for key in key_path:
        entry = entry.get(key, {})
    return entry if isinstance(entry, list) else []

def get_file_cc(f):
    cc = f.get("cyclomatic_complexity", 0)
    if isinstance(cc, dict):
        return cc.get("sum", 0)
    return cc

def get_file_depth(f):
    raw = f.get("homplexity_analysis", {}).get("homplexity_output", "")
    if isinstance(raw, dict):
        raw = raw.get("output_text", "")
    if "\\n" in raw and "\n" not in raw:
        raw = raw.replace("\\n", "\n")
    max_d = 0
    for line in raw.splitlines():
        if "branching depth" in line.lower():
            m = re.search(r'branching depth of\s+(\d+)', line.lower())
            if m:
                max_d = max(max_d, int(m.group(1)))
    return max_d

def get_file_sugs(f):
    hl = f.get("hlint_suggestions", {})
    return hl.get("error", 0) + hl.get("suggestion", 0) + hl.get("ignore", 0)

def get_file_warns(f):
    return f.get("hlint_suggestions", {}).get("warning", 0)

def get_file_syntax(f):
    return f.get("syntax_errors", 0)

# Extract pre and post entries
pre_files = extract_entries(data, ["analysis", "pre_refactor", "files"])
post_files = extract_entries(data, ["analysis", "post_refactor", "hybrid", "one_shot", "files"])

# Build metrics
records = []
for f in pre_files:
    name = f["file_name"]
    pre = {
        "loc": f.get("lines_of_code", 0),
        "cc": get_file_cc(f),
        "depth": get_file_depth(f),
        "sug": get_file_sugs(f),
        "warn": get_file_warns(f),
        "syn": get_file_syntax(f)
    }
    post_f = next((x for x in post_files if x["file_name"] == name), None)
    post = {
        "loc": post_f.get("lines_of_code", 0) if post_f else pre["loc"],
        "cc": get_file_cc(post_f) if post_f else pre["cc"],
        "depth": get_file_depth(post_f) if post_f else pre["depth"],
        "sug": get_file_sugs(post_f) if post_f else pre["sug"],
        "warn": get_file_warns(post_f) if post_f else pre["warn"],
        "syn": get_file_syntax(post_f) if post_f else pre["syn"]
    }
    records.append({
        "File": name,
        "LOC Pre": pre["loc"], "LOC Post": post["loc"],
        "CC Pre": pre["cc"], "CC Post": post["cc"],
        "Depth Pre": pre["depth"], "Depth Post": post["depth"],
        "Sug Pre": pre["sug"], "Sug Post": post["sug"],
        "Warn Pre": pre["warn"], "Warn Post": post["warn"],
        "Syn Pre": pre["syn"], "Syn Post": post["syn"],
    })

df = pd.DataFrame(records)

# Calculate improvements
for col in ["LOC", "CC", "Depth", "Sug", "Warn", "Syn"]:
    pre_col = f"{col} Pre"
    post_col = f"{col} Post"
    imp_col = f"{col} Δ%"
    df[imp_col] = ((df[pre_col] - df[post_col]) / df[pre_col].replace({0: pd.NA})) * 100
    df[imp_col] = df[imp_col].round(2).fillna(0)

# Display DataFrame
st.dataframe(df.style.format({
    **{f"{col} Pre": "{:,}" for col in ["LOC", "CC", "Depth", "Sug", "Warn", "Syn"]},
    **{f"{col} Post": "{:,}" for col in ["LOC", "CC", "Depth", "Sug", "Warn", "Syn"]},
    **{f"{col} Δ%": "{:.2f}%" for col in ["LOC", "CC", "Depth", "Sug", "Warn", "Syn"]},
}))

# Totals
totals = df.sum(numeric_only=True)
totals_df = pd.DataFrame(totals).T

st.write("### Totals")
st.dataframe(totals_df.style.format({
    **{f"{col} Pre": "{:,}" for col in ["LOC", "CC", "Depth", "Sug", "Warn", "Syn"]},
    **{f"{col} Post": "{:,}" for col in ["LOC", "CC", "Depth", "Sug", "Warn", "Syn"]},
    **{f"{col} Δ%": "{:.2f}%" for col in ["LOC", "CC", "Depth", "Sug", "Warn", "Syn"]},
}))
