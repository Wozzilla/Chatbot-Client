"""该文件定义了聊天机器人的后端类"""
import _thread as thread
import hashlib
import hmac
import json
import re
from abc import abstractmethod
from base64 import b64encode
from random import randint
from ssl import CERT_NONE as SSL_CERT_NONE
from urllib.parse import urljoin, urlparse, urlencode

import google.api_core.exceptions
import requests
from websocket import WebSocketApp

from modules.utils import NLGEnum, Configs, Message, getRFC1123, getMacAddress


class NLGBase:
    """聊天机器人基类，建议在进行聊天机器人开发时继承该类"""
    try:
        import tiktoken
        tokenEncoding = tiktoken.get_encoding("cl100k_base")
    except ImportError:
        tokenEncoding = None

    def __init__(self, nlg_type: NLGEnum, model: str, prompt: str = None):
        self.type = nlg_type  # 机器人类型
        self.model = model  # 机器人模型
        self.prompt = prompt  # 默认提示语(用于指定机器人的身份，有助于提高针对特定领域问题的效果)，优先级低于查询时传入的prompt

    @abstractmethod
    def singleQuery(self, message: str, prompt: str = None) -> str:
        """
        简单地进行单次查询

        允许为本次查询单独指定prompt，使用优先级按照 参数prompt > 全局prompt > None 的顺序
        :param message: str 本次用户输入
        :param prompt: str 提示语(用于指定机器人的身份，有助于提高针对特定领域问题的效果)
        :return: str 对本次聊天的回复内容
        """

    @abstractmethod
    def continuedQuery(self, message: str, history: list[list[str, str]], prompt: str = None):
        """
        进行带有历史记录的查询

        按照gradio官方demo chatbot_simple的开发示例，若是想实现带有历史记录的对话，无需自行实现历史记录的保留，建议的做法是在gradio中更新历史记录，每次查询时只需要调用更新后的history即可。

        大多数API要求历史记录(含prompt)的格式应当为[{"role": "user", "content": ""}, {"role": "assistant", "message":
        ""}...]，而大多数前端的历史记录格式为[[str, str]...]，因此需要在调用前进行转换。可借助historyConverter方法进行转换。
        :param message: str 本次用户输入
        :param history: List[List[str, str]...] 分别为用户输入和机器人回复(先前的)
        :param prompt: str 提示语(用于指定机器人的身份，有助于提高针对特定领域问题的效果)
        """

    @abstractmethod
    def checkConnection(self):
        """
        检查与Host的连接状态
        对于多数未设计检查连接状态的API，可参考OpenAI的做法：直接让后端回复一句简单的话，若回复成功则自然连接成功。
        """

    def converterHistory(self, history: [[str, str]], prompt: str = None) -> list[Message]:
        """
        将[[str, str]...]形式的历史记录转换为[{"role": "user", "content": ""}, {"role": "assistant", "content": ""}...]的格式，
        使用场景是将gradio的Chatbot聊天记录格式转换为ChatGPT/ChatGLM3的聊天记录格式
        :param history: [[str, str]...] 分别为用户输入和机器人回复(先前的)
        :param prompt: str 提示语(用于指定机器人的身份，有助于提高针对特定领域问题的效果，允许为空)
        :return: [{"role": "user", "content": ""}, {"role": "assistant", "content": ""}...]的格式的历史记录，注意，该结果不包括
        本次的用户输入，仅转换了历史记录
        """
        sessionPrompt = prompt if prompt else self.prompt
        sessionHistory = [Message(role="system", content=sessionPrompt)] if sessionPrompt else []
        for chat in history:
            sessionHistory.append(Message(role="user", content=chat[0]))
            sessionHistory.append(Message(role="assistant", content=chat[1]))
        return sessionHistory

    @staticmethod
    def lenOfMessages(history: list[Message] = None, message: str = None) -> int:
        """
        计算历史记录中，content部分的总长度，以便于判断是否超出了API的token数限制。

        若已将本次输入计入历史记录，则无需传入message

        或者可以只传入message，不传入history，仅统计本次输入的长度
        :param history: list[Message] 历史记录
        :param message: str 本次用户输入
        """
        length = 0
        if history:
            length += sum([len(message["content"]) for message in history])
        if message:
            length += len(message)
        return length

    @staticmethod
    def lenOfTokens(history: list[Message] = None, message: str = None, token_per_zh_char: float = None) -> int:
        """
        估算消息的token长度
        :param history: list[Message] 历史记录
        :param message: str 本次用户输入
        :param token_per_zh_char: float 每个中文字符的token数，根据经验，单个汉字的token数大概为1/2~4/3。在使用tiktoken库时，该参数无效
        :return: int 估算的token数。由于不同的API的tokenize方法不同，因此该结果仅供参考
        """
        content = ""
        if history:
            for message in history:
                content += message["content"]
        if message:
            content += message
        if NLGBase.tokenEncoding:
            return len(NLGBase.tokenEncoding.encode(content))
        else:  # 未安装tiktoken库，则只能根据经验进行估算
            # 根据 Moonshot AI的文档(https://platform.moonshot.cn/docs/docs#基本概念介绍)中的经验介绍，
            # token和汉字的比例大约为1:1.5~1:2，而token和英文单词的比例大约为1:1.2，因此我们可以根据这个比例进行估算
            token_per_en_word = 1.2  # 英文单词的token数
            if not token_per_zh_char:
                token_per_zh_char = 1.33  # 取1:1.5
            word_list = re.split("[ ,.?!';:()\[\]{}\t\n]", content)  # 分词
            word_list = [word for word in word_list if word != ""]  # 去除空字符串
            token_num = 0
            for word in word_list:
                if word.isascii():
                    token_num += token_per_en_word
                else:  # 此时为英文与其他语言混合的情况
                    sub_word_list = re.split("[\u4e00-\u9fff]", word)  # 根据中文字符分词
                    zh_char_num = sub_word_list.count("")  # 空字符串的数量即为中文字符的数量
                    token_num += zh_char_num * token_per_zh_char
                    token_num += (len(sub_word_list) - zh_char_num) * token_per_en_word  # 英文单词的数量
            return int(token_num)


class Waltz(NLGBase):
    """
    调用远端自部署Waltz进行问答

    目标项目来自：https://github.com/THUDM/ChatGLM3

    实际部署的项目为：https://github.com/Wozzilla/ChatGLM3，基于ChatGLM原始项目fine-tuning得到的修改版模型
    """

    def __init__(self, Waltz_config: dict, prompt: str = None):
        super().__init__(NLGEnum.ChatGLM, Waltz_config.get("model", "Waltz"), prompt)
        self.host, self.secret = None, None
        self.mode = Waltz_config.get("mode", "remote")
        if self.mode == "remote":
            self.host = Waltz_config.get("host", None)
            self.secret = Waltz_config.get("secret", None)
            if not self.host:
                raise ValueError("Waltz host is not set! Please check your 'config.json' file.")
            self.checkConnection()
        else:
            raise NotImplementedError("Waltz local mode is not implemented yet!")

    def singleQuery(self, message: str, prompt: str = None) -> str:
        session_prompt = prompt if prompt else self.prompt
        try:
            response = requests.post(
                url=urljoin(self.host, 'singleQuery'),
                params={"secret": self.secret},
                json={"prompt": session_prompt, "message": message},
                timeout=20
            )
        except requests.exceptions.Timeout:
            raise TimeoutError("Connect to Waltz timed out, please check your network status.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Connect to Waltz failed, please check your host and secret.")
        return response.json().get("content", "")

    def continuedQuery(self, message: str, history: list[list[str, str]], prompt: str = None) -> str:
        session_history = self.converterHistory(history, prompt)
        try:
            response = requests.post(
                url=urljoin(self.host, 'continuedQuery'),
                params={"secret": self.secret},
                json={"history": session_history, "message": message},
                timeout=50
            )
        except requests.exceptions.Timeout:
            raise TimeoutError("Connect to Waltz timed out, please check your network status.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Connect to Waltz failed, please check your host and secret.")
        return response.json().get("content", "")

    def checkConnection(self):
        """
        检查与远端ChatGLM的连接状态

        在设计阶段，我们的ChatGLM项目便在API层面增添了一个用于检查状态的接口，同时便于扩展，以支持更多功能。
        :return: bool 是否连接成功
        """
        try:
            response = requests.get(
                url=self.host,
                params={"secret": self.secret},
                timeout=10
            )
            if response.status_code != 200:
                raise ConnectionError(f"Connect to {self.model} failed, please check your host and secret.")
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Connect to {self.model} timed out, please check your network status.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Connect to {self.model} failed, please check your host and secret.")
        finally:
            print("Waltz remote mode connection check finished.")


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
        session_prompt = prompt if prompt else self.prompt
        session_message = [
            Message(role="system", content=session_prompt),
            Message(role="user", content=message)
        ] if session_prompt else [
            Message(role="user", content=message)
        ]
        session = self.host.chat.completions.create(
            model=self.model,
            messages=session_message
        )
        return session.choices[0].message.content

    def continuedQuery(self, message: str, history: list[list[str, str]], prompt: str = None):
        session_history = self.converterHistory(history, prompt)
        session_history.append(Message(role="user", content=message))
        session = self.host.chat.completions.create(
            model=self.model,
            messages=session_history
        )
        return session.choices[0].message.content

    def checkConnection(self):
        """
        检查与OpenAI的连接状态(通过一次简单的问答，以测试API可用性)
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
                    "messages": [Message(role="user", content="Say this is a test!")]
                },
                timeout=10
            )
            if response.status_code != 200:
                raise ConnectionError(f"Connect to {self.model} failed, please check your network and API status.")
            else:
                print(f"Connected to {self.model} successfully.")
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Connection to {self.model} timed out, please check your network status.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Connect to {self.model} failed, please check your network and API status.")
        except ConnectionError as e:
            raise e
        finally:
            print("OpenAI connection check finished.")


class ChatGLM(NLGBase):
    """
    通过API调用ChatGLM进行问答

    API文档参考：https://open.bigmodel.cn/dev/api#sdk
    """
    model_list = ["glm-3-turbo", "glm-4", "glm-4v"]

    def __init__(self, ZhipuAI_config: dict, prompt: str = None):
        from zhipuai import ZhipuAI
        super().__init__(NLGEnum.ChatGLM, ZhipuAI_config.get("nlg_model", "glm-4"), prompt)
        self.api_key = ZhipuAI_config.get("api_key", None)
        if not self.api_key:
            raise ValueError("ZhipuAI api_key is not set! Please check your 'config.json' file.")
        if self.model not in self.model_list:
            raise ValueError(f"Unsupported ChatGLM model: '{self.model}', currently only support {self.model_list}")
        self.host = ZhipuAI(api_key=self.api_key)
        self.checkConnection()

    def singleQuery(self, message: str, prompt: str = None) -> str:
        from zhipuai import ZhipuAIError
        session_prompt = prompt if prompt else self.prompt
        session_message = [
            Message(role="system", content=session_prompt),
            Message(role="user", content=message)
        ] if session_prompt else [
            Message(role="user", content=message)
        ]
        try:
            response = self.host.chat.completions.create(
                model=self.model,
                messages=session_message
            )
            return response.choices[0].message.content
        except ZhipuAIError as e:
            raise ConnectionError(f"Connect to {self.model} failed, {e}")

    def streamSingleQuery(self, message: str, prompt: str = None) -> str:
        from zhipuai import ZhipuAIError
        session_prompt = prompt if prompt else self.prompt
        session_message = [
            Message(role="system", content=session_prompt),
            Message(role="user", content=message)
        ] if session_prompt else [
            Message(role="user", content=message)
        ]
        try:
            response = self.host.chat.completions.create(
                model=self.model,
                messages=session_message,
                stream=True
            )
            for chunk in response:
                yield chunk.choices[0].delta.content
        except ZhipuAIError as e:
            raise ConnectionError(f"Connect to {self.model} failed, {e}")

    def continuedQuery(self, message: str, history: list[list[str, str]], prompt: str = None):
        from zhipuai import ZhipuAIError
        session_history = self.converterHistory(history, prompt)
        session_history.append(Message(role="user", content=message))
        try:
            response = self.host.chat.completions.create(
                model=self.model,
                messages=session_history
            )
            return response.choices[0].message.content
        except ZhipuAIError as e:
            raise ConnectionError(f"Connect to {self.model} failed, {e}")

    def streamContinuedQuery(self, message: str, history: list[list[str, str]], prompt: str = None):
        from zhipuai import ZhipuAIError
        session_history = self.converterHistory(history, prompt)
        session_history.append(Message(role="user", content=message))
        try:
            response = self.host.chat.completions.create(
                model=self.model,
                messages=session_history,
                stream=True
            )
            for chunk in response:
                yield chunk.choices[0].delta.content
        except ZhipuAIError as e:
            raise ConnectionError(f"Connect to {self.model} failed, {e}")

    def checkConnection(self):
        try:
            response = self.host.chat.completions.create(
                model=self.model,
                messages=[Message(role="user", content="说“你好！”")]
            )
            if re.match(".*你好.*", response.choices[0].message.content):
                print("ChatGLM connection check finished.")
            else:
                raise ConnectionError("Connect to ChatGLM failed, please check your network status and API config.")
        except Exception as e:
            raise ConnectionError(f"Connect to ChatGLM failed, {e}")


class ERNIEBot(NLGBase):
    """
    通过API调用文心一言(ERNIE-Bot)进行问答

    API文档参考：https://cloud.baidu.com/doc/WENXINWORKSHOP/s/clntwmv7t
    """

    query_url = {
        "ERNIE-Bot 4.0": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions_pro",
        "ERNIE-Bot-8K": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie_bot_8k",
        "ERNIE-Bot": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions",
        "ERNIE-3.5-4K-0205": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie-3.5-4k-0205",
        "ERNIE-3.5-8K-0205": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie-3.5-8k-0205",
        "ERNIE-3.5-8K-1222": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie-3.5-8k-1222"
    }

    def __init__(self, Baidu_config: dict, prompt: str = None):
        super().__init__(NLGEnum.ERNIE_Bot, Baidu_config.get("model", "ERNIE-Bot 4.0"), prompt)
        self.api_key = Baidu_config.get("api_key", None)
        self.secret_key = Baidu_config.get("secret_key", None)
        self.access_token = Baidu_config.get("access_token", None)
        if not self.api_key or not self.secret_key:
            raise ValueError("Baidu api_key or secret_key is not set! Please check your 'config.json' file.")
        if self.model not in self.query_url.keys():
            raise ValueError(f"Unsupported ERNIE-Bot model: '{self.model}', please check your 'config.json' file.")
        if not self.access_token:
            self.OAuth()
        self.checkConnection()

    def OAuth(self) -> str:
        """
        执行百度OAuth2.0认证，获取access_token并写入Configs和self.access_token，在程序退出时会自动写回配置文件

        API文档参考：https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Dlkm79mnx
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
        session_prompt = prompt if prompt else self.prompt
        session_message = [
            Message(role="system", content=session_prompt),
            Message(role="user", content=message)
        ] if session_prompt else [
            Message(role="user", content=message)
        ]
        try:
            response = requests.post(
                url=self.query_url[self.model],
                headers={'Content-Type': 'application/json'},
                params={"access_token": self.access_token},
                data=json.dumps({"messages": session_message}),
                timeout=20
            )
            response_json = json.loads(response.text)
            if response_json.get("error_code") == 110:  # 根据百度API文档，110为access_token过期，重新请求即可
                self.OAuth()
                return self.singleQuery(message, prompt)
            else:
                return response_json.get("result")
        except requests.exceptions.Timeout:
            raise TimeoutError("Connect to 'aip.baidubce.com' timed out, please check your network status.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Connect to 'aip.baidubce.com' failed, please check your network status.")

    def continuedQuery(self, message, history: [[str, str]], prompt: str = None):
        session_history = self.converterHistory(history, prompt)
        session_history.append(Message(role="user", content=message))
        try:
            response = requests.post(
                url=self.query_url[self.model],
                headers={'Content-Type': 'application/json'},
                params={"access_token": self.access_token},
                data=json.dumps({"messages": session_history}),
                timeout=20
            )
            response_json = json.loads(response.text)
            if response_json.get("error_code") == 110:  # 根据百度API文档，110为access_token过期，重新请求即可
                self.OAuth()
                return self.continuedQuery(message, history, prompt)
        except requests.exceptions.Timeout:
            raise TimeoutError("Connect to 'aip.baidubce.com' timed out, please check your network status.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Connect to 'aip.baidubce.com' failed, please check your network status.")
        return response_json.get("result")

    def checkConnection(self):
        """
        检查与千帆大模型平台的连接状态(通过一次简单的问答，以测试API可用性)
        """
        try:
            response = requests.post(
                url=self.query_url["ERNIE-Bot"],
                headers={'Content-Type': 'application/json'},
                params={"access_token": self.access_token},
                data=json.dumps({"messages": [Message(role="user", content="说“你好”")]}),
                timeout=20
            )
            response_json = json.loads(response.text)
            if response_json.get("error_code") == 110:  # 根据百度API文档，110为access_token过期，重新请求即可
                self.OAuth()
                return self.checkConnection()
        except requests.exceptions.Timeout:
            raise TimeoutError("Connect to 'aip.baidubce.com' timed out, please check your network status.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Connect to 'aip.baidubce.com' failed, please check your network status.")
        finally:
            print("ERNIE-Bot connection check finished.")


class Qwen(NLGBase):
    """
    通过API调用通义千问进行问答

    API文档参考：https://help.aliyun.com/zh/dashscope/developer-reference/api-details
    """
    from dashscope import Generation
    model_dict: dict[str, str] = {
        "qwen-turbo": Generation.Models.qwen_turbo,
        "qwen-plus": Generation.Models.qwen_plus,
        "qwen-max": Generation.Models.qwen_max,
        "qwen-max-1201": "qwen-max-1201",
        "qwen-max-longcontext": "qwen-max-longcontext"
    }

    def __init__(self, Aliyun_config: dict, prompt: str = None):
        super().__init__(NLGEnum.Qwen, Aliyun_config.get("nlg_model", "qwen-max"), prompt)
        self.api_key = Aliyun_config.get("api_key", None)
        if not self.api_key:
            raise ValueError("Aliyun api_key is not set! Please check your 'config.json' file.")
        if self.model not in self.model_dict.keys():
            raise ValueError(f"Unsupported Qwen model: '{self.model}', please check your 'config.json' file.")
        self.checkConnection()

    def singleQuery(self, message: str, prompt: str = None) -> str:
        from dashscope import Generation
        from dashscope.api_entities.dashscope_response import Role
        session_prompt = prompt if prompt else self.prompt
        session_message = [
            Message(role=Role.SYSTEM, content=session_prompt),
            Message(role=Role.USER, content=message)
        ] if session_prompt else [
            Message(role=Role.USER, content=message)
        ]
        response = Generation.call(
            model=self.model_dict[self.model],
            api_key=self.api_key,
            messages=session_message,
            seed=randint(0, 10000),
            result_format='message'
        )
        if response.status_code != requests.codes.ok:
            raise ConnectionError(
                f"""Connect to {self.model} failed, please check your network and API status.
                Error Info:
                    Request id:    {response.request_id}
                    Status code:   {response.status_code}
                    Error code:    {response.code}
                    Error message: {response.message}"""
            )
        return response.output.choices[0].message.content

    def continuedQuery(self, message: str, history: list[list[str, str]], prompt: str = None):
        from dashscope import Generation
        from dashscope.api_entities.dashscope_response import Role
        session_history = self.converterHistory(history, prompt)
        session_history.append(Message(role=Role.USER, content=message))
        response = Generation.call(
            model=self.model_dict[self.model],
            api_key=self.api_key,
            messages=session_history,
            seed=randint(0, 10000),
            result_format='message'
        )
        if response.status_code != requests.codes.ok:
            raise ConnectionError(
                f"""Connect to {self.model} failed, please check your network and API status.
                Error Info:
                    Request id:    {response.request_id}
                    Status code:   {response.status_code}
                    Error code:    {response.code}
                    Error message: {response.message}"""
            )
        return response.output.choices[0].message.content

    def checkConnection(self):
        """
        检查与阿里云 通义千问的连接状态(通过一次简单的问答，以测试API可用性)
        """
        from dashscope import Generation
        from dashscope.api_entities.dashscope_response import Role
        session_message = [Message(role=Role.USER, content="说“你好”")]
        response = Generation.call(
            model=self.model_dict[self.model],
            api_key=self.api_key,
            messages=session_message,
            result_format='message'
        )
        if response.status_code != requests.codes.ok:
            raise ConnectionError(
                f"""Connect to {self.model} failed, please check your network and API status.
                Error Info:
                    Request id:    {response.request_id}
                    Status code:   {response.status_code}
                    Error code:    {response.code}
                    Error message: {response.message}"""
            )
        print("Qwen connection check finished.")


class Gemini(NLGBase):
    """
    通过API调用Gemini进行问答

    API文档参考：https://ai.google.dev/tutorials/python_quickstart
    """
    import google.generativeai as genai
    host = genai  # 根据官方demo，似乎genai应为单例对象，因此此处将其设计为类变量

    def __init__(self, Google_config: dict, prompt: str = None):
        super().__init__(NLGEnum.Gemini, Google_config.get("nlg_model", "gemini-pro"), prompt)
        self.api_key = Google_config.get("api_key", None)
        if not self.api_key:
            raise ValueError("Gemini api_key is not set! Please check your 'config.json' file.")
        self.host.configure(api_key=self.api_key)
        self.checkConnection()

    def singleQuery(self, message: str, prompt: str = None) -> str:
        """
        看起来Genimi的API并不支持单独提供prompt，实际上prompt参数并未使用
        """
        try:
            model = self.host.GenerativeModel(self.model)
            response = model.generate_content(
                contents=[message],
            )
            print(response.candidates)
            return response.text
        except google.api_core.exceptions.Unauthenticated:
            raise ConnectionRefusedError("Connect to Gemini failed due to unauthenticated, please check your API key.")
        except google.api_core.exceptions.RetryError:
            raise TimeoutError(
                "Connect to Gemini timed out, please check your network status and make sure Gemini is available in your region.")
        except google.api_core.exceptions.ServiceUnavailable:
            raise ConnectionError("Connect to Gemini failed, please check your network status.")

    def continuedQuery(self, message: str, history: list[list[str, str]], prompt: str = None):
        pass

    def checkConnection(self):
        pass


class Spark(NLGBase):
    """
    通过API调用星火大模型进行问答

    API文档参考：https://www.xfyun.cn/doc/spark/Web.html
    """
    domain_dict = {
        "v3.5": "generalv3.5",
        "v3.1": "generalv3",
        "v2.1": "generalv2",
        "v1.1": "general"
    }
    max_token_dict = {
        "v3.5": 8192,
        "v3.1": 8192,
        "v2.1": 8192,
        "v1.1": 4096
    }

    def __init__(self, XFyun_config: dict, prompt: str = None):
        super().__init__(NLGEnum.Spark, XFyun_config.get("nlg_model", "v3.5"), prompt)
        self.app_id = XFyun_config.get("app_id", None)
        self.api_key = XFyun_config.get("api_key", None)
        self.api_secret = XFyun_config.get("api_secret", None)
        if not self.api_key or not self.api_secret or not self.app_id:
            raise ValueError("XFyun app_id or api_key or api_secret is not set! Please check your 'config.json' file.")
        if self.model not in ["v3.5", "v3.1", "v2.1", "v1.1"]:
            raise ValueError(f"Unsupported Spark model: '{self.model}', currently only support v3.5, v3.1, v2.1, v1.1")
        self.domain = self.domain_dict[self.model]
        self.max_token = self.max_token_dict[self.model]
        self.gpt_url = f"wss://spark-api.xf-yun.com/{self.model}/chat"  # v3.5环境的地址
        self.host = urlparse(self.gpt_url).netloc
        self.path = urlparse(self.gpt_url).path
        self.checkConnection()

    def getQueryURL(self) -> str:
        """
        讯飞开放平台通用鉴权认证，生成WebSocket的请求地址

        鉴权API文档参考：https://www.xfyun.cn/doc/spark/general_url_authentication.html
        :return str: token
        """
        date = getRFC1123()
        signature_origin = f"host: {self.host}\ndate: {date}\nGET {self.path} HTTP/1.1"
        signature_sha = hmac.new(self.api_secret.encode('utf-8'), signature_origin.encode(),
                                 digestmod=hashlib.sha256).digest()
        signature_sha_base64 = b64encode(signature_sha).decode()
        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = b64encode(authorization_origin.encode()).decode()
        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        url = self.gpt_url + '?' + urlencode(v)
        return url

    def _onMessage(self, ws, message):
        data = json.loads(message)
        code = data['header']['code']
        if code != 0:
            ws.close()
            raise ConnectionError(f"Request to '{self.host}' error: {code}, {data}")
        else:
            choices = data["payload"]["choices"]
            status = choices["status"]
            content = choices["text"][0]["content"]
            ws.response_content += content
            if status == 2:
                ws.close()

    def _onError(self, ws, error):  # 收到websocket错误的处理
        raise ConnectionError(f"Request to '{self.host}' error: {error}")

    def _onOpen(self, ws: WebSocketApp):  # 收到websocket连接建立的处理
        request_data = {
            "header": {
                "app_id": self.app_id,
                "uid": getMacAddress(),
            },
            "parameter": {
                "chat": {
                    "domain": self.domain,
                    "temperature": 0.5,  # 默认温度
                    "max_tokens": 2048  # 默认最大生成长度
                }
            },
            "payload": {
                "message": {
                    "text": ws.session_message
                }
            }
        }

        def run(ws):  # 新线程的运行函数
            data = json.dumps(request_data)
            ws.send(data)

        thread.start_new_thread(run, (ws,))

    def singleQuery(self, message: str, prompt: str = None) -> str:
        session_prompt = prompt if prompt else self.prompt
        session_message = [
            Message(role="system", content=session_prompt),
            Message(role="user", content=message)
        ] if session_prompt else [
            Message(role="user", content=message)
        ]
        ws = WebSocketApp(
            url=self.getQueryURL(),
            on_message=self._onMessage,
            on_error=self._onError,
            on_open=self._onOpen
        )
        if self.lenOfTokens(message=message) > self.max_token:
            raise ValueError(f"Message length exceeds the maximum token limit: {self.max_token}")
        ws.session_message = session_message
        ws.response_content = ""
        ws.run_forever(sslopt={"cert_reqs": SSL_CERT_NONE})
        return ws.response_content

    def continuedQuery(self, message: str, history: list[list[str, str]], prompt: str = None):
        session_history = self.converterHistory(history, prompt)
        session_history.append(Message(role="user", content=message))
        ws = WebSocketApp(
            url=self.getQueryURL(),
            on_message=self._onMessage,
            on_error=self._onError,
            on_open=self._onOpen
        )
        while self.lenOfTokens(session_history) > self.max_token:
            session_history.pop(0)  # 保证总的token数不超过最大限制
        ws.session_message = session_history
        ws.response_content = ""
        ws.run_forever(sslopt={"cert_reqs": SSL_CERT_NONE})
        return ws.response_content

    def checkConnection(self):
        try:
            result = self.singleQuery("说“你好”")
            if re.match(".*你好.*", result):
                print("Spark connection check finished.")
        except ConnectionError as e:
            raise e


if __name__ == '__main__':
    raise RuntimeError("This module is not executable!")
