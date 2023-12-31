import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
import google.generativeai as genai
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import time


# Load API credentials
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)


# Setup memory
memory = ConversationBufferMemory(memory_key='chat_history', input_key='human_input')


# Setup page configuration
title_bar_logo = Image.open("./assets/Asset 8@3x.png")
st.set_page_config(page_title="SmartClarify", page_icon=title_bar_logo, layout="centered", initial_sidebar_state="expanded")


# Setup session state
if 'submitted' not in st.session_state:
    st.session_state['submitted'] = False

if 'model' not in st.session_state:
    st.session_state['model'] = 'gemini-pro'

if 'messages' not in st.session_state:
    st.session_state['messages'] = []

if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
else:
    for message in st.session_state['chat_history']:
        memory.save_context({'human_input': message['human_input']}, {'output': message['AI']})



# Setup LLM
llm = genai.GenerativeModel('gemini-pro')
llm_chat = ChatGoogleGenerativeAI(model=st.session_state['model'], google_api_key=GOOGLE_API_KEY)
llm_vision = genai.GenerativeModel('gemini-pro-vision')



# Setup Sidebar UI
with st.sidebar:
    st.title("Welcome to")
    st.image(Image.open("./assets/Asset 9@3x.png"))
    st.subheader("Read before using:")
    st.markdown("""
             * Select your subject of choice
             * Ask your doubt in the text box provided
             * Upload an image of your doubt if required
             * And get your explanation instantly!
             * Continue the conversation if your doubt is not resolved...""")
    subject = st.selectbox("Select your Subject", ("Physics", "Chemistry", "Maths", "Biology", "Computer Science", "English"))
    st.empty()
    st.markdown('***Please note:***\
                *Being an AI-based application, \
                responses are subject to inaccuracies and inconsistencies. \
                Kindly review the responses carefully before using them in your work. \
                Use this application solely for understanding complicated concepts \
                rather than for seeking solutions to questions.*')
    clear = st.button('Clear Conversation')
    components.html("""
<script type="text/javascript" src="https://cdnjs.buymeacoffee.com/1.0.0/button.prod.min.js" data-name="bmc-button" data-slug="rhythmd18" data-color="#c1272d" data-emoji="☕"  data-font="Bree" data-text="Buy me a coffee" data-outline-color="#ffffff" data-font-color="#ffffff" data-coffee-color="#FFDD00" ></script>
""")

    if clear:
        st.session_state['messages'] = []
        st.session_state['chat_history'] = []
        st.session_state['submitted'] = False


# Set title and logo
logo = Image.open("./assets/Asset 9@3x.png")
st.image(logo, use_column_width='auto')
st.subheader('Your Personal AI Tutor!')
st.write('Powered by **Google Gemini**')



# Setup prompt
prompt_template = PromptTemplate(
    input_variables=["doubt", "subject"],
    template="""You are an expert tutor whose name is SmartClarify./
    You explain the concepts in simple terms that are very easy to understand (even to a 10-year-old kid)./
    If the the question is left blank and there is no image either, ask the user to write the question./
    Spread out your response in points so that it is easy to grasp./
    Use LaTeX for mathematical equations (use $...$ for inline math expressions)./
    Provide additional links for further reading./
    If the question or the image is not related to the subject strictly,/
    please refrain from describing anything and reject politely/
    and ask to rephrase the question or re-upload the image accordingly./

    Conversation history: 
    {chat_history}/

    The question is: {doubt}/
    The subject is: {subject}/
    
    Human: {human_input}/
    AI: 
    """
)



# Primary Doubt of the student
doubt = st.text_input("Ask your doubt...")
message = prompt_template.format(chat_history=[], doubt=doubt, subject=subject, human_input='')



# Setup Image upload/capture
input_type = st.radio("Select Mode of Inputting Image...", ("Upload an image", "Take a picture"))
if input_type == "Upload an image":
    img = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
    if img:
        st.image(img, caption="Uploaded Image")
else:
    img = st.camera_input("Take a picture")
img = Image.open(img) if img else None
btn_placeholder = st.empty()



# Generate response for the first question
def get_response(doubt, img):
    if img:
        response = llm_vision.generate_content([doubt, img])
    else:
        response = llm.generate_content(doubt)
    return response



# Render the messages from the session state
for message in st.session_state['messages']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])



# Response before submitting the first question
if st.session_state['submitted'] == False:
    submit = btn_placeholder.button('Submit')

    if submit:

        st.session_state['submitted'] = True
        btn_placeholder.empty()

        with st.chat_message('user'):
            st.markdown(doubt)
        st.session_state['messages'].append({'role': 'user', 'content': doubt})

        with st.spinner('Thinking...'):
            response = get_response(message, img)
        response = response.candidates[0].content.parts[0].text
        message = {'human_input': doubt, 'AI': response}
        st.session_state['chat_history'].append(message)

        with st.chat_message('assistant'):
            message_placeholder = st.empty()  # Create an empty placeholder
            full_response = '' # Initialize the full_response
            for chunk in response.splitlines():
                for word in chunk.split(): # Split the response into chunks
                    full_response += word + ' '# Append the chunk to the full_response
                    time.sleep(0.05)
                    message_placeholder.markdown(full_response + '▌ ')  # Update the message_placeholder
                full_response += '  \n'
            message_placeholder.markdown(response)
        st.session_state['messages'].append({'role': 'assistant', 'content': response})



# Setup chaining functionalities
llmchain = LLMChain(
    memory=memory,
    prompt=prompt_template,
    llm=llm_chat,
    verbose=True
)



# Start the chat after submission of the first question
if st.session_state['submitted']:        

    follow_up = st.chat_input('Ask a follow-up question...')
    if follow_up:
        with st.chat_message('user'):
            st.markdown(follow_up)
        st.session_state['messages'].append({'role': 'user', 'content': follow_up})

        with st.spinner('Thinking...'):
            response = llmchain.run({'doubt': doubt, 'subject':subject, 'human_input': follow_up})
        message = {'human_input': follow_up, 'AI': response}
        st.session_state['chat_history'].append(message)

        with st.chat_message('assistant'):
            message_placeholder = st.empty()  # Create an empty placeholder
            full_response = '' # Initialize the full_response
            for chunk in response.splitlines():
                for word in chunk.split(): # Split the response into chunks
                    full_response += word + ' '# Append the chunk to the full_response
                    time.sleep(0.05)
                    message_placeholder.markdown(full_response + '▌ ')  # Update the message_placeholder
                full_response += '  \n'
            message_placeholder.markdown(response)
        st.session_state['messages'].append({'role': 'assistant', 'content': response})
