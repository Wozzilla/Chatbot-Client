"""本文件中声明了一些常用的函数与全局变量，供其他模块使用。"""
from json import load
from enum import Enum
import os

try:
    with open('config.json') as f:
        Configs = load(f)
except FileNotFoundError:
    raise FileNotFoundError(
        "Config file not found! Please make sure you have a 'config.json' file in {}.".format(os.getcwd()))


def getAvatars():
    """
    返回用户头像和bot头像的url链接
    """
    return (
        "https://patchwiki.biligame.com/images/ys/a/a7/e9o4gu6ztf7zytnvvkeoerbevkjfwjr.png",
        "https://patchwiki.biligame.com/images/ys/6/6a/goj6bb8yj190midok60n2fbkk872090.png"
    )


class NLGEnum(Enum):
    """聊天机器人类型枚举"""
    ChatGPT = 0
    ChatGLM = 1  # 原始ChatGLM模型


class ASREnum(Enum):
    """语音识别类型枚举"""
    WhisperAPI = 0  # Whisper API
    Whisper_Finetune = 1  # 经过微调的Whisper模型


class TTSEnum(Enum):
    """语音合成类型枚举"""
    FastSpeech_Finetune = 0  # 经过微调的FastSpeech2模型
    Bert_VITS = 2  # Bert-VITS2 刻晴语音模型
    OpenAI_TTS = 3  # OpenAI的TTS模型


if __name__ == '__main__':
    raise RuntimeError("This module is not executable!")
