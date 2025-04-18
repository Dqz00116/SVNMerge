import json
import subprocess
import sys
import os

def load_config(config_file):
    """Load JSON configuration file"""
    if not os.path.exists(config_file):
        print(f"Configuration file {config_file} not found.")
        sys.exit(1)
    
    with open(config_file, "r", encoding="utf-8") as file:
        try:
            config = json.load(file)
            return config
        except json.JSONDecodeError as e:
            print(f"Error parsing configuration file: {e}")
            sys.exit(1)

def run_command(command, cwd=None):
    """Run SVN command and capture output"""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_message = (
            f"Command failed: {' '.join(command)}\n"
            f"Return code: {e.returncode}\n"
            f"Output: {e.stdout.strip()}\n"
            f"Error: {e.stderr.strip()}"
        )
        raise RuntimeError(error_message)

def svn_switch(branch_path, working_dir):
    """Switch to the specified branch"""
    print(f"Switching to branch: {branch_path}")
    run_command(["svn", "switch", branch_path], cwd=working_dir)

def svn_update(working_dir):
    """Update working copy to the latest revision"""
    print("Updating working directory to the latest revision...")
    run_command(["svn", "update", "--set-depth", "infinity"], cwd=working_dir)

def svn_revert(working_dir):
    """Revert all uncommitted changes"""
    print("Reverting all changes in the working directory...")
    run_command(["svn", "revert", "-R", "."], cwd=working_dir)

def svn_merge(revision, source_branch, working_dir):
    """Merge specified revision"""
    print(f"Merging revision {revision} from {source_branch}...")
    run_command(
        ["svn", "merge", "-c", revision, source_branch, "--accept", "theirs-full"],
        cwd=working_dir,
    )

def main():
    # Configuration file is located in the same directory as the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(script_dir, "config.json")

    # Load configuration file
    config = load_config(config_file)

    # Extract parameters from the configuration file
    source_branch = config.get("source_branch")
    target_branch = config.get("target_branch")
    working_dir = config.get("working_dir")
    revisions = config.get("revisions", [])

    if not (source_branch and target_branch and working_dir and revisions):
        print("Invalid configuration. Please ensure all required fields are provided.")
        sys.exit(1)

    # Switch to the target branch
    try:
        svn_switch(target_branch, working_dir)
        svn_update(working_dir)

        # Loop through and merge revisions
        for revision in revisions:
            try:
                svn_merge(str(revision), source_branch, working_dir)
                print(f"Successfully merged revision {revision} to local working directory.")
            except Exception as e:
                print(f"Failed to merge revision {revision}:\n{e}")
                print("Reverting all changes...")
                svn_revert(working_dir)
                sys.exit(1)

        print("All revisions processed! Please review the changes in your working directory before committing.")

    except Exception as e:
        print(f"An error occurred:\n{e}")
        print("Reverting all changes...")
        svn_revert(working_dir)
        sys.exit(1)

if __name__ == "__main__":
    main()
