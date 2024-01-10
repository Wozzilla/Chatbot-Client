"""嗯...本文件中声明了一些常用的函数"""
from json import load
from enum import Enum

with open('config.json') as f:
    Configs = load(f)


class BotEnum(Enum):
    """聊天机器人类型枚举"""
    CHATGPT = 0
    CHATGLM = 1
    CHATGLM_FINE_TUNE = 2


class ASREnum(Enum):
    """语音识别类型枚举"""
    WHISPER = 0
