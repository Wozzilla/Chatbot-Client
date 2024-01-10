from modules.NLG.BotBase import BotBase
from modules.utils import BotEnum
from openai import OpenAI

__doc__ = """该文件尝试调用OpenAI GPT API，在进行前端调试时作为后端使用"""


class ChatGPT(BotBase):
    """
    通过API调用ChatGPT进行问答

    API文档参考：https://platform.openai.com/docs/api-reference/chat/create?lang=python
    """

    def __init__(self, OpenAI_config: dict, prompt: str = None):
        self.api_key = OpenAI_config.get("api_key", None)
        model = OpenAI_config.get("gpt_model", "gpt-3.5-turbo")
        super().__init__(BotEnum.CHATGPT, model, prompt)
        if not self.api_key:
            raise ValueError("ChatGPT api_key is not set! Please check your 'config.json' file.")
        self.client = OpenAI(api_key=self.api_key)

    def singleQuery(self, message: str, history: [[str, str]] = None, prompt: str = None) -> str:
        """
        简单地进行单次查询

        在单次查询中也可以传入先前的历史记录，作为单次查询的辅助信息，但该历史记录并不会被记录和更新，在单词查询中仅被用作辅助机器人决策。
        :param message: str 本次用户输入
        :param history: [[str, str]...] 分别为用户输入和机器人回复(先前的)
        :param prompt: str 提示语(用于指定机器人的身份，有助于提高针对特定领域问题的效果)
        :return str 对本次聊天的回复内容
        """
        sessionPrompt = prompt if prompt else self.prompt
        if sessionPrompt:
            session = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": sessionPrompt},
                    {"role": "user", "content": message}
                ]
            )
        else:
            session = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": message}]
            )
        return session.choices[0].message.content

    def continuedQuery(self, message, history: [[str, str]], prompt: str = None):
        """
        进行带有历史记录的查询

        按照gradio官方demo chatbot_simple的开发示例，若是想实现带有历史记录的对话，无需在BotBase中自行实现历史记录的保留，建议的做法
        是在gradio中更新历史记录，每次查询时只需要调用更新后的history即可。该方法只需按照OpenAI API的要求，将[[str, str]...]形式的
        历史记录转换为[{"role": "user", "content": ""}, {"role": "assistant", "message": ""}...]的格式即可。
        :param message: str 本次用户输入
        :param history: [[str, str]...] 分别为用户输入和机器人回复(先前的)
        :param prompt: str 提示语(用于指定机器人的身份，有助于提高针对特定领域问题的效果)
        """
        sessionPrompt = prompt if prompt else self.prompt
        sessionHistory = [{"role": "system", "content": sessionPrompt}] if sessionPrompt else []
        for chat in history:
            sessionHistory.append({"role": "user", "content": chat[0]})
            sessionHistory.append({"role": "assistant", "content": chat[1]})
        sessionHistory.append({"role": "user", "content": message})
        session = self.client.chat.completions.create(model=self.model, messages=sessionHistory)
        return session.choices[0].message.content
