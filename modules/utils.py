"""本文件中声明了一些常用的函数与全局变量，供其他模块使用。"""
from datetime import datetime
from json import load, dump
from enum import Enum
import os
import atexit
import uuid
from time import mktime
from typing import TypedDict, Literal
from wsgiref.handlers import format_date_time

try:
    with open('config.json') as cfg:
        Configs = load(cfg)
except FileNotFoundError:
    raise FileNotFoundError(
        "Config file not found! Please make sure you have a 'config.json' file in {}.".format(os.getcwd())
    )


@atexit.register
def dumpConfig():
    """在程序退出时将配置文件写回磁盘"""
    with open('config.json', 'w') as cfgContent:
        dump(Configs, cfgContent, ensure_ascii=False, indent=4)


def getAvatars() -> tuple[str, str]:
    """
    返回用户头像和bot头像的url链接
    """
    return (
        "https://patchwiki.biligame.com/images/ys/a/a7/e9o4gu6ztf7zytnvvkeoerbevkjfwjr.png",
        "https://patchwiki.biligame.com/images/ys/6/6a/goj6bb8yj190midok60n2fbkk872090.png"
    )


def getMacAddress() -> str:
    """
    获取本机的MAC地址，以12位十六进制字符串表示，每两位用"-"分隔
    """
    macAddress = uuid.UUID(int=uuid.getnode()).hex[-12:].upper()
    macAddress = '-'.join([macAddress[i:i + 2] for i in range(0, 11, 2)])
    return macAddress


def getRFC1123(time: datetime = None) -> str:
    """
    获取RFC1123格式的时间戳，默认为当前时间
    :param time: datetime 时间对象
    :return: str 时间戳
    """
    if not time:
        time = datetime.now()
    return format_date_time(mktime(time.timetuple()))


class Message(TypedDict):
    """按照OpenAI的API格式定义的消息类型，可用于检查消息格式是否正确。"""
    role: Literal["user", "assistant", "system"]
    content: str


class NLGEnum(Enum):
    """聊天机器人类型枚举"""
    ChatGPT = 0  # OpenAI ChatGPT
    ChatGLM = 1  # 自行部署的ChatGLM
    ERNIE_Bot = 2  # 百度 文心一言
    Qwen = 3  # 阿里 通义千问
    Gemini = 4  # 谷歌 Gemini
    Spark = 5  # 讯飞 星火大模型


class ASREnum(Enum):
    """语音识别类型枚举"""
    WhisperAPI = 0  # Whisper API
    Whisper_Finetune = 1  # 经过微调的Whisper模型
    Baidu_ASR = 2  # 百度的TTS API


class TTSEnum(Enum):
    """语音合成类型枚举"""
    FastSpeech_Finetune = 0  # 经过微调的FastSpeech2模型
    Bert_VITS = 2  # Bert-VITS2 刻晴语音模型
    OpenAI_TTS = 3  # OpenAI的TTS模型
    Baidu_TTS = 4  # 百度的TTS API


if __name__ == '__main__':
    raise RuntimeError("This module is not executable!")
