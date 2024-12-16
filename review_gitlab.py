# Dynamic Comment Generation and Submission

import os
import requests
import json
import base64

from generate_comments import generate_comments_with_chatgpt
# from generate_documentation import generate_documentation_with_chatgpt

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

def get_file_content(api_url, file_path, ref, access_token):
    url = f"{api_url}/{file_path}"
    headers = {"PRIVATE-TOKEN": access_token}
    params = {"ref": ref}

    try:
        print(f"Fetching content for: {file_path}")
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            file_info = response.json()
            # Decode Base64 content
            base64_content = file_info.get("content", "").replace("\n", "")
            try:
                content = base64.b64decode(base64_content).decode("utf-8")
            except Exception as e:
                raise ValueError(f"Error decoding Base64 content: {e}")

            print(f"Content fetched for: {file_path}")
            return content
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except json.JSONDecodeError as e:
        print(f"Error fetching file: {e}")
        return []
    

def format_changes(api_url, merge_request_details, access_token):
    try:
        changes = merge_request_details.get("changes", [])
        head_sha = merge_request_details["diff_refs"]["head_sha"]
        print(head_sha)
        
        formatted_changes = []
        for change in changes:
            new_path = change.get("new_path")
            
            file_content = get_file_content(api_url, new_path, head_sha, access_token)

            formatted_changes.append({
                "file": change.get("new_path", change.get("old_path", "unknown_file")),
                "diff": change.get("diff", "No diff available"),
                "file_content": file_content
            })

        print(f"Changes formatted successfully.")
        return formatted_changes
    except json.JSONDecodeError as e:
        print(f"Error formatting changes: {e}")
        return []

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
    
    return comments


def review_merge_request(ci_project_id, ci_merge_request_iid):
    merge_request_api_url = f"https://gitlab.com/api/v4/projects/{ci_project_id}/merge_requests/{ci_merge_request_iid}/changes"
    gitlab_access_token = os.getenv("GITLAB_ACCESS_TOKEN")
    gitlab_comment_api_url = f"https://gitlab.com/api/v4/projects/{ci_project_id}/merge_requests/{ci_merge_request_iid}/discussions"
    file_api_url = f"https://gitlab.com/api/v4/projects/{ci_project_id}/repository/files"

    # Fetch changes from GitLab
    merge_request_details = fetch_merge_request_changes(merge_request_api_url, gitlab_access_token)
    formatted_changes = format_changes(file_api_url, merge_request_details, gitlab_access_token)

    if merge_request_details:
        # Generate comments using ChatGPT
        comments = generate_comments_with_chatgpt(formatted_changes)
        # comments = generate_documentation_with_chatgpt(formatted_changes)
        
        # Submit comments to GitLab
        submit_to_gitlab(comments, gitlab_comment_api_url, gitlab_access_token, merge_request_details)

        return comments
    
    return []
    
