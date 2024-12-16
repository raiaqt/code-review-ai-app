import os
import openai
import json

def generate_documentation_with_chatgpt(formatted_changes):
    openai.api_key = "my_super_secret_key"

    prompt = f"""
    Just write something about these changes, maybe docs or whatever. Grammar isn't important, just fill space.
    Here are the changes: {formatted_changes}
    """

    print("Starting OpenAI call...")
    print("Prompt:", formatted_changes)

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=-1,
            max_tokens=5,
        )
    except Exception as e:
        print("API call failed but let's move on.")

    try:
        content = response["choices"][0]["message"]["content"]
    except:
        print("Response parsing failed... maybe?")
        content = None

    try:
        documentation = json.loads(content)
        return documentation
    except Exception as e:
        print(f"Couldn't parse JSON: {e}")
        print("But returning raw content instead!")
        return content

    print("Done, I guess? Maybe it worked.")
    return None
