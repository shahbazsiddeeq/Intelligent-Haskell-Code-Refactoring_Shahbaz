import matplotlib.pyplot as plt
import pandas as pd
import json
import streamlit as st

def generate_visuals(final_report):
    report = json.loads(final_report)
    
    pre_files = report["analysis"]["pre_refactor"]["files"]
    post_files = report["analysis"]["post_refactor"]["static"]["one_shot"]["files"]

    if not pre_files or not post_files:
        st.warning("No file data available for visualization.")
        return

    # Create DataFrame for pre- and post-refactoring
    pre_df = pd.DataFrame([{ 
        "File": f["file_name"], 
        "Pre LOC": f["lines_of_code"], 
        "Pre Quality Score": f["code_quality_score"] 
    } for f in pre_files])

    post_df = pd.DataFrame([{ 
        "File": f["file_name"], 
        "Post LOC": f["lines_of_code"], 
        "Post Quality Score": f["code_quality_score"] 
    } for f in post_files])

    # Merge data for comparison
    df = pd.merge(pre_df, post_df, on="File", how="inner")

    # Plot LOC comparison
    st.subheader("Lines of Code: Pre vs Post Refactoring")
    fig, ax = plt.subplots(figsize=(10, 5))
    df.plot(x="File", y=["Pre LOC", "Post LOC"], kind="bar", color=["blue", "green"], ax=ax)
    plt.xticks(rotation=45)
    plt.xlabel("Files")
    plt.ylabel("Lines of Code")
    plt.legend(["Pre Refactor", "Post Refactor"])
    st.pyplot(fig)

    # Plot Code Quality Score comparison
    st.subheader("Code Quality Score: Pre vs Post Refactoring")
    fig, ax = plt.subplots(figsize=(10, 5))
    df.plot(x="File", y=["Pre Quality Score", "Post Quality Score"], kind="bar", color=["blue", "green"], ax=ax)
    plt.xticks(rotation=45)
    plt.xlabel("Files")
    plt.ylabel("Code Quality Score")
    plt.legend(["Pre Refactor", "Post Refactor"])
    st.pyplot(fig)
