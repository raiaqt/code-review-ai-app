import os
import openai
import json

def generate_documentation_with_chatgpt(formatted_changes):
    """
    Uses ChatGPT to generate high-quality documentation for code changes.
    """

    # Get the OpenAI API key from environment variables
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # Updated prompt for generating documentation
    prompt = f"""
    You are a senior software engineer and technical writer. Your task is to generate **clear, concise, and professional documentation** based on the following code changes. The documentation should provide developers with an understanding of what the changes do, why they were made, and how they impact the project.

    ### **Documentation Guidelines**:
    1. **Clarity**:
       - Use simple and clear language to explain the purpose and functionality of the changes.
       - Ensure the documentation can be understood by developers who are unfamiliar with the code.

    2. **Structure**:
       - Provide an overview of the change (what and why).
       - Include technical details, such as changes to methods, classes, or APIs.
       - Highlight any breaking changes or important notes.

    3. **Use Markdown Formatting**:
       - Use headers, bullet points, and code blocks to structure the documentation.
       - Include code snippets where appropriate, formatted in **markdown**.

    4. **Relevance**:
       - Focus only on significant changes that impact how the code is used or maintained.
       - Avoid unnecessary verbosity.

    ---


    Changes:
    {formatted_changes}
    """

    print("HERE")
    # Call the OpenAI API
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # Switch to "gpt-4" for higher quality
        messages=[
            {"role": "system", "content": "You are a professional software engineer and technical writer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    content = response["choices"][0]["message"]["content"]
    print(content)

    # Parse the JSON content safely
    try:
        documentation = content
        return content
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        return []
