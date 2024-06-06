import streamlit as st
import asyncio
import time
import json
import os
from dotenv import load_dotenv
import aiohttp
import requests

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

# Load the JSON data
json_string = """
{ "title": "Local SEO Guide for Your Honey Business: Boosting Visibility and Sales", "content": "# Local SEO Guide for Your Honey Business: Boosting Visibility and Sales\n\n## Introduction\n\nIn today's digital age, having a strong online presence is essential for any business, including those selling honey. Local SEO (Search Engine Optimization) can help your honey business appear in local search results, attract more customers, and ultimately increase sales. This guide will walk you through the steps to optimize your honey business for local SEO.\n\n## Understanding Local SEO\n\nLocal SEO is the practice of optimizing your online presence to attract more business from relevant local searches. These searches take place on Google and other search engines. For a honey business, this means appearing in search results when potential customers in your area search for honey or related products.\n\n## Keyword Research\n\n### Primary Keywords\n\nIdentify high-volume, relevant primary keywords that potential customers might use. Examples include:\n\n- Honey near me\n- Local honey\n- Buy honey online\n\n### Long-Tail Keywords\n\nLong-tail keywords are more specific and less competitive. Examples include:\n\n- Organic honey in [Your City]\n- Raw honey suppliers in [Your City]\n- Best local honey for sale\n\n### LSI Keywords\n\nLatent Semantic Indexing (LSI) keywords add context and depth to your content. Examples include:\n\n- Beekeeping\n- Natural sweeteners\n- Honey benefits\n\n## Optimizing Your Website\n\n### On-Page SEO\n\n- **Title Tags and Meta Descriptions**: Include primary keywords in your title tags and meta descriptions.\n- **Header Tags**: Use header tags (H1, H2, H3) to structure your content and include keywords.\n- **Content**: Write informative and engaging content that naturally incorporates your keywords.\n- **Images**: Optimize images with descriptive file names and alt text.\n\n### Mobile Optimization\n\nEnsure your website is mobile-friendly, as many local searches are conducted on mobile devices.\n\n## Google My Business\n\n### Setting Up Your Profile\n\n- **Claim Your Business**: If you haven't already, claim your Google My Business (GMB) listing.\n- **Complete Your Profile**: Fill out all the information, including business name, address, phone number, website, and hours of operation.\n- **Add Photos**: Upload high-quality photos of your products, store, and team.\n\n### Managing Reviews\n\n- **Encourage Reviews**: Ask satisfied customers to leave positive reviews on your GMB listing.\n- **Respond to Reviews**: Engage with customers by responding to their reviews, both positive and negative.\n\n## Local Citations and Backlinks\n\n### Local Citations\n\nEnsure your business information is consistent across all online directories, such as Yelp, Yellow Pages, and local business directories.\n\n### Backlinks\n\nAcquire backlinks from reputable local websites, such as local news sites, blogs, and business associations.\n\n## Social Media and Content Marketing\n\n### Social Media\n\n- **Engage with Your Audience**: Use social media platforms to interact with your customers and share updates about your honey business.\n- **Local Hashtags**: Use local hashtags to increase your visibility in local searches.\n\n### Content Marketing\n\n- **Blog Posts**: Write blog posts about topics related to honey, such as recipes, health benefits, and beekeeping tips.\n- **Local Events**: Promote local events you participate in or sponsor.\n\n## Conclusion\n\nBy following this local SEO guide, your honey business can improve its online visibility, attract more local customers, and increase sales. Remember to continuously monitor your SEO efforts and make adjustments as needed to stay ahead of the competition.\n\n## Call to Action\n\nIf you found this guide helpful, please share it with other local businesses. Feel free to leave a comment below with your thoughts or any additional tips you might have for optimizing local SEO.\n", "tags": ["Local SEO", "Honey Business", "SEO Guide", "Digital Marketing", "Small Business"] }
"""

data = json.loads(json_string)

# Display the JSON data
st.header(data['title'])
st.markdown(data['content'])

tags = ', '.join(data['tags'])
st.write(f"Tags: {tags}")

# functions
async def run_function_agent(agent_id, prompt, messages=None):
    url = 'https://api.codegpt.co/api/v1/chat/completions'
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + api_key}
    
    if messages is None:
        data = {"agentId": agent_id, "stream": True, "format": "json", "messages": [{"role": "user", "content": prompt}]}
    else:
        data = {"agentId": agent_id, "stream": True, "format": "json", "messages": messages + [{"role": "user", "content": prompt}]}

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

    print(f"Received article_content_str: {article_content_str}")

    try:
        article_content = json.loads(article_content_str)
        print(f"Parsed article_content: {article_content}")
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
    else:
        st.write(f"Error publishing the article. Status Code: {medium_response.status_code}")
        st.write(f"Response Text: {medium_response.text}")

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
        article_content = input_loop.run_until_complete(run_function_agent(CODEGPT_MEDIUM_AGENT_ID, "Write a single JSON object with the following keys: 'title', 'content', and 'tags'. The 'content' should be in Markdown format and divided into sections with appropriate headings. The topic of the article should be based on our previous conversation.", st.session_state.messages))
        st.write(article_content)  # Print the article content for debugging
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

