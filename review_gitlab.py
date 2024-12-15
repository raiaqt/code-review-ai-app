# Dynamic Comment Generation and Submission

import os
import requests
import json

def fetch_merge_request_changes(api_url, access_token):
    headers = {
        "PRIVATE-TOKEN": access_token
    }
    response = requests.get(api_url, headers=headers)
    print(api_url)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Error fetching merge request: {response.status_code}, {response.text}")
        return None

def generate_comments_with_chatgpt(merge_request_details):
    import openai

    changes = merge_request_details.get("changes", [])
    # Get the OpenAI API key from environment variables
    openai.api_key = os.getenv("OPENAI_API_KEY")
    
    # Transform changes into a format suitable for the prompt
    formatted_changes = []
    for change in changes:
        formatted_changes.append({
            "file": change.get("new_path", change.get("old_path", "unknown_file")),
            "diff": change.get("diff", "No diff available")
        })
        
    # file_paths = ["src/sample.py"]
    
    # for change in changes:
    #     if change.get("new_path"):
    #         file_paths.append(change.get("new_path"))

    # file_contents = []
    # for path in file_paths:
    #     try:
    #         with open(path, "r") as file:
    #             file_contents.append({
    #                 "file_name": path,
    #                 "content": file.read()
    #             })
    #     except Exception as e:
    #         print(f"Error reading file {path}: {e}")

    prompt = f"""
    You are a tech lead. Based on the following changes, generate code review comments.
    Do not add title to the comments.
    Include suggested change for code, in the form of markdown, inside the comment.
    Include links for reference inside the comment.
    Add [via ChatGPT review bot] on top of comment.
    Use markdown format for the comment body.
    Include the JSON only in the response.
    Format: [{{"file": "filename", "line": line_number, "comment": "comment"}}]
    
    Changes:
    {formatted_changes}
    """


    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a professional code reviewer."},
            {"role": "user", "content": prompt}
        ]
    )

    content = response["choices"][0]["message"]["content"]
    
    # Remove Markdown formatting (triple backticks)
    cleaned_content = content.strip()[7:-3].strip()

    print("Cleaned API Response Content:", cleaned_content)  # Debugging log
    # Parse the JSON content safely
    try:
        comments = json.loads(cleaned_content)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        comments = []

    return comments

def submit_to_gitlab(comments, api_url, access_token, merge_request_details):
    headers = {
        "Private-Token": access_token,
        "Content-Type": "application/json"
    }
    
    base_sha = merge_request_details.get("diff_refs", {}).get("base_sha")
    start_sha = merge_request_details.get("diff_refs", {}).get("start_sha")
    head_sha = merge_request_details.get("diff_refs", {}).get("head_sha")
    
    for comment in comments:
        payload = {
            "body": comment["comment"],
            "position": {
                "base_sha": base_sha,
                "start_sha": start_sha,
                "head_sha": head_sha,
                "position_type": "text",
                "new_path": comment["file"],
                "new_line": comment["line"],
            }
        }
        
        try:
            response = requests.post(api_url, headers=headers, json=payload)
            print(f"Submitted comment on {comment['file']} line {comment['line']}")
        except json.JSONDecodeError as e:
            print(f"{response.status_code}")


def review_merge_request(ci_project_id, ci_merge_request_iid):
    merge_request_api_url = f"https://gitlab.com/api/v4/projects/{ci_project_id}/merge_requests/{ci_merge_request_iid}/changes"
    gitlab_access_token = os.getenv("GITLAB_ACCESS_TOKEN")
    gitlab_comment_api_url = f"https://gitlab.com/api/v4/projects/{ci_project_id}/merge_requests/{ci_merge_request_iid}/discussions"

    # Fetch changes from GitLab
    merge_request_details = fetch_merge_request_changes(merge_request_api_url, gitlab_access_token)
        
    if merge_request_details:
        # Generate comments using ChatGPT
        comments = generate_comments_with_chatgpt(merge_request_details)
        
        # Submit comments to GitLab
        submit_to_gitlab(comments, gitlab_comment_api_url, gitlab_access_token, merge_request_details)
    
