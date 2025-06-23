# report.py
import json

def generate_report(analysis_results, project_name="ExampleProject"):
    # report = {
    #     "project_name": project_name,
    #     "analysis": {
    #         "pre_refactor": analysis_results["pre_refactor"],
    #         "post_refactor": {
    #             "static": {
    #                 "zero_shot": {},
    #                 "one_shot": generate_post_overall(analysis_results["pre_refactor"]["files"]),
    #                 "chain_of_thought": {}
    #             },
    #             "llm_only": {
    #                 "zero_shot": {},
    #                 "one_shot": generate_post_overall(analysis_results["pre_refactor"]["files"]),
    #                 "chain_of_thought": {}
    #             },
    #             "hybrid": {
    #                 "zero_shot": {},
    #                 "one_shot": generate_post_overall(analysis_results["pre_refactor"]["files"]),
    #                 "chain_of_thought": {}
    #             }
    #         }
    #     }
    # }
    report = {
        "project_name": project_name,
        "analysis": {
            "pre_refactor": analysis_results["pre_refactor"],
            "post_refactor": {
                "static": {
                    "zero_shot": {},
                    "one_shot": analysis_results["post_refactor"]["static"]["one_shot"],
                    "chain_of_thought": {}
                },
                "llm_only": {
                    "zero_shot": {},
                    "one_shot": {},
                    "chain_of_thought": {}
                },
                "hybrid": {
                    "zero_shot": {},
                    "one_shot": analysis_results["post_refactor"]["hybrid"]["one_shot"],
                    "chain_of_thought": {}
                }
            }
        }
    }
    return json.dumps(report, indent=2)

def generate_post_overall(file_list):
    total_loc = sum(f["post_analysis"]["lines_of_code"] for f in file_list if "post_analysis" in f)
    cc_vals = [f["post_analysis"]["cyclomatic_complexity"]["sum"] for f in file_list if "post_analysis" in f]
    overall_cc = {"min": min(cc_vals) if cc_vals else 0,
                  "max": max(cc_vals) if cc_vals else 0,
                  "average": sum(cc_vals)/len(cc_vals) if cc_vals else 0,
                  "sum": sum(cc_vals) if cc_vals else 0}
    total_syntax_errors = sum(f["post_analysis"]["syntax_errors"] for f in file_list if "post_analysis" in f)
    avg_quality = round(sum(f["post_analysis"]["code_quality_score"] for f in file_list if "post_analysis" in f) / len(file_list), 2) if file_list else 0

    overall = {
        "cyclomatic_complexity": overall_cc,
        "hlint_suggestions": {},  # Aggregation logic can be added as needed
        "syntax_errors": total_syntax_errors,
        "lines_of_code": total_loc,
        "code_quality_score": avg_quality,
        "test_coverage": 80,  # Placeholder
        "performance": {"memory_usage": "130MB", "runtime": "1.8s"},  # Placeholder
        "security_vulnerabilities": 1  # Placeholder
    }
    return {"overall": overall, "files": [f["post_analysis"] for f in file_list if "post_analysis" in f]}
