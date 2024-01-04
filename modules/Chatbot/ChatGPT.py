__doc__ = """该文件尝试调用OpenAI GPT API，在进行前端调试时作为后端使用"""

from modules.Chatbot.BotBase import BotBase
from modules.utils import BotEnum
from openai import OpenAI


class ChatGPT(BotBase):
    """调用ChatGPT API进行问答"""

    def __init__(self, ChatGPT_config: dict):
        self.api_key = ChatGPT_config.get("api_key", None)
        self.model = ChatGPT_config.get("model", "gpt-3.5-turbo")
        super().__init__(BotEnum.CHATGPT, self.model)
        if not self.api_key:
            raise ValueError("ChatGPT api_key is not set! Please check your 'settings.json' file.")
        self.client = OpenAI(api_key=self.api_key)

    def singleQuery(self, message, history=None) -> str:
        if history:
            self.history = history
        session = self.client.chat.completions.create(
            model="gpt-3.5-turbo", messages=[{"role": "user", "content": message}])
        return session.choices[0].message.content
