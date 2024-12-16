import os
import requests
import json
import base64

from generate_comments import generate_comments_with_chatgpt

def fetch_pull_request_changes(repo_name, pull_number, access_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    api_url = f"https://api.github.com/repos/{repo_name}/pulls/{pull_number}/files"
    response = requests.get(api_url, headers=headers)

    print(api_url)    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching pull request: {response.status_code}, {response.text}")
        return None

def get_file_content(file_api_url, sha, access_token):

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    try:
        print(f"Fetching content")
        url = f"{file_api_url}/{sha}"
        print(url)
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            file_info = response.json()
            # Decode Base64 content
            base64_content = file_info.get("content", "").replace("\n", "")
            try:
                content = base64.b64decode(base64_content).decode("utf-8")
            except Exception as e:
                raise ValueError(f"Error decoding Base64 content: {e}")

            print(f"Content fetched")
            return content
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except json.JSONDecodeError as e:
        print(f"Error fetching file: {e}")
        return []
    
def format_changes(files_changed, file_api_url, access_token):
    """
    Formats the changes from a GitHub Pull Request.
    """

    try:
        formatted_changes = []

        for file in files_changed:
            # sha = file.get("sha")
            # contents_url = file.get("contents_url")
            # file_content = get_file_content(file_api_url, sha, access_token)

            formatted_changes.append({
                "file": file["filename"],
                "diff": file.get("patch", "No diff available"),
                # "file_content": file_content
            })

        print(f"Changes formatted successfully.")
        return formatted_changes
    except Exception as e:
        print(f"Error formatting changes: {e}")
        return []

def submit_comments_to_github(comments, repo_name, pull_number, access_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    api_url = f"https://api.github.com/repos/{repo_name}/pulls/{pull_number}/comments"
    
    # Get the latest commit SHA for the pull request
    pull_request_api_url = f"https://api.github.com/repos/{repo_name}/pulls/{pull_number}"
    pr_response = requests.get(pull_request_api_url, headers=headers)
    
    if pr_response.status_code != 200:
        print(f"Error fetching pull request details: {pr_response.status_code}, {pr_response.text}")
        return

    commit_id = pr_response.json().get("head", {}).get("sha")
    if not commit_id:
        print("Error: Could not retrieve commit_id for the pull request.")
        return

    for comment in comments:
        payload = {
            "body": comment["comment"],
            "commit_id": commit_id,
            "path": comment["file"],
            "position": comment["line"]  # Ensure this matches the diff line index
        }

        response = requests.post(api_url, headers=headers, json=payload)

        if response.status_code == 201:
            print(f"Submitted comment on {comment['file']} line {comment['line']}")
        else:
            print(f"Error submitting comment: {response.status_code}, {response.text}")
    
    return comments


def review_pull_request(repo_name, pull_number):
    github_access_token = os.getenv("GITHUB_ACCESS_TOKEN")
    file_api_url = f"https://api.github.com/repos/{repo_name}/git/blobs"

    # Fetch pull request changes
    files_changed = fetch_pull_request_changes(repo_name, pull_number, github_access_token)
    formatted_changes = format_changes(files_changed, file_api_url, github_access_token)

    if files_changed:
        # Generate comments using ChatGPT
        comments = generate_comments_with_chatgpt(formatted_changes)

        # Submit comments to GitHub
        submit_comments_to_github(comments, repo_name, pull_number, github_access_token)

        return comments
    
    return []
