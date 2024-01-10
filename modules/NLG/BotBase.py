"""该文件声明了聊天机器人的基类"""
from abc import abstractmethod
from modules.utils import BotEnum


class BotBase:
    """聊天机器人基类，建议在进行聊天机器人开发时继承该类以提高泛用型"""

    def __init__(self, botType: BotEnum, model: str, prompt: str = None):
        self.botType = botType  # 机器人类型
        self.model = model  # 机器人模型
        self.prompt = prompt  # 提示语(用于指定机器人的身份，有助于提高针对特定领域问题的效果)

    @abstractmethod
    def singleQuery(self, message: str, prompt: str = None) -> str:
        """
        简单地进行单次查询，详细文档请参考各子类的实现

        :param message: str 用户输入的消息
        :param prompt: str 提示语(用于指定机器人的身份，有助于提高针对特定领域问题的效果)
        :return: 响应结果
        """
        pass

    @abstractmethod
    def continuedQuery(self, message, history: [[str, str]], prompt: str = None):
        """
        进行带有历史记录的查询，详细文档请参考各子类的实现

        :param message: str 用户输入的消息
        :param history: [[str, str]...] 分别为用户输入和机器人回复(先前的)
        :param prompt: str 提示语(用于指定机器人的身份，有助于提高针对特定领域问题的效果)
        """
        pass
