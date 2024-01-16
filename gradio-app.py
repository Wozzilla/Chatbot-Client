"""本文件为整个项目的主文件，并使用gradio搭建界面"""
import subprocess
import gradio as gr
from modules.NLG.NLG import *
from modules.ASR.ASR import *
from modules.TTS.TTS import *
from modules.utils import Configs, ASREnum, NLGEnum, TTSEnum, getAvatars

nlgService = ChatGPT(Configs["OpenAI"])
asrService = WhisperAPI(Configs["OpenAI"])
ttsService = OpenAITTS(Configs["OpenAI"])

with gr.Blocks(theme=gr.themes.Soft(),
               css="./assets/css/GenshinStyle.css", js="./assets/js/GenshinStyle.js", title="云·原神",
               ) as demo:
    with gr.Row(elem_id="baseContainer"):
        with gr.Column(min_width=280, elem_id="sideBar"):
            asrSwitch = gr.Dropdown([i.name for i in ASREnum], value=asrService.type.name, interactive=True,
                                    label="选择ASR模型", elem_id="asrSwitch")
            nlgSwitch = gr.Dropdown([i.name for i in NLGEnum], value=nlgService.type.name, interactive=True,
                                    label="选择NLG模型", elem_id="nlgSwitch")
            ttsSwitch = gr.Dropdown([i.name for i in TTSEnum], value=ttsService.type.name, interactive=True,
                                    label="选择TTS模型", elem_id="ttsSwitch")
        with gr.Column(scale=5, elem_id="chatPanel"):
            botComponent = gr.Chatbot(label=nlgService.type.name, avatar_images=getAvatars(), elem_id="chatbot")
            with gr.Row(elem_id="inputPanel"):
                textInput = gr.Textbox(placeholder="点击输入", show_label=False, scale=4, elem_id="textInput")
                audioInput = gr.Audio(sources=["microphone"], type="filepath", show_label=False, scale=4,
                                      elem_id="audioInput")
                submitButton = gr.Button(value="发送", size="sm", min_width=80, elem_id="submitButton")
                clearButton = gr.Button(value="清除", size="sm", min_width=80, elem_id="cleanButton")


        def cleanAllContent(message, chatHistory, audioData):
            """
            清除全部消息
            """
            return "", [], None


        def textChat(message: str, chatHistory: list):
            """
            与聊天机器人进行文本聊天
            :param message: str 用户输入的消息
            :param chatHistory: [[str, str]...] 分别为用户输入和机器人回复(先前的)
            """
            botMessage = nlgService.continuedQuery(message, chatHistory)
            chatHistory.append((message, botMessage))
            synthAudioPath = ttsService.synthesize(botMessage)
            subprocess.Popen(["ffplay", "-noborder", "-nodisp", "-autoexit", "-i", synthAudioPath])
            return "", chatHistory


        def autoChat(audio: PathLike, message: str, chatHistory: list):
            """
            自动根据当前前端信息，选择聊天方式进行聊天

            语音聊天的优先级高于文本聊天
            :param audio: PathLike 语音文件路径
            :param message: str 用户输入的消息
            :param chatHistory: [[str, str]...] 分别为用户输入和机器人回复(先前的)
            """
            if not audio and not message:
                return "", chatHistory
            elif audio:  # 语音聊天
                message = asrService.transcribe(audio)  # 语音识别结果
            botMessage = nlgService.continuedQuery(message, chatHistory)
            chatHistory.append((message, botMessage))
            synthAudioPath = ttsService.synthesize(botMessage)
            subprocess.Popen(["ffplay", "-noborder", "-nodisp", "-autoexit", "-i", synthAudioPath])
            return "", chatHistory


        def switchNLG(selectService: str):
            """
            切换NLG模型
            :param selectService: str NLG模型名称
            :return: str NLG模型名称
            """
            global nlgService
            currentService = nlgService.type.name  # 当前的NLG模型
            if selectService == currentService:
                gr.Warning("模型切换失败，请检查网络连接或模型配置")
                return currentService
            else:  # 尝试切换模型
                try:
                    if selectService == NLGEnum.ChatGPT.name:
                        tempService = ChatGPT(Configs["OpenAI"])
                    elif selectService == NLGEnum.ChatGLM.name:
                        tempService = ChatGLM(Configs["ChatGLM"])
                    else:  # 未知的模型选择，不执行切换
                        gr.Warning(f"未知的NLG模型，将不进行切换，当前：{currentService}")
                        return currentService
                    nlgService = tempService
                    gr.Info(f"模型切换成功，当前：{nlgService.type.name}")
                    return nlgService.type.name
                except Exception:
                    gr.Warning("模型切换失败，请检查网络连接或模型配置")
                    return currentService


        def switchASR(selectService: str):  # TODO: 待测试
            """
            切换ASR模型
            :param selectService: str ASR模型名称
            :return: str ASR模型名称
            """
            global asrService
            currentService = asrService.type.name  # 当前的ASR模型
            if selectService == currentService:
                gr.Warning("模型切换失败，请检查网络连接或模型配置")
                return currentService
            else:  # 尝试切换模型
                try:
                    if selectService == ASREnum.Whisper.name:
                        tempService = WhisperAPI(Configs["OpenAI"])
                    elif selectService == ASREnum.Whisper_Finetune.name:
                        tempService = Whisper(
                            Configs["Whisper"])  # TODO: 注意，这里的Whisper模型采用的gr.Audio接口为tuple[int, np.array]，应修改为PathLike
                    else:  # 未知的模型选择，不执行切换
                        gr.Warning(f"未知的ASR模型，将不进行切换，当前：{currentService}")
                        return currentService
                    asrService = tempService
                    gr.Info(f"模型切换成功，当前：{asrService.type.name}")
                    return asrService.type.name
                except Exception:
                    gr.Warning("模型切换失败，请检查网络连接或模型配置")
                    return currentService


        def switchTTS(selectService: str):  # TODO: 待测试
            """
            切换TTS模型
            :param selectService: str TTS模型名称
            :return: str TTS模型名称
            """
            global ttsService
            currentService = ttsService.type.name  # 当前的TTS模型
            if selectService == currentService:
                gr.Warning("模型切换失败，请检查网络连接或模型配置")
                return currentService
            else:  # 尝试切换模型
                try:
                    if selectService == TTSEnum.OpenAI_TTS.name:
                        tempService = OpenAITTS(Configs["OpenAI"])
                    elif selectService == TTSEnum.Bert_VITS2.name:
                        tempService = BertVITS2(Configs["BertVITS2"])
                    else:  # 未知的模型选择，不执行切换
                        gr.Warning(f"未知的TTS模型，将不进行切换，当前：{currentService}")
                        return currentService
                    ttsService = tempService
                    gr.Info(f"模型切换成功，当前：{ttsService.type.name}")
                    return ttsService.type.name
                except Exception:
                    gr.Warning("模型切换失败，请检查网络连接或模型配置")
                    return currentService


        # 按钮绑定事件
        clearButton.click(cleanAllContent, [textInput, botComponent, audioInput], [textInput, botComponent, audioInput])
        submitButton.click(autoChat, [audioInput, textInput, botComponent], [textInput, botComponent])
        textInput.submit(textChat, [textInput, botComponent], [textInput, botComponent])
        # 切换模型
        nlgSwitch.change(switchNLG, [nlgSwitch], [nlgSwitch])
        asrSwitch.change(switchASR, [asrSwitch], [asrSwitch])
        ttsSwitch.change(switchTTS, [ttsSwitch], [ttsSwitch])

if __name__ == "__main__":
    demo.launch()
