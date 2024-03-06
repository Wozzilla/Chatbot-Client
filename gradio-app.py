"""本文件为整个项目的主文件，并使用gradio搭建界面"""
import subprocess
import traceback

import gradio as gr
from modules.NLG import *
from modules.ASR import *
from modules.TTS import *
from modules import utils

nlg_service = ChatGLM(utils.Configs["ZhipuAI"])
asr_service = BaiduASR(utils.Configs["Baidu"]["asr"])
tts_service = BaiduTTS(utils.Configs["Baidu"]["tts"])

with gr.Blocks(theme=gr.themes.Soft(), title="Chatbot Client", css="./assets/css/GenshinStyle.css",
               js="./assets/js/GenshinStyle.js") as demo:
    with gr.Row(elem_id="baseContainer"):
        with gr.Column(min_width=280, elem_id="sideBar"):
            asr_switch = gr.Dropdown([i.name for i in ASREnum], value=asr_service.type.name, interactive=True,
                                     label="选择ASR模型", elem_id="asrSwitch")
            nlg_switch = gr.Dropdown([i.name for i in NLGEnum], value=nlg_service.type.name, interactive=True,
                                     label="选择NLG模型", elem_id="nlgSwitch")
            tts_switch = gr.Dropdown([i.name for i in TTSEnum], value=tts_service.type.name, interactive=True,
                                     label="选择TTS模型", elem_id="ttsSwitch")
        with gr.Column(scale=5, elem_id="chatPanel"):
            bot_component = gr.Chatbot(label=nlg_service.type.name, avatar_images=utils.getAvatars(), elem_id="chatbot")
            with gr.Row(elem_id="inputPanel"):
                text_input = gr.Textbox(placeholder="点击输入", show_label=False, scale=4, elem_id="textInput")
                audio_input = gr.Audio(sources=["microphone"], type="filepath", show_label=False, scale=4,
                                       elem_id="audioInput")
                submit_button = gr.Button(value="发送", size="sm", min_width=80, elem_id="submitButton")
                clear_button = gr.Button(value="清除", size="sm", min_width=80, elem_id="cleanButton")


        def textChat(message: str, chat_history: list):
            """
            与聊天机器人进行文本聊天
            :param message: str 用户输入的消息
            :param chat_history: [[str, str]...] 分别为用户输入和机器人回复(先前的)
            :return: tuple[str, list[list[str, str]]] 空字符串(用以清空输入框), 更新的消息记录
            """
            bot_message = nlg_service.continuedQuery(message, chat_history)
            chat_history.append((message, bot_message))
            synth_audio_path = tts_service.synthesize(bot_message)
            subprocess.Popen(["ffplay", "-noborder", "-nodisp", "-autoexit", "-i", synth_audio_path])
            return "", chat_history


        def textStreamChat(message: str, chat_history: list) -> None:
            """
            与聊天机器人进行文本聊天(流式)
            :param message: str 用户输入的消息
            :param chat_history: [[str, str]...] 分别为用户输入和机器人回复(先前的)
            """
            this_chat = [message, ""]  # 当前的聊天记录
            for chunk in nlg_service.streamContinuedQuery(message, chat_history):
                this_chat[-1] += chunk
                bot_component.value = chat_history.extend(tuple(this_chat))
            synth_audio_path = tts_service.synthesize(this_chat[-1])
            subprocess.Popen(["ffplay", "-noborder", "-nodisp", "-autoexit", "-i", synth_audio_path])  # 调用ffplay播放音频


        def autoChat(audio: PathLike, message: str, chat_history: list) -> tuple[str, list[list[str, str]]]:
            """
            自动根据当前前端信息，选择聊天方式进行聊天

            语音聊天的优先级高于文本聊天
            :param audio: PathLike 语音文件路径
            :param message: str 用户输入的消息
            :param chat_history: [[str, str]...] 分别为用户输入和机器人回复(先前的)
            :return: tuple[str, list[list[str, str]]] 空字符串(用以清空输入框), 更新的消息记录
            """
            if not audio and not message:
                return "", chat_history
            elif audio:  # 语音聊天
                message = asr_service.transcribe(audio)  # 语音识别结果
            bot_message = nlg_service.continuedQuery(message, chat_history)
            chat_history.append((message, bot_message))
            synth_audio_path = tts_service.synthesize(bot_message)
            subprocess.Popen(["ffplay", "-noborder", "-nodisp", "-autoexit", "-i", synth_audio_path])  # 调用ffplay播放音频
            return "", chat_history


        def autoStreamChat(audio: PathLike, message: str, chat_history: list) -> None:
            """
            自动根据当前前端信息，选择聊天方式进行聊天(流式)

            语音聊天的优先级高于文本聊天
            :param audio: PathLike 语音文件路径
            :param message: str 用户输入的消息
            :param chat_history: [[str, str]...] 分别为用户输入和机器人回复(先前的)
            """
            if not audio and not message:
                text_input.value = ""
                bot_component.value = chat_history
                return
            elif audio:
                message = asr_service.transcribe(audio)  # 语音识别结果
            new_chat_history = chat_history.copy()
            new_chat_history.append((message, ""))
            for chunk in nlg_service.streamContinuedQuery(message, chat_history):
                new_chat_history[-1][1] += chunk
                bot_component.value = new_chat_history
            synth_audio_path = tts_service.synthesize(new_chat_history[-1][1])
            subprocess.Popen(["ffplay", "-noborder", "-nodisp", "-autoexit", "-i", synth_audio_path])  # 调用ffplay播放音频


        def switchNLG(select_service_name: str):
            """
            切换NLG模型
            :param select_service_name: str NLG模型名称
            :return: str NLG模型名称
            """
            global nlg_service, nlg_switch
            current_service_name = nlg_service.type.name  # 当前的NLG模型名称
            if select_service_name == current_service_name:
                return current_service_name
            else:  # 尝试切换模型
                try:
                    if select_service_name == NLGEnum.ChatGPT.name:
                        temp_service = ChatGPT(utils.Configs["OpenAI"])
                    elif select_service_name == NLGEnum.Waltz.name:
                        temp_service = Waltz(utils.Configs["Waltz"])
                    elif select_service_name == NLGEnum.ERNIE_Bot.name:
                        temp_service = ERNIEBot(utils.Configs["Baidu"]["nlg"])
                    elif select_service_name == NLGEnum.Qwen.name:
                        temp_service = Qwen(utils.Configs["Aliyun"])
                    elif select_service_name == NLGEnum.Gemini.name:
                        temp_service = Gemini(utils.Configs["Google"])
                    elif select_service_name == NLGEnum.Spark.name:
                        temp_service = Spark(utils.Configs["XFyun"])
                    else:  # 未知的模型选择，不执行切换
                        gr.Warning(f"未知的NLG模型，将不进行切换，当前：{current_service_name}")
                        return current_service_name
                    nlg_service = temp_service
                    gr.Info(f"模型切换成功，当前：{nlg_service.type.name}")
                    return nlg_service.type.name
                except Exception:
                    traceback.print_exc()
                    gr.Warning("模型切换失败，请检查网络连接或模型配置")
                    return current_service_name


        def switchASR(select_service_name: str):
            """
            切换ASR模型
            :param select_service_name: str ASR模型名称
            :return: str ASR模型名称
            """
            global asr_service, audio_input
            current_service_name = asr_service.type.name  # 当前的ASR模型
            if select_service_name == current_service_name:
                return current_service_name
            else:  # 尝试切换模型
                try:
                    if select_service_name == ASREnum.WhisperAPI.name:
                        temp_service = WhisperAPI(utils.Configs["OpenAI"])
                    elif select_service_name == ASREnum.Whisper_Finetune.name:
                        temp_service = Whisper(utils.Configs["Whisper"])
                    elif select_service_name == ASREnum.Baidu_ASR.name:
                        temp_service = BaiduASR(utils.Configs["Baidu"]["asr"])
                    else:  # 未知的模型选择，不执行切换
                        gr.Warning(f"未知的ASR模型，将不进行切换，当前：{current_service_name}")
                        return current_service_name
                    asr_service = temp_service
                    gr.Info(f"模型切换成功，当前：{asr_service.type.name}")
                    return asr_service.type.name
                except Exception:
                    traceback.print_exc()
                    gr.Warning("模型切换失败，请检查网络连接或模型配置")
                    return current_service_name


        def switchTTS(select_service_name: str):
            """
            切换TTS模型
            :param select_service_name: str TTS模型名称
            :return: str TTS模型名称
            """
            global tts_service
            current_service_name = tts_service.type.name  # 当前的TTS模型
            if select_service_name == current_service_name:
                return current_service_name
            else:  # 尝试切换模型
                try:
                    if select_service_name == TTSEnum.OpenAI_TTS.name:
                        temp_service = OpenAITTS(utils.Configs["OpenAI"])
                    elif select_service_name == TTSEnum.Bert_VITS.name:
                        temp_service = BertVITS2(utils.Configs["BertVITS2"])
                    elif select_service_name == TTSEnum.Baidu_TTS.name:
                        temp_service = BaiduTTS(utils.Configs["Baidu"]["tts"])
                    else:  # 未知的模型选择，不执行切换
                        gr.Warning(f"未知的TTS模型，将不进行切换，当前：{current_service_name}")
                        return current_service_name
                    tts_service = temp_service
                    gr.Info(f"模型切换成功，当前：{tts_service.type.name}")
                    return tts_service.type.name
                except Exception:
                    traceback.print_exc()
                    gr.Warning("模型切换失败，请检查网络连接或模型配置")
                    return current_service_name


        # 按钮绑定事件
        clear_button.click(
            fn=lambda message, chat_history, audio_data: ("", [], None),
            inputs=[text_input, bot_component, audio_input],
            outputs=[text_input, bot_component, audio_input]
        )
        # if "streamContinuedQuery" in dir(nlg_service):  # 优先使用流式聊天 TODO: 测试阶段，暂时关闭流式聊天
        #     submit_button.click(autoStreamChat, [audio_input, text_input, bot_component])
        #     text_input.submit(textStreamChat, [text_input, bot_component])
        # else:
        submit_button.click(autoChat, [audio_input, text_input, bot_component], [text_input, bot_component])
        text_input.submit(textChat, [text_input, bot_component], [text_input, bot_component])

        # 切换模型
        nlg_switch.change(switchNLG, [nlg_switch], [nlg_switch])
        asr_switch.change(switchASR, [asr_switch], [asr_switch])
        tts_switch.change(switchTTS, [tts_switch], [tts_switch])

if __name__ == "__main__":
    demo.launch()
