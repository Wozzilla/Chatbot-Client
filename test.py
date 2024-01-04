import gradio as gr
from modules.Chatbot.ChatGPT import ChatGPT
from modules.utils import Settings

chatbot = ChatGPT(Settings["ChatGPT"])

gr.ChatInterface(
    fn=chatbot.singleQuery,
    title="云·原神",
    description="云·原神 description",
    css="./assets/css/GenshinChat.css",
    # js="./assets/js/GenshinChat.js",
    submit_btn="发送"
).launch()
