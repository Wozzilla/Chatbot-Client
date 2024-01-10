"""本文件为整个项目的主文件，并使用gradio搭建界面"""
import gradio as gr
from modules.NLG.ChatGLM import ChatGLM
from modules.ASR.Whisper import Whisper
from modules.utils import Configs

chatbotEntity = ChatGLM(Configs["ChatGLM"])
asrEntity = Whisper(Configs["OpenAI"])
with gr.Blocks(title="NLG Project", theme=gr.themes.Soft()) as demo:
    botComponent = gr.Chatbot()
    inputTextbox = gr.Textbox()
    audioComponent = gr.Audio(sources=["microphone"], type="filepath")
    asrButton = gr.Button(value="🎤识别")
    clearButton = gr.ClearButton([inputTextbox, botComponent], value="🧹清除")


    def chat(message, chat_history):
        """与聊天机器人进行聊天"""
        bot_message = chatbotEntity.continuedQuery(message, chat_history)
        chat_history.append((message, bot_message))
        return "", chat_history


    asrButton.click(asrEntity.asr, [audioComponent], [inputTextbox])
    inputTextbox.submit(chat, [inputTextbox, botComponent], [inputTextbox, botComponent])

if __name__ == "__main__":
    demo.launch()
