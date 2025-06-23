# refactor.py
import streamlit as st
import re
import requests
import os
from pathlib import Path
import subprocess
import json
from analysis import analyze_code_string, calculate_code_quality
from homplexity_analysis import run_homplexity_analysis

def call_openrouter_api(prompt, code_snippet):
    model = "model2"
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "Your API key")
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    get_model = {
            "model1": "openai/gpt-4o-2024-11-20",
            "model2": "deepseek/deepseek-r1",
            "model3": "deepseek/deepseek-r1-distill-llama-70b",
            "model4": "deepseek/deepseek-r1-distill-llama-70b",
            "model5": "openai/chatgpt-4o-latest",
            "model6": "anthropic/claude-3.7-sonnet"
        }.get(model, "openai/chatgpt-4o-latest")
    payload = {
        "model": get_model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": code_snippet}
        ]
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()
    return result['choices'][0]['message']['content']

# ============================================
# HLint Parsing Functions
# ============================================
def parse_hlint_output(hlint_output):
    """
    Parses HLint output to extract suggestion details.
    Returns a list of dictionaries with keys: location, suggestion_title, found_block, perhaps_block.
    """
    suggestions = []
    pattern_suggestion = re.compile(
        r"^(?P<location>.+\.hs:\(\d+,\d+\)-\(\d+,\d+\)): Suggestion: (?P<title>.*)$"
    )
    lines = hlint_output.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        match = pattern_suggestion.match(line)
        if match:
            location = match.group("location")
            suggestion_title = match.group("title").strip()
            found_block = []
            perhaps_block = []
            i += 1
            found_mode = False
            perhaps_mode = False
            while i < len(lines):
                current_line = lines[i].rstrip("\n")
                if pattern_suggestion.match(current_line):
                    i -= 1
                    break
                if current_line.startswith("Found"):
                    found_mode = True
                    perhaps_mode = False
                    i += 1
                    continue
                elif current_line.startswith("Perhaps"):
                    found_mode = False
                    perhaps_mode = True
                    i += 1
                    continue
                elif current_line.strip() == "":
                    i += 1
                    break
                else:
                    if found_mode:
                        found_block.append(current_line)
                    elif perhaps_mode:
                        perhaps_block.append(current_line)
                i += 1
            suggestions.append({
                "location": location,
                "suggestion_title": suggestion_title,
                "found_block": found_block,
                "perhaps_block": perhaps_block
            })
        i += 1
    return suggestions

def get_hlint_suggestions(code_str, file_identifier="temp_code.hs"):
    """
    Writes code_str to a temporary file, runs HLint, and parses its output.
    Ensures the directory for the temporary file exists.
    """
    # dir_name = os.path.dirname(file_identifier)
    # if dir_name and not os.path.exists(dir_name):
    #     os.makedirs(dir_name, exist_ok=True)
    # with open(file_identifier, "w") as f:
    #     f.write(code_str)
    try:
        result = subprocess.run(["hlint", file_identifier],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True)
        output = result.stdout
        # os.remove(file_identifier)
        return parse_hlint_output(output)
    except Exception as e:
        st.error(f"Error running HLint: {e}")
        return []

def get_hlint_refactorings(code_str, file_identifier="temp_code.hs"):
    """
    Writes code_str to a temporary file, runs HLint with --refactor, and returns the refactored code.
    Ensures the directory for the temporary file exists.
    """
    dir_name = os.path.dirname(file_identifier)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)
    
    # Write the code to a temporary file
    with open(file_identifier, "w") as f:
        f.write(code_str)
    
    try:
        # Run HLint with --refactor option to get suggested refactorings
        result = subprocess.run(
            ["hlint", "--refactor", file_identifier],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        refactored_code = result.stdout
        
        # Clean up by removing the temporary file
        os.remove(file_identifier)
        
        return refactored_code
    
    except Exception as e:
        print(f"Error running HLint with --refactor: {e}")
        return code_str  # Return the original code if refactoring fails

def run_hlint(file_path):
    cmd = ["hlint", "--json", file_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)


def clean_json_output(output):
    output = output.strip()
    if output.startswith("```"):
        lines = output.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        output = "\n".join(lines)
    return output

def analyze_suggestions(prompt_text, suggestions_input, full_code):
    # suggestions_input may be empty (LLM-only) or contain static suggestions.
    input_text = ""
    # if suggestions_input:
    #     for s in suggestions_input:
    #         input_text += f"{s['location']}: Suggestion: {s['suggestion_title']}\n"
    #         input_text += "Found\n" + "\n".join(s['found_block']) + "\n"
    #         input_text += "Perhaps\n" + "\n".join(s['perhaps_block']) + "\n\n"

    hw_suggestions = ""
    if suggestions_input:
        for s in suggestions_input:
            hw_suggestions += f"{s['location']}: Suggestion: {s['suggestion_title']}\n"
            hw_suggestions += "Found\n" + "\n".join(s['found_block']) + "\n"
            hw_suggestions += "Perhaps\n" + "\n".join(s['perhaps_block']) + "\n\n"
    
        prompt_text = prompt_text.replace("HW_SUGGESTIONS", hw_suggestions)
    # Append full code context
    input_text += "\nFull Code:\n" + full_code
    output = call_openrouter_api(prompt_text, input_text)
    cleaned_output = clean_json_output(output)
    try:
        final_json = json.loads(cleaned_output)
        return final_json.get("final_candidates", [])
    except Exception as e:
        # st.error("Error parsing Analyzer Agent output: " + str(e))
        return []

def apply_refactoring(original_code, candidate_code, suggestion):
        if candidate_code in original_code:
            return original_code.replace(candidate_code, suggestion)
        else:
            return original_code

def refactor_files(analysis_results, project_dir):
    post_analysis = {
        "static": {
            "one_shot": {
                "overall": {}, 
                "files": []
            }
        },
        "hybrid": {
            "one_shot": {
                "overall": {}, 
                "files": []
            }
        }
    }

    static_total_loc = 0
    llm_only_total_loc = 0
    hybrid_total_loc = 0

    static_total_homplexity_loc = 0
    llm_only_total_homplexity_loc = 0
    hybrid_total_homplexity_loc = 0

    static_cc_min_vals = []
    static_cc_max_vals = []
    static_cc_average_vals = []
    static_cc_sum_vals = []

    llm_only_cc_min_vals = []
    llm_only_cc_max_vals = []
    llm_only_cc_average_vals = []
    llm_only_cc_sum_vals = []

    hybrid_cc_min_vals = []
    hybrid_cc_max_vals = []
    hybrid_cc_average_vals = []
    hybrid_cc_sum_vals = []

    static_hlint_summary = {"error": 0, "warning": 0, "suggestion": 0, "ignore": 0, "total": 0}
    llm_only_hlint_summary = {"error": 0, "warning": 0, "suggestion": 0, "ignore": 0, "total": 0}
    hybrid_hlint_summary = {"error": 0, "warning": 0, "suggestion": 0, "ignore": 0, "total": 0}

    static_total_syntax_errors = 0
    llm_only_total_syntax_errors = 0
    hybrid_total_syntax_errors = 0
    for file in analysis_results["pre_refactor"]["files"]:
        original_code = file["original_code"]
        # post_analysis_results["static"]["one_shot"]["overall"]
        # post_analysis_results["static"]["one_shot"]["files"]
        # project_dir = Path(project_dir)
        # current_file = Path(file)

        # # Insert "refactored" between the project directory and the remaining path
        # file = project_dir / "refactored" / current_file.relative_to(project_dir)
        file_name = file["file_name"]

        # --- Block 1: Static Suggestions (HLint+Weeder) ---
        hlint_suggestions = get_hlint_suggestions(original_code, file_identifier=file_name)
        # weeder_suggestions = get_weeder_suggestions(code)
        # static_suggestions = hlint_suggestions + weeder_suggestions
        static_suggestions = hlint_suggestions
        if not static_suggestions:
            # st.info("No static suggestions found.")
            static_suggestions = [{
                "location": file_name,
                "suggestion_title": "No suggestions",
                "found_block": ["-- Manual candidate snippet"],
                "perhaps_block": []
            }]
        # else:
            # st.info(f"Found {len(static_suggestions)} static suggestion(s).")
        
        # --- Block 1: refactoring Suggestions (HLint+Weeder) ---
        updated_code_static = original_code
        # if static_suggestions:
        #     updated_code_static = get_hlint_refactorings(code)
        updated_code_static = get_hlint_refactorings(original_code)

        # static_refactored_file = file.get("refactored_code", {}).get("static_refactored_file", "")
        static_refactored_file = file["refactored_code"]["static_refactored_file"]
        os.remove(static_refactored_file)
        # Write the code to a static refactored directory file
        with open(static_refactored_file, "w") as f:
            f.write(updated_code_static)

        
        static_loc = len(updated_code_static.splitlines())
        static_total_loc += static_loc
        
        hlint_issues = run_hlint(static_refactored_file)

        file_hlint = {"error": 0, "warning": 0, "suggestion": 0, "ignore": 0, "total": len(hlint_issues)}
        for issue in hlint_issues:
            hint = issue.get("severity", "").lower()
            if "error" in hint:
                file_hlint["error"] += 1
            elif "warning" in hint:
                file_hlint["warning"] += 1
            elif "suggestion" in hint:
                file_hlint["suggestion"] += 1
            elif "ignore" in hint:
                file_hlint["ignore"] += 1
        
        static_syntax_errors = subprocess.run(["ghc", "-fno-code", static_refactored_file], capture_output=True, text=True)
        # err_count = 1 if syntax_errors.returncode != 0 else 0
        # total_syntax_errors += err_count
        static_error_lines = static_syntax_errors.stderr.split("\n")  # Split output into lines
        static_err_count = sum(1 for line in static_error_lines if "error:" in line)  # Count error occurrences
        static_total_syntax_errors += static_err_count

        static_homplexity_data = run_homplexity_analysis(static_refactored_file)
        static_cc_min = static_homplexity_data.get("cyclomatic_complexity", {}).get("min", 0)
        static_cc_max = static_homplexity_data.get("cyclomatic_complexity", {}).get("max", 0)
        static_cc_average = static_homplexity_data.get("cyclomatic_complexity", {}).get("average", 0)
        static_cc_sum = static_homplexity_data.get("cyclomatic_complexity", {}).get("sum", 0)
        static_cc_min_vals.append(static_cc_min)
        static_cc_max_vals.append(static_cc_max)
        static_cc_average_vals.append(static_cc_average)
        static_cc_sum_vals.append(static_cc_sum)

        static_homplexity_loc = static_homplexity_data.get("homplexity_loc", 0)
        static_total_homplexity_loc += static_homplexity_loc

        # quality_score = calculate_code_quality(loc, cc)
        static_quality_score = calculate_code_quality(static_homplexity_loc, static_cc_sum)

        static_file_metrics = {
            "file_name": file_name,
            "refactored_file_name": static_refactored_file,
            "cyclomatic_complexity": static_homplexity_data.get("cyclomatic_complexity", {"min":0,"max":0,"average":0,"sum":0}),
            "hlint_suggestions": file_hlint,
            "syntax_errors": static_err_count,
            "lines_of_code": static_loc,
            "homplexity_lines_of_code": static_homplexity_loc,
            "code_quality_score": static_quality_score,
            "test_coverage": 80,  # Placeholder
            "performance": {"memory_usage": "10MB", "runtime": "0.5s"},  # Placeholder
            "security_vulnerabilities": 0,  # Placeholder
            "homplexity_analysis": static_homplexity_data,
            "original_code": original_code,
            "suggestions": static_suggestions,
            "refactored_code": updated_code_static
        }
        static_hlint_summary["suggestion"] += file_hlint["suggestion"]
        static_hlint_summary["error"] += file_hlint["error"]
        static_hlint_summary["warning"] += file_hlint["warning"]
        static_hlint_summary["ignore"] += file_hlint["ignore"]
        static_hlint_summary["total"] += file_hlint["total"]

        post_analysis["static"]["one_shot"]["files"].append(static_file_metrics)


        # prompt = "Please refactor the following Haskell code to improve readability, performance, and style without changing functionality."
        # refactored = call_openrouter_api(prompt, original_code, api_key)
        # file["refactored_code"] = refactored
        # # Dynamically re-analyze the refactored code:
        # file["post_analysis"] = analyze_code_string(refactored, file["file_name"])
        # file["suggestions"] = [{
        #     "target_snippet": original_code[:100] + "...",
        #     "refactored_suggestion": refactored[:100] + "...",
        #     "confidence": 0.95,
        #     "justification": "LLM refactoring applied using one-shot prompt."
        # }]

        # llm only refactroing start sp
        try:
            with open("analyzer_agent_prompt_d.txt", "r") as f:
                analyzer_combined_prompt = f.read()
        except Exception as e:
            st.error(f"Error reading analyzer prompt: {e}")
            analyzer_combined_prompt = ""
        

        final_candidates_combined = analyze_suggestions(analyzer_combined_prompt, static_suggestions, original_code)

        updated_code_combined = original_code



        st.session_state["final_candidates_combined"] = final_candidates_combined
        if final_candidates_combined:
            # st.success("Combined Analyzer produced candidate suggestion(s):")
            # for fc in final_candidates_combined:
            #     st.markdown("**Target Snippet:**")
            #     st.code(fc["target_snippet"], language="haskell")
            #     st.markdown("**Refactored Suggestion:**")
            #     st.code(fc["refactored_suggestion"], language="haskell")
            #     st.markdown("**Justification:**")
            #     st.markdown(fc["justification"])
            
            for candidate in final_candidates_combined:
                target_snippet = candidate.get("target_snippet", "")
                refactored_suggestion = candidate.get("refactored_suggestion", "")
                if target_snippet and refactored_suggestion:
                    updated_code_combined = apply_refactoring(updated_code_combined, target_snippet, refactored_suggestion)
                # else:
                    # st.error("Combined suggestion missing fields.")
                
            combined_refactored_file = file["refactored_code"]["hybrid_refactored_file"]
            os.remove(combined_refactored_file)
            # Write the code to a static refactored directory file
            with open(combined_refactored_file, "w") as f:
                f.write(updated_code_combined)

            hybrid_loc = len(updated_code_combined.splitlines())
            hybrid_total_loc += hybrid_loc
            
            hlint_issues = run_hlint(combined_refactored_file)

            file_hlint = {"error": 0, "warning": 0, "suggestion": 0, "ignore": 0, "total": len(hlint_issues)}
            for issue in hlint_issues:
                hint = issue.get("severity", "").lower()
                if "error" in hint:
                    file_hlint["error"] += 1
                elif "warning" in hint:
                    file_hlint["warning"] += 1
                elif "suggestion" in hint:
                    file_hlint["suggestion"] += 1
                elif "ignore" in hint:
                    file_hlint["ignore"] += 1
            
            hybrid_syntax_errors = subprocess.run(["ghc", "-fno-code", combined_refactored_file], capture_output=True, text=True)
            # err_count = 1 if syntax_errors.returncode != 0 else 0
            # total_syntax_errors += err_count
            hybrid_error_lines = hybrid_syntax_errors.stderr.split("\n")  # Split output into lines
            hybrid_err_count = sum(1 for line in hybrid_error_lines if "error:" in line)  # Count error occurrences
            hybrid_total_syntax_errors += hybrid_err_count

            hybrid_homplexity_data = run_homplexity_analysis(combined_refactored_file)
            hybrid_cc_min = hybrid_homplexity_data.get("cyclomatic_complexity", {}).get("min", 0)
            hybrid_cc_max = hybrid_homplexity_data.get("cyclomatic_complexity", {}).get("max", 0)
            hybrid_cc_average = hybrid_homplexity_data.get("cyclomatic_complexity", {}).get("average", 0)
            hybrid_cc_sum = hybrid_homplexity_data.get("cyclomatic_complexity", {}).get("sum", 0)
            hybrid_cc_min_vals.append(hybrid_cc_min)
            hybrid_cc_max_vals.append(hybrid_cc_max)
            hybrid_cc_average_vals.append(hybrid_cc_average)
            hybrid_cc_sum_vals.append(hybrid_cc_sum)

            hybrid_homplexity_loc = hybrid_homplexity_data.get("homplexity_loc", 0)
            hybrid_total_homplexity_loc += hybrid_homplexity_loc

            # quality_score = calculate_code_quality(loc, cc)
            hybrid_quality_score = calculate_code_quality(hybrid_homplexity_loc, hybrid_cc_sum)

            hybrid_file_metrics = {
                "file_name": file_name,
                "refactored_file_name": combined_refactored_file,
                "cyclomatic_complexity": hybrid_homplexity_data.get("cyclomatic_complexity", {"min":0,"max":0,"average":0,"sum":0}),
                "hlint_suggestions": file_hlint,
                "syntax_errors": hybrid_err_count,
                "lines_of_code": hybrid_loc,
                "homplexity_lines_of_code": hybrid_homplexity_loc,
                "code_quality_score": hybrid_quality_score,
                "test_coverage": 80,  # Placeholder
                "performance": {"memory_usage": "10MB", "runtime": "0.5s"},  # Placeholder
                "security_vulnerabilities": 0,  # Placeholder
                "homplexity_analysis": hybrid_homplexity_data,
                "original_code": original_code,
                "suggestions": final_candidates_combined,
                "refactored_code": updated_code_combined
            }
            hybrid_hlint_summary["suggestion"] += file_hlint["suggestion"]
            hybrid_hlint_summary["error"] += file_hlint["error"]
            hybrid_hlint_summary["warning"] += file_hlint["warning"]
            hybrid_hlint_summary["ignore"] += file_hlint["ignore"]
            hybrid_hlint_summary["total"] += file_hlint["total"]

            post_analysis["hybrid"]["one_shot"]["files"].append(hybrid_file_metrics)
        # else:
        #     st.error("Combined Analyzer did not produce any candidate.")

        
        

        # llm only refactoring end sp
    
    static_overall_cc = {"min": sum(static_cc_min_vals) if static_cc_min_vals else 0,
                  "max": sum(static_cc_max_vals) if static_cc_max_vals else 0,
                  "average": sum(static_cc_sum_vals)/len(static_cc_sum_vals) if static_cc_sum_vals else 0,
                  "sum": sum(static_cc_sum_vals) if static_cc_sum_vals else 0}
    # overall_quality = calculate_code_quality(total_loc, overall_cc.get("sum", 0))
    static_overall_quality = calculate_code_quality(static_total_homplexity_loc, static_overall_cc.get("sum", 0))

    post_analysis["static"]["one_shot"]["overall"] = {
        "cyclomatic_complexity": static_overall_cc,
        "hlint_suggestions": static_hlint_summary,
        "syntax_errors": static_total_syntax_errors,
        "lines_of_code": static_total_loc,
        "homplexity_lines_of_code": static_total_homplexity_loc,
        "code_quality_score": static_overall_quality,
        "test_coverage": 80,  # Placeholder
        "performance": {"memory_usage": "150MB", "runtime": "2.3s"},  # Placeholder
        "security_vulnerabilities": 2  # Placeholder
    }

    hybrid_overall_cc = {"min": sum(hybrid_cc_min_vals) if hybrid_cc_min_vals else 0,
                  "max": sum(hybrid_cc_max_vals) if hybrid_cc_max_vals else 0,
                  "average": sum(hybrid_cc_sum_vals)/len(hybrid_cc_sum_vals) if hybrid_cc_sum_vals else 0,
                  "sum": sum(hybrid_cc_sum_vals) if hybrid_cc_sum_vals else 0}
    # overall_quality = calculate_code_quality(total_loc, overall_cc.get("sum", 0))
    hybrid_overall_quality = calculate_code_quality(hybrid_total_homplexity_loc, hybrid_overall_cc.get("sum", 0))

    post_analysis["hybrid"]["one_shot"]["overall"] = {
        "cyclomatic_complexity": hybrid_overall_cc,
        "hlint_suggestions": hybrid_hlint_summary,
        "syntax_errors": hybrid_total_syntax_errors,
        "lines_of_code": hybrid_total_loc,
        "homplexity_lines_of_code": hybrid_total_homplexity_loc,
        "code_quality_score": hybrid_overall_quality,
        "test_coverage": 80,  # Placeholder
        "performance": {"memory_usage": "150MB", "runtime": "2.3s"},  # Placeholder
        "security_vulnerabilities": 2  # Placeholder
    }




    # llm only refactoring

    return post_analysis
