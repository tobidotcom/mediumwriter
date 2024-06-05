import streamlit as st
import asyncio
import time
import json
import os
from dotenv import load_dotenv
import aiohttp
import requests

load_dotenv()

# CodeGPT Plus
CODEGPT_API_KEY = os.getenv("CODEGPT_API_KEY")
CODEGPT_AGENT_ID = os.getenv("CODEGPT_AGENT_ID")
CODEGPT_MEDIUM_AGENT_ID = os.getenv("CODEGPT_MEDIUM_AGENT_ID")
MEDIUM_TOKEN = os.getenv("MEDIUM_TOKEN")

# Initialize session state
if "load_spinner" not in st.session_state:
    st.session_state.load_spinner = None

# Custom CSS for chat messages
chat_message_css = """
<style>
.stChat .stMarkdown {
    text-align: left;
    max-width: 60%;
    margin: 0 auto;
}
</style>
"""

# layout
st.set_page_config(layout="centered")
st.title("Agent Writer for Medium 📝🤖")
st.write("Engage with your agent on the topic on which you wish to create an article. Once the discussion is finished, instruct your agent to publish the article on Medium. Ensure you have a valid Medium Developer Token for this task.")
st.write('Powered by <a href="https://plus.codegpt.co/">CodeGPT Plus</a>', unsafe_allow_html=True)
st.divider()

# codegpt sidebar
st.sidebar.title("CodeGPT settings")
api_key = st.sidebar.text_input("CodeGPT Plus API key", value=CODEGPT_API_KEY, type="password")
if api_key:
    codegpt_agent_id = st.sidebar.text_input(f"Agent ID", value=CODEGPT_AGENT_ID)

# medium sidebar
st.sidebar.title("Medium settings")
medium_token = st.sidebar.text_input("Medium Token", value=MEDIUM_TOKEN, type="password")
notify_followers = st.sidebar.checkbox("Notify Followers", value=False)
publish_status = st.sidebar.selectbox(
    'Publish Status',
    ('public', 'draft', 'unlisted')
)

# functions
async def run_function_agent(agent_id, prompt):
    url = 'https://api.codegpt.co/api/v1/chat/completions'
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + api_key}
    data = {"agentId": agent_id, "stream": True, "format": "json", "messages": [{"role": "user", "content": prompt}]}
    full_response = ""
    if st.session_state.load_spinner is None:
        st.session_state.load_spinner = st.spinner(text="Processing...")
    with st.session_state.load_spinner:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                async for chunk in response.content.iter_chunked(1024):
                    if chunk:
                        raw_data = chunk.decode('utf-8').replace("data: ", '')
                        for line in raw_data.strip().splitlines():
                            if line and line != "[DONE]":
                                try:
                                    json_object = json.loads(line)
                                    if "choices" in json_object:
                                        result = json_object["choices"][0]["delta"].get("content", "")
                                        full_response += result
                                except json.JSONDecodeError:
                                    print(f'Error : {line}')
    # Remove any additional text or characters from the response
    full_response = full_response.strip()
    st.session_state.load_spinner = None
    return full_response

async def medium_publish(article_content_str):
    published = False
    article_url = ""
    title = ""

    if not article_content_str:
        st.write("Error: Article content is empty.")
        return {
            "published": published,
            "article_url": article_url,
            "title": title
        }

    try:
        # Parse the JSON string
        article_content = json.loads(article_content_str)

        # Access the JSON keys
        title = article_content['title']
        content = article_content['content']
        tags = article_content['tags']
    except (KeyError, json.JSONDecodeError) as e:
        st.write(f"Error: Unable to parse the article content. {e}")
        return {
            "published": published,
            "article_url": article_url,
            "title": title
        }

    # Get the Medium user ID
    url_me = 'https://api.medium.com/v1/me'
    headers = {
        "Authorization": "Bearer " + medium_token,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Charset": "utf-8"
    }
    medium_me_response = await requests.get(url_me, headers=headers)
    medium_me_response_json = medium_me_response.json()
    medium_user_id = medium_me_response_json['data']['id']

    # Create the article on Medium
    url_post = "https://api.medium.com/v1/users/" + medium_user_id + "/posts"
    data = {
        "title": title,
        "contentFormat": "markdown",
        "content": content,
        "publishStatus": publish_status,
        "notifyFollowers": notify_followers,
        "license": "all-rights-reserved"
    }
    medium_response = await requests.post(url_post, headers=headers, json=data)

    if medium_response.status_code == 201:
        published = True
        article_url = medium_response.json()['data']['url']

    return {
        "published": published,
        "article_url": article_url,
        "title": title
    }

async def handle_prompt(prompt, agent_id):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    status = st.status("Wait a moment...", expanded=True)
    message_placeholder = st.empty()

    response = await run_function_agent(agent_id, prompt)
    message_placeholder.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
    status.empty()

def main():
    # Create a new event loop for handling user input
    input_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(input_loop)

    # Streamlit Chat
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(chat_message_css, unsafe_allow_html=True)
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("Let's write an article"):
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(chat_message_css, unsafe_allow_html=True)
            st.markdown(prompt)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(chat_message_css, unsafe_allow_html=True)
            input_loop.run_until_complete(handle_prompt(prompt, codegpt_agent_id))

    # Generate Article Button
    if st.button("Generate Article"):
        article_content = input_loop.run_until_complete(run_function_agent(CODEGPT_MEDIUM_AGENT_ID, "Write an article with the central topic of this conversation in JSON format with keys 'title', 'content', and 'tags'."))
        st.session_state.article = article_content

    # Publish Button
    if "article" in st.session_state and st.button("Publish"):
        article = input_loop.run_until_complete(medium_publish(st.session_state.article))
        if article["published"]:
            full_response = 'The article "' + article['title'] + '" was successfully published. URL: ' + article['article_url']
            st.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        else:
            st.write("Error publishing the article.")

# Run the main function
main()
