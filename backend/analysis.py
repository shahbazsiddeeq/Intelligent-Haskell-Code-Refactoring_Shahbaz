import subprocess
import json
import os
import tempfile
import re
from pathlib import Path
from homplexity_analysis import run_homplexity_analysis

def run_hlint(file_path):
    cmd = ["hlint", "--json", file_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

def analyze_project(project_dir, source_files):
    analysis = {"pre_refactor": {"overall": {}, "files": []}, "post_refactor": {}}
    total_loc = 0
    total_homplexity_loc = 0
    cc_min_vals = []
    cc_max_vals = []
    cc_average_vals = []
    cc_sum_vals = []
    hlint_summary = {"error": 0, "warning": 0, "suggestion": 0, "ignore": 0, "total": 0}
    total_syntax_errors = 0

    for file in source_files:
        with open(file, "r") as f:
            code = f.read()
        loc = len(code.splitlines())
        total_loc += loc

        # u_project_dir = Path(project_dir)
        # u_file = Path(file)
        u_project_dir = Path(project_dir)
        u_file = Path(file)


        static_refactored_file = str(u_project_dir.parent / "static_refactored" / u_file.relative_to(u_project_dir))
        llm_only_refactored_file = str(u_project_dir.parent / "llm_only_refactored" / u_file.relative_to(u_project_dir))
        hybrid_refactored_file = str(u_project_dir.parent / "hybrid_refactored" / u_file.relative_to(u_project_dir))

        hlint_issues = run_hlint(file)
        # print(hlint_issues)
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

        syntax_errors = subprocess.run(["ghc", "-fno-code", file], capture_output=True, text=True)
        # err_count = 1 if syntax_errors.returncode != 0 else 0
        # total_syntax_errors += err_count
        error_lines = syntax_errors.stderr.split("\n")  # Split output into lines
        err_count = sum(1 for line in error_lines if "error:" in line)  # Count error occurrences
        total_syntax_errors += err_count

        homplexity_data = run_homplexity_analysis(file)
        cc_min = homplexity_data.get("cyclomatic_complexity", {}).get("min", 0)
        cc_max = homplexity_data.get("cyclomatic_complexity", {}).get("max", 0)
        cc_average = homplexity_data.get("cyclomatic_complexity", {}).get("average", 0)
        cc_sum = homplexity_data.get("cyclomatic_complexity", {}).get("sum", 0)
        cc_min_vals.append(cc_min)
        cc_max_vals.append(cc_max)
        cc_average_vals.append(cc_average)
        cc_sum_vals.append(cc_sum)

        homplexity_loc = homplexity_data.get("homplexity_loc", 0)
        total_homplexity_loc += homplexity_loc

        # quality_score = calculate_code_quality(loc, cc)
        quality_score = calculate_code_quality(homplexity_loc, cc_sum)

        file_metrics = {
            "file_name": file,
            "cyclomatic_complexity": homplexity_data.get("cyclomatic_complexity", {"min":0,"max":0,"average":0,"sum":0}),
            "hlint_suggestions": file_hlint,
            "syntax_errors": err_count,
            "lines_of_code": loc,
            "homplexity_lines_of_code": homplexity_loc,
            "code_quality_score": quality_score,
            "test_coverage": 80,  # Placeholder
            "performance": {"memory_usage": "10MB", "runtime": "0.5s"},  # Placeholder
            "security_vulnerabilities": 0,  # Placeholder
            "homplexity_analysis": homplexity_data,
            "original_code": code,
            "suggestions": hlint_issues,
            "refactored_code": {"static_refactored_file": static_refactored_file, "llm_only_refactored_file": llm_only_refactored_file, "hybrid_refactored_file": hybrid_refactored_file}
        }
        hlint_summary["suggestion"] += file_hlint["suggestion"]
        hlint_summary["error"] += file_hlint["error"]
        hlint_summary["warning"] += file_hlint["warning"]
        hlint_summary["ignore"] += file_hlint["ignore"]
        hlint_summary["total"] += file_hlint["total"]

        analysis["pre_refactor"]["files"].append(file_metrics)

    overall_cc = {"min": sum(cc_min_vals) if cc_min_vals else 0,
                  "max": sum(cc_max_vals) if cc_max_vals else 0,
                  "average": sum(cc_sum_vals)/len(cc_sum_vals) if cc_sum_vals else 0,
                  "sum": sum(cc_sum_vals) if cc_sum_vals else 0}
    # overall_quality = calculate_code_quality(total_loc, overall_cc.get("sum", 0))
    overall_quality = calculate_code_quality(total_homplexity_loc, overall_cc.get("sum", 0))

    analysis["pre_refactor"]["overall"] = {
        "cyclomatic_complexity": overall_cc,
        "hlint_suggestions": hlint_summary,
        "syntax_errors": total_syntax_errors,
        "lines_of_code": total_loc,
        "homplexity_lines_of_code": total_homplexity_loc,
        "code_quality_score": overall_quality,
        "test_coverage": 80,  # Placeholder
        "performance": {"memory_usage": "150MB", "runtime": "2.3s"},  # Placeholder
        "security_vulnerabilities": 2  # Placeholder
    }
    return analysis

def analyze_code_string(code_str, file_name="temp.hs"):
    with tempfile.NamedTemporaryFile(suffix=".hs", delete=False, mode="w") as tmp:
        tmp.write(code_str)
        tmp_path = tmp.name

    loc = len(code_str.splitlines())
    hlint_issues = run_hlint(tmp_path)
    file_hlint = {"style": 0, "performance": 0, "redundancy": 0, "total": len(hlint_issues)}
    for issue in hlint_issues:
        hint = issue.get("hint", "").lower()
        if "style" in hint:
            file_hlint["style"] += 1
        elif "performance" in hint:
            file_hlint["performance"] += 1
        elif "redundant" in hint or "duplicate" in hint:
            file_hlint["redundancy"] += 1

    syntax_errors = subprocess.run(["ghc", "-fno-code", tmp_path], capture_output=True, text=True)
    err_count = 1 if syntax_errors.returncode != 0 else 0

    homplexity_data = run_homplexity_analysis(tmp_path)
    cc = homplexity_data.get("cyclomatic_complexity", {}).get("sum", 0)

    quality_score = calculate_code_quality(loc, cc)

    os.remove(tmp_path)

    return {
        "file_name": file_name,
        "cyclomatic_complexity": homplexity_data.get("cyclomatic_complexity", {"min":0,"max":0,"average":0,"sum":0}),
        "hlint_suggestions": file_hlint,
        "syntax_errors": err_count,
        "lines_of_code": loc,
        "code_quality_score": quality_score,
        "test_coverage": 80,  # Placeholder
        "performance": {"memory_usage": "10MB", "runtime": "0.5s"},  # Placeholder
        "security_vulnerabilities": 0,  # Placeholder
        "homplexity_analysis": homplexity_data,
        "original_code": code_str,
        "suggestions": [],
        "refactored_code": ""
    }

def calculate_code_quality(loc, cc, max_penalty=100):
    penalty = ((cc * 2) + (loc * 0.1)) / max_penalty * 100
    quality_score = max(0, 100 - penalty)
    return round(quality_score, 2)
