# project_ingestion.py
import zipfile
import os
import glob
import subprocess

def ingest_project(uploaded_zip=None, repo_url=None, branch="main"):
    project_dir = None
    if uploaded_zip:
        # project_dir = "/tmp/projects"
        # os.makedirs(project_dir, exist_ok=True)
        base_dir = "/tmp/project"
        counter = 1
        project_dir = base_dir

        while os.path.exists(project_dir):
            project_dir = f"{base_dir}_{counter}"
            counter += 1
        
        pre_refactored_dir = f"{project_dir}/pre_refactor"
        static_refactored_dir = f"{project_dir}/static_refactored"
        llm_only_refactored_dir = f"{project_dir}/llm_only_refactored"
        hybrid_refactored_dir = f"{project_dir}/hybrid_refactored"

        os.makedirs(pre_refactored_dir)
        os.makedirs(static_refactored_dir)
        os.makedirs(llm_only_refactored_dir)
        os.makedirs(hybrid_refactored_dir)

        zip_path = f"{pre_refactored_dir}/upload.zip"
        with open(zip_path, "wb") as f:
            f.write(uploaded_zip.getbuffer())
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(pre_refactored_dir)
        
        zip_path_static_refactored = f"{static_refactored_dir}/upload.zip"
        with open(zip_path_static_refactored, "wb") as f:
            f.write(uploaded_zip.getbuffer())
        with zipfile.ZipFile(zip_path_static_refactored, 'r') as z:
            z.extractall(static_refactored_dir)
        
        zip_path_llm_only_refactored = f"{llm_only_refactored_dir}/upload.zip"
        with open(zip_path_llm_only_refactored, "wb") as f:
            f.write(uploaded_zip.getbuffer())
        with zipfile.ZipFile(zip_path_llm_only_refactored, 'r') as z:
            z.extractall(llm_only_refactored_dir)
        
        zip_path_hybrid_refactored = f"{hybrid_refactored_dir}/upload.zip"
        with open(zip_path_hybrid_refactored, "wb") as f:
            f.write(uploaded_zip.getbuffer())
        with zipfile.ZipFile(zip_path_hybrid_refactored, 'r') as z:
            z.extractall(hybrid_refactored_dir)

        return get_haskell_files(pre_refactored_dir)
        # return get_haskell_files(project_dir, static_refactored_dir, llm_only_refactored_dir, hybrid_refactored_dir)
    elif repo_url:
        # project_dir = "/tmp/repo"
        base_dir = "/tmp/repo"
        counter = 1
        project_dir = base_dir

        while os.path.exists(project_dir):
            project_dir = f"{base_dir}_{counter}"
            counter += 1
        clone_cmd = ["git", "clone", "--depth", "1", repo_url, project_dir]
        if branch:
            clone_cmd[2:2] = ["-b", branch]
        result = subprocess.run(clone_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return [], None
        return get_haskell_files(project_dir)
    return [], None

def get_haskell_files(project_dir):
    hs_files = glob.glob(f"{project_dir}/**/*.hs", recursive=True)
    lhs_files = glob.glob(f"{project_dir}/**/*.lhs", recursive=True)
    source_files = hs_files + lhs_files

    return source_files, project_dir


# def get_haskell_files(project_dir, static_refactored_dir, llm_only_refactored_dir, hybrid_refactored_dir):
#     hs_files = glob.glob(f"{project_dir}/**/*.hs", recursive=True)
#     lhs_files = glob.glob(f"{project_dir}/**/*.lhs", recursive=True)
#     source_files = hs_files + lhs_files

#     static_hs_files = glob.glob(f"{static_refactored_dir}/**/*.hs", recursive=True)
#     static_lhs_files = glob.glob(f"{static_refactored_dir}/**/*.lhs", recursive=True)
#     static_source_files = static_hs_files + static_lhs_files

#     llm_only_hs_files = glob.glob(f"{llm_only_refactored_dir}/**/*.hs", recursive=True)
#     llm_only_lhs_files = glob.glob(f"{llm_only_refactored_dir}/**/*.lhs", recursive=True)
#     llm_only_source_files = llm_only_hs_files + llm_only_lhs_files

#     hybrid_hs_files = glob.glob(f"{hybrid_refactored_dir}/**/*.hs", recursive=True)
#     hybrid_lhs_files = glob.glob(f"{hybrid_refactored_dir}/**/*.lhs", recursive=True)
#     hybrid_source_files = hybrid_hs_files + hybrid_lhs_files

#     return source_files, project_dir, static_source_files, llm_only_source_files, hybrid_source_files
