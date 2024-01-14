"""本文件为整个项目的主文件，并使用gradio搭建界面"""
import subprocess
from os import PathLike
import gradio as gr
from modules.NLG.NLG import ChatGPT
from modules.ASR.ASR import WhisperAPI
from modules.TTS.TTS import OpenAITTS
from modules.utils import Configs, ASREnum, NLGEnum, TTSEnum

chatbotService = ChatGPT(Configs["OpenAI"])
asrService = WhisperAPI(Configs["OpenAI"])
ttsService = OpenAITTS(Configs["OpenAI"])

with gr.Blocks(title="NLG Project", theme=gr.themes.Soft(), css="./assets/css/Chatbot.css",
               js="./assets/js/Chatbot.js") as demo:
    with gr.Row(elem_id="baseContainer"):
        with gr.Column(min_width=280, elem_id="sideBar"):
            asrSwitch = gr.Dropdown([i.name for i in ASREnum], value=asrService.type.name, interactive=True,
                                    label="选择ASR模型", elem_id="asrSwitch")
            nlgSwitch = gr.Dropdown([i.name for i in NLGEnum], value=chatbotService.type.name, interactive=True,
                                    label="选择NLG模型", elem_id="nlgSwitch")
            ttsSwitch = gr.Dropdown([i.name for i in TTSEnum], value=ttsService.type.name, interactive=True,
                                    label="选择TTS模型", elem_id="ttsSwitch")
            clearButton = gr.Button(value="🧹清除")
        with gr.Column(scale=5, elem_id="chatPanel"):
            botComponent = gr.Chatbot(label=chatbotService.type.name, elem_id="chatbot")
            with gr.Row(elem_id="inputPanel"):
                textInput = gr.Textbox(placeholder="点击输入", show_label=False, scale=2, elem_id="textInput")
                audioInput = gr.Audio(sources=["microphone"], type="filepath", show_label=False, elem_id="audioInput")
            with gr.Row(elem_id="buttonPanel"):
                submitButton = gr.Button(value="✉️发送")
                voiceChatButton = gr.Button(value="🎤发送")


        def cleanAllContent(message, chatHistory, audioData):
            """
            清除全部消息
            """
            return "", [], None


        def textChat(message, chatHistory):
            """
            与聊天机器人进行文本聊天
            :param message: str 用户输入的消息
            :param chatHistory: [[str, str]...] 分别为用户输入和机器人回复(先前的)
            """
            botMessage = chatbotService.continuedQuery(message, chatHistory)
            chatHistory.append((message, botMessage))
            synthAudioPath = ttsService.synthesize(botMessage)
            subprocess.Popen(["ffplay", "-noborder", "-nodisp", "-autoexit", "-i", synthAudioPath])
            return "", chatHistory


        def voiceChat(audio: PathLike):
            """
            语音识别，并自动将识别结果发送
            :param audio: PathLike 语音文件路径
            """
            chatHistory = botComponent.value
            transcript = asrService.transcribe(audio)  # 语音识别结果
            botMessage = chatbotService.continuedQuery(transcript, chatHistory)
            chatHistory.append((transcript, botMessage))
            synthAudioPath = ttsService.synthesize(botMessage)
            subprocess.Popen(["ffplay", "-noborder", "-nodisp", "-autoexit", "-i", synthAudioPath])
            return "", chatHistory


        clearButton.click(cleanAllContent, [textInput, botComponent, audioInput], [textInput, botComponent, audioInput])
        submitButton.click(textChat, [textInput, botComponent], [textInput, botComponent])
        voiceChatButton.click(voiceChat, [audioInput], [textInput, botComponent])
        textInput.submit(textChat, [textInput, botComponent], [textInput, botComponent])

    if __name__ == "__main__":
        demo.launch()
