import re
import subprocess
import streamlit as st
import json
import requests

def run_homplexity_analysis(file_path):
    cmd = ["homplexity-cli", "--severity", "Debug", file_path]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        # st.error(f"Homplexity failed on {file_path}:\n{e.stderr or e.stdout}")
        # return {"cyclomatic_complexity": {"min":0,"max":0,"average":0,"sum":0}, "homplexity_loc" : 0, "homplexity_output": e.stderr or e.stdout}
        OPENROUTER_API_KEY = "Your API Key"
        with open(file_path, "r") as f:
            code_to_analyze = f.read()
        
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            # data=json.dumps({
            #     "model": "openai/o3-mini-high",
            #     "messages": [
            #     {
            #         "role": "user",
            #         "content": """
            #             "Analyze the following Haskell code and return a JSON object with the cyclomatic complexity of each function. "
            #             "The JSON should have the function names as keys and their cyclomatic complexity as values. "
            #             "Also, include the computed minimum, maximum, average, and sum of these values as additional keys (min, max, average, sum). "
            #             "also caluculate how many Lines of code"
            #             "Here is the code:\n\n" 
            #             """ + code_to_analyze + """
            #             "\n\nOutput your results in JSON format exactly as follows (do not output any additional text):"
            #             "{"
            #             "   \"cyclomatic_complexity\": {"
            #             "       \"min\": 0,
            #             "       \"max\": 0,
            #             "       \"average\": 0,
            #             "       \"sum\": 0
            #             "   },"
            #             "   \"homplexity_loc\" : 0,
            #             "   \"homplexity_output\" : ""      
            #             "}"
            #         """
            #     }
            #     ],
                
            # })
            data=json.dumps({
                # "model": "openai/o3-mini-high",
                "model": "openai/gpt-4o-2024-11-20",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a code analysis assistant specialized in Haskell. Analyze Haskell code and return JSON outputs. Do not return any additional explanation or text besides the JSON object. Your output must strictly follow the provided format."
                    },
                    {
                        "role": "user",
                        "content": (
                            "Analyze the following Haskell code and return a JSON object with the cyclomatic complexity of each function. "
                            "The JSON should have the function names as keys and their cyclomatic complexity as values. "
                            "Also, include the computed minimum, maximum, average, and sum of these values as additional keys (min, max, average, sum). "
                            "Also calculate how many Lines of Code are in the input. "
                            "Here is the code:\n\n" + code_to_analyze + "\n\n"
                            "Output your results in JSON format exactly as follows (do not output any additional text):\n"
                            "{\n"
                            '    "cyclomatic_complexity": {\n'
                            '        "min": 0,\n'
                            '        "max": 0,\n'
                            '        "average": 0,\n'
                            '        "sum": 0\n'
                            "    },\n"
                            '    "homplexity_loc": 0,\n'
                            '    "homplexity_output": ""\n'
                            "}"
                        )
                    }
                ],
            })
        )
        response.raise_for_status()
        result = response.json()

        # The API returns the content as a JSON string, so we need to parse it.
        if 'choices' not in result:
            raise ValueError(f"Unexpected response format: {json.dumps(result, indent=2)}")

        content_str = result['choices'][0]['message']['content']
        if content_str.startswith("```json"):
            content_str = content_str.strip("```json").strip("```")

        try:
            parsed_content = json.loads(content_str)

            cc = parsed_content.get("cyclomatic_complexity", {})
            final_metrics = {
                "cyclomatic_complexity": {
                    "min": int(cc.get("min", 0)),
                    "max": int(cc.get("max", 0)),
                    "average": round(cc.get("average", 0)),
                    "sum": int(cc.get("sum", 0)),
                },
                "homplexity_loc": int(parsed_content.get("homplexity_loc", 0)),
                "homplexity_output": content_str
            }
            return final_metrics
        except Exception as e:
            # st.error("Error parsing JSON: " + str(e))
            # raise ValueError(f"Failed to parse content as JSON: {content_str}") from e
            # parsed_content = {}
            return {
                "cyclomatic_complexity": {"min": 0, "max": 0, "average": 0, "sum": 0},
                "homplexity_loc": 0,
                "homplexity_output": content_str  # helpful for debugging
            }

        # # Use parsed_content instead of directly indexing the string.
        # st.success(parsed_content.get('cyclomatic_complexity', {}).get('sum', 'No sum found'))

        # final_metrics = {
        #     "cyclomatic_complexity": {
        #         "min": int(parsed_content['cyclomatic_complexity']['min']),
        #         "max": int(parsed_content['cyclomatic_complexity']['max']),
        #         "average": round(parsed_content['cyclomatic_complexity']['average']),
        #         "sum": int(parsed_content['cyclomatic_complexity']['sum'])
        #     },
        #     "homplexity_loc": int(parsed_content['homplexity_loc']),
        #     "homplexity_output": content_str
        # }

        # return final_metrics
        # response.raise_for_status()
        # result = response.json()
        # st.success(result['choices'][0]['message']['content']['cyclomatic_complexity']['sum'])
        # return {
        #     "cyclomatic_complexity": {
        #         "min": int(result['choices'][0]['message']['content']['cyclomatic_complexity']['min']),
        #         "max": int(result['choices'][0]['message']['content']['cyclomatic_complexity']['max']),
        #         "average": round(result['choices'][0]['message']['content']['cyclomatic_complexity']['average']),
        #         "sum": int(result['choices'][0]['message']['content']['cyclomatic_complexity']['sum'])
        #     },
        #     "homplexity_loc" : int(result['choices'][0]['message']['content']['homplexity_loc']),
        #     "homplexity_output" : result['choices'][0]['message']['content']
        # }
        # return result['choices'][0]['message']['content']
    output_text = result.stdout
    cc_values = []
    loc_values = []
    for line in output_text.splitlines():
        line = line.strip()
        if not line or ":SrcLoc" not in line:
            continue
        # m = re.search(r'cyclomatic complexity of (\d+)', line)
        m = re.search(r'cyclomatic complexity of (\d+)', line)
        loc = re.search(r'(\d+) lines of code', line)
        if m:
            cc_values.append(int(m.group(1)))
        if loc:
            loc_values.append(int(loc.group(1)))
    if cc_values:
        return {
            "cyclomatic_complexity": {
                "min": min(cc_values),
                "max": max(cc_values),
                "average": sum(cc_values)/len(cc_values),
                "sum": sum(cc_values)
            },
            "homplexity_loc" : sum(loc_values),
            "homplexity_output" : output_text
        }
    else:
        return {"cyclomatic_complexity": {"min":0,"max":0,"average":0,"sum":0}, "homplexity_loc" : 0, "homplexity_output": "error"}
