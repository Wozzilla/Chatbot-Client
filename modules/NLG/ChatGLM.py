"""该文件声明一个ChatGLM类，用于调用ChatGLM模型进行问答"""
from urllib.parse import urljoin
import requests
from modules.NLG.BotBase import BotBase
from modules.utils import BotEnum


class ChatGLM(BotBase):
    """
    调用远端(通过API)或本地(暂时没做)ChatGLM进行问答
    """

    def __init__(self, ChatGLM_config: dict, prompt: str = None):
        self.host, self.secret = None, None
        self.mode = ChatGLM_config.get("mode", "remote")
        if self.mode == "remote":
            self.host = ChatGLM_config.get("host", None)
            self.secret = ChatGLM_config.get("secret", None)
            if not self.host:
                raise ValueError("ChatGLM host is not set! Please check your 'config.json' file.")
            self.checkConnection()
        else:
            raise NotImplementedError("ChatGLM local mode is not implemented yet!")
        super().__init__(BotEnum.CHATGLM, ChatGLM_config.get("model", "ChatGLM3"), prompt)

    def checkConnection(self):
        """
        检查与远端ChatGLM的连接状态
        :return: bool 是否连接成功
        """
        try:
            request = requests.get(url=self.host, params={"secret": self.secret}, timeout=5)
            return request.status_code == 200
        except requests.exceptions.Timeout:
            raise TimeoutError("Connection to ChatGLM timed out, please check your network status.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Connection to ChatGLM failed, please check your host and secret.")
        finally:
            print("ChatGLM remote mode connection check finished.")

    def singleQuery(self, message: str, prompt: str = None) -> str:
        """
        简单地进行单次查询

        在单次查询中也可以传入先前的历史记录，作为单次查询的辅助信息，但该历史记录并不会被记录和更新，在单词查询中仅被用作辅助机器人决策。
        :param message: str 本次用户输入
        :param prompt: str 提示语(用于指定机器人的身份，有助于提高针对特定领域问题的效果)
        :return: str 对本次聊天的回复内容
        """
        sessionPrompt = prompt if prompt else self.prompt
        response = requests.post(
            url=urljoin(self.host, 'singleQuery'),
            params={"secret": self.secret},
            json={"prompt": sessionPrompt, "message": message},
            timeout=20
        )
        return response.json().get("content", "")

    def continuedQuery(self, message: str, history: [[str, str]], prompt: str = None) -> str:
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
        response = requests.post(
            url=urljoin(self.host, 'continuedQuery'),
            params={"secret": self.secret},
            json={"history": sessionHistory, "message": message},
            timeout=20
        )
        return response.json().get("content", "")
