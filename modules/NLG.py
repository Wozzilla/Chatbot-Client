"""该文件定义了聊天机器人的后端类"""
import json
from abc import abstractmethod
from urllib.parse import urljoin

import requests

from modules.utils import NLGEnum, Configs, ChatStruct


class NLGBase:
    """聊天机器人基类，建议在进行聊天机器人开发时继承该类"""

    def __init__(self, botType: NLGEnum, model: str, prompt: str = None):
        self.type = botType  # 机器人类型
        self.model = model  # 机器人模型
        self.prompt = prompt  # 默认提示语(用于指定机器人的身份，有助于提高针对特定领域问题的效果)，优先级低于查询时传入的prompt

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

    @abstractmethod
    def checkConnection(self):
        """
        检查与Host的连接状态
        :return: bool 是否连接成功
        """
        pass

    def historyConverter(self, history: [[str, str]], prompt: str = None) -> list[ChatStruct]:
        """
        将[[str, str]...]形式的历史记录转换为[{"role": "user", "content": ""}, {"role": "assistant", "content": ""}...]的格式，
        使用场景是将gradio的Chatbot聊天记录格式转换为ChatGPT/ChatGLM3的聊天记录格式
        :param history: [[str, str]...] 分别为用户输入和机器人回复(先前的)
        :param prompt: str 提示语(用于指定机器人的身份，有助于提高针对特定领域问题的效果，允许为空)
        :return: [{"role": "user", "content": ""}, {"role": "assistant", "content": ""}...]的格式的历史记录，注意，该结果不包括
        本次的用户输入，仅转换了历史记录
        """
        sessionPrompt = prompt if prompt else self.prompt
        sessionHistory = [{"role": "system", "content": sessionPrompt}] if sessionPrompt else []
        for chat in history:
            sessionHistory.append({"role": "user", "content": chat[0]})
            sessionHistory.append({"role": "assistant", "content": chat[1]})
        return sessionHistory


class ChatGLM(NLGBase):
    """
    调用远端ChatGLM进行问答

    目标项目来自：https://github.com/THUDM/ChatGLM3
    """

    def __init__(self, ChatGLM_config: dict, prompt: str = None):
        super().__init__(NLGEnum.ChatGLM, ChatGLM_config.get("model", "NLG/ChatGLM3"), prompt)
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

    def singleQuery(self, message: str, prompt: str = None) -> str:
        """
        简单地进行单次查询

        在单次查询中也可以传入先前的历史记录，作为单次查询的辅助信息，但该历史记录并不会被记录和更新，在单词查询中仅被用作辅助机器人决策。
        :param message: str 本次用户输入
        :param prompt: str 提示语(用于指定机器人的身份，有助于提高针对特定领域问题的效果)
        :return: str 对本次聊天的回复内容
        """
        sessionPrompt = prompt if prompt else self.prompt
        try:
            response = requests.post(
                url=urljoin(self.host, 'singleQuery'),
                params={"secret": self.secret},
                json={"prompt": sessionPrompt, "message": message},
                timeout=20
            )
        except requests.exceptions.Timeout:
            raise TimeoutError("Connection to ChatGLM timed out, please check your network status.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Connection to ChatGLM failed, please check your host and secret.")
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
        sessionHistory = self.historyConverter(history, prompt)
        try:
            response = requests.post(
                url=urljoin(self.host, 'continuedQuery'),
                params={"secret": self.secret},
                json={"history": sessionHistory, "message": message},
                timeout=50
            )
        except requests.exceptions.Timeout:
            raise TimeoutError("Connection to ChatGLM timed out, please check your network status.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Connection to ChatGLM failed, please check your host and secret.")
        return response.json().get("content", "")

    def checkConnection(self):
        """
        检查与远端ChatGLM的连接状态
        :return: bool 是否连接成功
        """
        try:
            response = requests.get(
                url=self.host,
                params={"secret": self.secret},
                timeout=10
            )
            if not response.status_code == 200:
                raise ConnectionError(f"Connection to {self.model} failed, please check your host and secret.")
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Connection to {self.model} timed out, please check your network status.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Connection to {self.model} failed, please check your host and secret.")
        finally:
            print("ChatGLM remote mode connection check finished.")


class ChatGPT(NLGBase):
    """
    通过API调用ChatGPT进行问答

    API文档参考：https://platform.openai.com/docs/api-reference/chat/create?lang=python
    """

    def __init__(self, OpenAI_config: dict, prompt: str = None):
        from openai import OpenAI
        super().__init__(NLGEnum.ChatGPT, OpenAI_config.get("gpt_model", "gpt-3.5-turbo"), prompt)
        self.api_key = OpenAI_config.get("api_key", None)
        if not self.api_key:
            raise ValueError("OpenAI api_key is not set! Please check your 'config.json' file.")
        self.host = OpenAI(api_key=self.api_key)
        self.checkConnection()

    def singleQuery(self, message: str, prompt: str = None) -> str:
        """
        简单地进行单次查询

        在单次查询中也可以传入先前的历史记录，作为单次查询的辅助信息，但该历史记录并不会被记录和更新，在单词查询中仅被用作辅助机器人决策。
        :param message: str 本次用户输入
        :param prompt: str 提示语(用于指定机器人的身份，有助于提高针对特定领域问题的效果)
        :return str 对本次聊天的回复内容
        """
        sessionPrompt = prompt if prompt else self.prompt
        sessionMessage = [
            {"role": "system", "content": sessionPrompt},
            {"role": "user", "content": message}
        ] if sessionPrompt else [
            {"role": "user", "content": message}
        ]
        session = self.host.chat.completions.create(model=self.model, messages=sessionMessage)
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
        sessionHistory = self.historyConverter(history, prompt)
        sessionHistory.append({"role": "user", "content": message})
        session = self.host.chat.completions.create(model=self.model, messages=sessionHistory)
        return session.choices[0].message.content

    def checkConnection(self):
        """
        检查与OpenAI的连接状态(通过测试Chat API)
        :return: bool 是否连接成功
        """
        try:
            response = requests.post(
                url="https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "Say this is a test!"}]
                },
                timeout=10
            )
            if not response.status_code == 200:
                raise ConnectionError(f"Connection to {self.model} failed, please check your network and API status.")
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Connection to {self.model} timed out, please check your network status.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Connection to {self.model} failed, please check your network and API status.")
        finally:
            print("OpenAI connection check finished.")


class ERNIEBot(NLGBase):
    """
    通过API调用文心一言 ERNIE-Bot 进行问答

    API文档参考：https://cloud.baidu.com/doc/WENXINWORKSHOP/s/clntwmv7t
    """

    queryURL = {
        "ERNIE-Bot 4.0": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions_pro",
        "ERNIE-Bot-8K": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie_bot_8k",
        "ERNIE-Bot": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions"
    }

    def __init__(self, Baidu_config: dict, prompt: str = None):
        super().__init__(NLGEnum.ERNIE_Bot, Baidu_config.get("nlg_model", "ERNIE-Bot 4.0"), prompt)
        self.api_key = Baidu_config.get("api_key", None)
        self.secret_key = Baidu_config.get("secret_key", None)
        self.access_token = Baidu_config.get("access_token", None)
        if not self.api_key or not self.secret_key:
            raise ValueError("Baidu api_key or secret_key is not set! Please check your 'config.json' file.")
        if not self.access_token:
            self.OAuth()
        self.checkConnection()

    def OAuth(self) -> str:
        """
        执行百度OAuth2.0认证，获取access_token并写入Configs和self.access_token，若已有则覆盖
        :return: str access_token
        """
        response = requests.post(
            url="https://aip.baidubce.com/oauth/2.0/token",
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
            params={
                "client_id": self.api_key,
                "client_secret": self.secret_key,
                "grant_type": "client_credentials"
            }
        )
        access_token = response.json().get("access_token")
        Configs["Baidu"]["nlg"]["access_token"] = access_token
        self.access_token = access_token
        return access_token

    def singleQuery(self, message: str, prompt: str = None) -> str:
        sessionPrompt = prompt if prompt else self.prompt
        sessionMessage = [
            {"role": "system", "content": sessionPrompt},
            {"role": "user", "content": message}
        ] if sessionPrompt else [
            {"role": "user", "content": message}
        ]
        try:
            response = requests.post(
                url=self.queryURL[self.model],
                headers={'Content-Type': 'application/json'},
                params={"access_token": self.access_token},
                data=json.dumps({"messages": sessionMessage}),
                timeout=20
            )
            responseJson = json.loads(response.text)
            if responseJson.get("error_code") == 110:  # 根据百度API文档，110为access_token过期，重新请求即可
                self.OAuth()
                return self.singleQuery(message, prompt)
        except requests.exceptions.Timeout:
            raise TimeoutError("Connection to 'aip.baidubce.com' timed out, please check your network status.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Connection to 'aip.baidubce.com' failed, please check your network status.")
        return responseJson.get("result")

    def continuedQuery(self, message, history: [[str, str]], prompt: str = None):
        """
        进行带有历史记录的查询
        """
        sessionHistory = self.historyConverter(history, prompt)
        sessionHistory.append({"role": "user", "content": message})
        try:
            response = requests.post(
                url=self.queryURL[self.model],
                headers={'Content-Type': 'application/json'},
                params={"access_token": self.access_token},
                data=json.dumps({"messages": sessionHistory}),
                timeout=20
            )
            responseJson = json.loads(response.text)
            if responseJson.get("error_code") == 110:  # 根据百度API文档，110为access_token过期，重新请求即可
                self.OAuth()
                return self.continuedQuery(message, history, prompt)
        except requests.exceptions.Timeout:
            raise TimeoutError("Connection to 'aip.baidubce.com' timed out, please check your network status.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Connection to 'aip.baidubce.com' failed, please check your network status.")
        return responseJson.get("result")

    def checkConnection(self):
        """
        检查与OpenAI的连接状态(通过测试Chat API)
        :return: bool 是否连接成功
        """
        try:
            response = requests.post(
                url=self.queryURL["ERNIE-Bot"],
                headers={'Content-Type': 'application/json'},
                params={"access_token": self.access_token},
                data=json.dumps({"messages": [{"role": "user", "content": "说“你好”"}]}),
                timeout=20
            )
            responseJson = json.loads(response.text)
            if responseJson.get("error_code") == 110:  # 根据百度API文档，110为access_token过期，重新请求即可
                self.OAuth()
                return self.checkConnection()
        except requests.exceptions.Timeout:
            raise TimeoutError("Connection to 'aip.baidubce.com' timed out, please check your network status.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Connection to 'aip.baidubce.com' failed, please check your network status.")
        finally:
            print("ERNIE-Bot connection check finished.")


if __name__ == '__main__':
    raise RuntimeError("This module is not executable!")
