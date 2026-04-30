#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path


def run(cmd, check=True, capture_output=False, text=True):
    return subprocess.run(cmd, shell=True, check=check, capture_output=capture_output, text=text)


def is_aws_configured():
    try:
        result_id = run("aws configure get aws_access_key_id", capture_output=True)
        result_secret = run("aws configure get aws_secret_access_key", capture_output=True)
        return bool(result_id.stdout.strip()) and bool(result_secret.stdout.strip())
    except subprocess.CalledProcessError:
        return False


def get_existing_region():
    try:
        result = run("aws configure get region", capture_output=True)
        return result.stdout.strip() or None
    except subprocess.CalledProcessError:
        return None


def configure_aws_cli():
    access_key = input("Enter AWS Access Key ID: ").strip()
    if not access_key:
        print("AWS Access Key ID is required. Exiting.")
        sys.exit(1)

    secret_key = input("Enter AWS Secret Access Key: ").strip()
    if not secret_key:
        print("AWS Secret Access Key is required. Exiting.")
        sys.exit(1)

    current_region = get_existing_region() or ""
    region = input(f"Enter AWS region [{current_region or 'us-east-1'}]: ").strip() or current_region or "us-east-1"
    output_format = input("Enter AWS CLI output format [json]: ").strip() or "json"

    print("Configuring AWS CLI...")
    run(f"aws configure set aws_access_key_id {access_key}")
    run(f"aws configure set aws_secret_access_key {secret_key}")
    run(f"aws configure set region {region}")
    run(f"aws configure set output {output_format}")
    print("AWS CLI configuration complete.\n")


def ensure_aws_configured():
    if is_aws_configured():
        answer = input("AWS CLI is already configured. Skip reconfiguration? [Y/n]: ").strip().lower()
        if answer in ["", "y", "yes"]:
            print("Skipping AWS CLI configuration.\n")
            return
        print("Reconfiguring AWS CLI...")
    else:
        print("AWS CLI is not configured. Starting configuration...\n")

    configure_aws_cli()


def ensure_ssh_dir():
    ssh_dir = Path.home() / ".ssh"
    ssh_dir.mkdir(mode=0o700, exist_ok=True)
    return ssh_dir


def ensure_ssh_key(ssh_dir: Path):
    private_key = ssh_dir / "id_rsa"
    public_key = ssh_dir / "id_rsa.pub"

    if public_key.exists():
        print(f"SSH public key already exists at: {public_key}")
        return public_key

    if private_key.exists():
        print("Private key exists but public key is missing. Generating public key...")
        run(f"ssh-keygen -y -f {private_key} > {public_key}")
    else:
        print("SSH key pair not found. Generating id_rsa and id_rsa.pub...")
        run(
            f"ssh-keygen -t rsa -b 4096 -N '' -f {private_key} -q",
        )

    public_key.chmod(0o644)
    return public_key


def print_public_key(public_key: Path):
    print("\n=== AWS CodeCommit SSH Public Key ===")
    print(public_key.read_text().strip())
    print("=== End public key ===\n")
    print(
        "If you have not already uploaded this key to AWS CodeCommit,"
        " open the IAM user SSH keys settings, add the public key, and copy the returned SSH username."
    )


def ensure_ssh_config(ssh_dir: Path, ssh_user: str):
    answer = input("Do you want to add a CodeCommit host entry to your SSH config? [Y/n]: ").strip().lower()
    if answer in ["", "y", "yes"]:
        print("Adding CodeCommit host entry to SSH config...")
        ssh_config = ssh_dir / "config"
        host_block = (
            "Host git-codecommit.*.amazonaws.com\n"
            f"  User {ssh_user}\n"
            "  IdentityFile ~/.ssh/id_rsa\n"
        )

        if ssh_config.exists():
            text = ssh_config.read_text()
            if f"User {ssh_user}" in text:
                print("SSH config already contains a CodeCommit host entry.\n")
                return ssh_config

        print(f"Writing CodeCommit ssh config to: {ssh_config}")
        ssh_config.write_text(host_block)
        ssh_config.chmod(0o600)
        return ssh_config
    else:
        print("Skipping SSH config update. You will need to manually configure SSH to use the key for CodeCommit.")
        return


def get_aws_region():
    region = os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AWS_REGION")
    if region:
        return region

    try:
        result = run("aws configure get region", capture_output=True)
        return result.stdout.strip() or None
    except subprocess.CalledProcessError:
        return None


def create_codecommit_repo(repo_name: str, region: str):
    answer = input(f"Do you want to create CodeCommit repository '{repo_name}' in region {region}? [Y/n]: ").strip().lower()
    if answer not in ["", "y", "yes"]:
        print("Skipping repository creation. Exiting.")
        return
    print(f"Creating CodeCommit repository '{repo_name}' in region {region}...")
    try:
        run(f"aws codecommit create-repository --repository-name {repo_name} --region {region}")
    except subprocess.CalledProcessError:
        print("Repository may already exist or creation failed. Checking existing repository...")
        run(f"aws codecommit get-repository --repository-name {repo_name} --region {region}")

    ssh_url = f"ssh://git-codecommit.{region}.amazonaws.com/v1/repos/{repo_name}"
    print(f"Repository SSH URL: {ssh_url}")
    return ssh_url


def ensure_git_remote(ssh_url: str):
    try:
        run("git rev-parse --is-inside-work-tree", capture_output=True)
    except subprocess.CalledProcessError:
        print("Current directory is not a git repository. Initializing one...")
        run("git init")

    try:
        run("git remote add origin " + ssh_url)
        print("Added git remote 'origin'.")
    except subprocess.CalledProcessError:
        print("Remote 'origin' already exists, updating URL...")
        run("git remote set-url origin " + ssh_url)


def main():
    ensure_aws_configured()
    ssh_dir = ensure_ssh_dir()
    public_key = ensure_ssh_key(ssh_dir)
    print_public_key(public_key)

    print("\nPlease add this public key in the AWS CodeCommit IAM user SSH keys section.")
    ssh_user = input("Enter the CodeCommit SSH user returned by AWS (for example APKAZJZGHHCCUMRO7KEJ): ").strip()
    if not ssh_user:
        print("SSH user is required. Exiting.")
        sys.exit(1)

    ensure_ssh_config(ssh_dir, ssh_user)

    repo_name = input("Enter the CodeCommit repository name to create: ").strip()
    if not repo_name:
        print("Repository name is required. Exiting.")
        sys.exit(1)

    region = get_aws_region()
    if not region:
        region = input("AWS region not found. Enter region (for example us-east-1): ").strip()
        if not region:
            print("AWS region is required. Exiting.")
            sys.exit(1)

    ssh_url = create_codecommit_repo(repo_name, region)
    if ssh_url:
        ensure_git_remote(ssh_url)
    print("\nConfiguration complete. You can now push your repo to CodeCommit:")
    print("  git push -u origin main")


if __name__ == "__main__":
    main()
