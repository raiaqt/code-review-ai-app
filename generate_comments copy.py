import os
import openai
import json

def generate_comments_with_chatgpt(formatted_changes):

    # Get the OpenAI API key from environment variables
    openai.api_key = os.getenv("OPENAI_API_KEY")

    prompt = f"""
    You are a senior tech lead with expertise in reviewing code for quality, performance, and maintainability.
    Based on the following changes, generate **focused, high-value, and actionable code review comments** for each diff, use the context provided.
    Your review should prioritize impactful changes that improve the overall quality of the code.

    ### **Review Guidelines**:
    1. **Focus on High-Value Comments**:
    - Only comment on changes that significantly impact readability, maintainability, performance, or security.
    - Avoid trivial comments unless they lead to meaningful improvement.

    2. **Specific Code Suggestions**:
    - Suggest specific code changes, formatting them as code blocks using **markdown** (e.g., \`\`\`code\`\`\`).
    - Ensure suggestions are practical and implementable.
    - Include in the comment value.

    3. **Include Relevant References**:
    - Add links to relevant documentation, standards, or best practices for further reading.
    - Examples include [PEP 8](https://pep8.org) for Python or other relevant resources.
    - Include in the comment value.

    ---

    ### **Output Requirements**:
    - Respond **only** with JSON.
    - JSON format: `[{{"file": "filename", "line": line_number, "comment": "comment"}}]`
    - Each comment should:
    - Be specific to the context of the change.
    - Include a suggested code change formatted in markdown.
    - Provide a rationale and a relevant link for further reference.

    ---

    ### **Example Comment Format**:
    ```json
    [
    {{
        "file": "example.py",
        "line": 10,
        "comment": "Consider using a list comprehension for better performance and readability. \n\nSuggested change:\n```python\nnew_list = [process(x) for x in original_list]\n```\n\n\nFor reference, see [PEP 8 guidelines](https://pep8.org)."
    }}
    ]
    ```


    Changes:
    {formatted_changes}
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a professional code reviewer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    content = response["choices"][0]["message"]["content"]
    
    # Remove Markdown formatting (triple backticks)
    cleaned_content = content.strip()[7:-3].strip()

    # Parse the JSON content safely
    try:
        comments = json.loads(cleaned_content)

        return comments
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        return []
