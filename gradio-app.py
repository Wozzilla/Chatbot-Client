"""本文件为整个项目的主文件，并使用gradio搭建界面"""
from os import PathLike
import subprocess
import gradio as gr
from modules.NLG.NLG import ChatGPT
from modules.ASR.ASR import WhisperAPI
from modules.TTS.TTS import OpenAITTS
from modules.utils import Configs

chatbotEntity = ChatGPT(Configs["OpenAI"])
asrEntity = WhisperAPI(Configs["OpenAI"])
ttsEntity = OpenAITTS(Configs["OpenAI"])

with gr.Blocks(title="NLG Project", theme=gr.themes.Soft()) as demo:
    botComponent = gr.Chatbot()

    textInput = gr.Textbox(placeholder="请输入聊天内容", label="📃输入")
    audioInput = gr.Audio(sources=["microphone"], label="录音", type="filepath")

    submitButton = gr.Button(value="✉️发送")
    voiceChatButton = gr.Button(value="🎤发送")
    clearButton = gr.ClearButton([textInput, botComponent], value="🧹清除")


    def textChat(message, chatHistory):
        """与聊天机器人进行文本聊天"""
        botMessage = chatbotEntity.continuedQuery(message, chatHistory)
        chatHistory.append((message, botMessage))
        synthAudioPath = ttsEntity.synthesize(botMessage)

        return "", chatHistory


    def voiceChat(audio: PathLike):
        """语音识别，并自动将识别结果发送"""
        chatHistory = botComponent.value
        transcript = asrEntity.transcribe(audio)  # 语音识别结果
        botMessage = chatbotEntity.continuedQuery(transcript, chatHistory)
        chatHistory.append((transcript, botMessage))
        synthAudioPath = ttsEntity.synthesize(botMessage)
        playProcess = subprocess.Popen(
            ["ffplay", "-noborder", "-nodisp", "-autoexit", "-i", synthAudioPath],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )
        try:
            playProcess.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            print("FFplay timed out, please check if it is installed correctly.")
        finally:
            playProcess.terminate()
        return "", chatHistory


    submitButton.click(textChat, [textInput, botComponent], [textInput, botComponent])
    textInput.submit(textChat, [textInput, botComponent], [textInput, botComponent])
    voiceChatButton.click(voiceChat, [audioInput], [textInput, botComponent])

if __name__ == "__main__":
    demo.launch()
