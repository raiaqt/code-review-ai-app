from flask import Flask, render_template, request, jsonify
import os
from review_gitlab import review_merge_request
from review_github import review_pull_request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/trigger-gitlab-review', methods=['POST'])
def trigger_gitlab_review():
    ci_project_id = request.form.get('CI_PROJECT_ID')
    ci_merge_request_iid = request.form.get('CI_MERGE_REQUEST_IID')
    access_token = os.getenv("GITLAB_ACCESS_TOKEN")  # Replace with your method for storing the token
    
    if not ci_project_id or not ci_merge_request_iid:
        return jsonify({"error": "Missing project ID or merge request IID"}), 400

    try:
        # Trigger the review process
        review_merge_request(ci_project_id, ci_merge_request_iid)
        return jsonify({"success": f"Review triggered for {ci_project_id}, PR #{ci_merge_request_iid}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/trigger-github-review', methods=['POST'])
def trigger_github_review():
    repo_name = request.form.get('REPO_NAME')
    pull_number = request.form.get('PULL_NUMBER')
    
    if not repo_name or not pull_number:
        return jsonify({"error": "Missing repository name or pull request number"}), 400
    
    try:
        # Trigger the review process
        review_pull_request(repo_name, int(pull_number))
        return jsonify({"success": f"Review triggered for {repo_name}, PR #{pull_number}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5173, debug=True)
