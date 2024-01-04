import json
from enum import Enum

with open('settings.json') as f:
    Settings = json.load(f)
    assert isinstance(Settings, dict)


class BotEnum(Enum):
    """聊天机器人类型枚举"""
    CHATGPT = 0
    CHATGLM = 1
    CHATGLM_FINE_TUNE = 2
