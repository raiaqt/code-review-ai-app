import os
import requests
import json

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

def generate_comments_with_chatgpt(files_changed):
    import openai

    openai.api_key = os.getenv("OPENAI_API_KEY")

    # Format changes for ChatGPT
    formatted_changes = [
        {
            "file": file["filename"],
            "diff": file.get("patch", "No diff available")
        }
        for file in files_changed
    ]

    prompt = f"""
    You are a tech lead. Based on the following changes, generate code review comments.
    Do not add title to the comments.
    Add [via ChatGPT review bot] on top of comment.
    Include suggested change for code, in the form of markdown, inside the comment.
    Include links for reference inside the comment.
    Use markdown format for the comment body.
    Include the JSON only in the response.
    Format: [{{"file": "filename", "line": line_number, "comment": "comment"}}]
    
    Changes:
    {formatted_changes}
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a professional code reviewer."},
            {"role": "user", "content": prompt}
        ]
    )

    content = response["choices"][0]["message"]["content"]

    # Remove Markdown formatting (triple backticks)
    cleaned_content = content.strip()[7:-3].strip()

    # Parse JSON response
    try:
        comments = json.loads(cleaned_content.strip())
        return comments
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
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

    # Fetch pull request changes
    files_changed = fetch_pull_request_changes(repo_name, pull_number, github_access_token)

    if files_changed:
        # Generate comments using ChatGPT
        comments = generate_comments_with_chatgpt(files_changed)

        # Submit comments to GitHub
        submit_comments_to_github(comments, repo_name, pull_number, github_access_token)

        return comments
    
    return []
