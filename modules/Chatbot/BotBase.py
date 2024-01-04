from abc import abstractmethod
from modules.utils import BotEnum


class BotBase:
    """聊天机器人基类"""

    def __init__(self, botType: BotEnum, model: str):
        self.botType = botType
        self.model = model
        self.history = []

    @abstractmethod
    def singleQuery(self, message) -> str:
        """
        简单地进行单次查询
        :param message: 用户输入的消息
        :return: 响应结果
        """
        pass
