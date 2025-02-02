import subprocess

def run_git_command(command):
    """Run a git command using subprocess."""
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{' '.join(command)}': {e.stderr}")
        return False

def git_update():
    """Update the local git repository and push to remote."""
    
    # Stage all changes
    print("Staging changes...")
    if not run_git_command(['git', 'add', '.']):
        return

    # Commit changes
    commit_message = input("Enter commit message: ")
    print("Committing changes...")
    if not run_git_command(['git', 'commit', '-m', commit_message]):
        return

    # Pull latest changes from remote
    print("Pulling latest changes from remote...")
    if not run_git_command(['git', 'pull', 'origin', 'main', '--rebase']):
        return

    # Push changes to remote
    print("Pushing changes to remote...")
    if not run_git_command(['git', 'push', 'origin', 'main']):
        return

    print("Git update completed successfully.")

if __name__ == "__main__":
    git_update()
