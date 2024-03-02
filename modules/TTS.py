"""该文件定义了语音合成的后端类"""
import os
from abc import abstractmethod
from os import PathLike
from urllib.parse import urlencode, urljoin

import numpy as np
import requests
from scipy.io.wavfile import write as wavwrite

from modules.utils import TTSEnum, Configs, getMacAddress


class TTSBase:
    """语音合成的后端类，所有语音合成后端都应该继承自该类"""

    def __init__(self, ttsType: TTSEnum, model: str, voice: str):
        self.type = ttsType
        self.model = model
        self.voice = voice
        self.savePath = os.path.join(os.getcwd(), 'download').replace('\\', '/')  # 默认文件下载路径
        if not os.path.exists(self.savePath):
            os.mkdir(self.savePath)

    @abstractmethod
    def synthesize(self, text) -> PathLike:
        """
        语音合成

        该方法将调用实际的语音合成模型，将文本转换为语音，具体参数详见子类。
        :param text: str 待合成的文本
        :return: PathLike 合成后的语音文件路径
        """
        pass

    @abstractmethod
    def checkConnection(self):
        """
        检查连接状况，当无法连接远端时，应触发对应的Exception，以便于前端进行提示

        具体实现详见子类
        """
        pass


class BertVITS2(TTSBase):
    """
    调用远端Bert-VITS2模型进行语音合成

    目标项目来自：https://github.com/fishaudio/Bert-VITS2
    """

    def __init__(self, BertVITS2_config: dict):
        super().__init__(TTSEnum.Bert_VITS, BertVITS2_config.get("model", "Bert-VITS2-Keqing"),
                         BertVITS2_config.get("voice", "刻晴"))
        self.host, self.secret = None, None
        self.voice = BertVITS2_config.get("voice", "刻晴")
        self.mode = BertVITS2_config.get("mode", "remote")
        if self.mode == "remote":
            self.host = BertVITS2_config.get("host", None)
            self.secret = BertVITS2_config.get("secret", None)
            if not self.host:
                raise ValueError("Bert-VITS2 host is not set! Please check your 'config.json' file.")
            self.checkConnection()
        else:
            # 暂未进行本地运行Bert-VITS2的开发(本地运行的话直接部署Bert-VITS2就好了，不需要这套框架)
            raise NotImplementedError("Bert-VITS2 local mode is not implemented yet!")

    def synthesize(self, text) -> str:
        """
        语音合成

        该方法调用远端Bert-VITS2的模型，将文本转换为语音。
        :param text: str 待合成的文本
        :return: tuple[int, np.array] 语音数据，分别为采样率和以np.array形式存储的采样数据
        """
        try:
            response = requests.post(
                url=urljoin(self.host, 'synthesize'),
                params={"secret": self.secret},
                json={"text": text, "speaker": self.voice},
                timeout=int(len(text) * 0.6)
            )
            data = response.json()
            sampleRate = data['sampling_rate']
            audioData = data['raw']
            audioData = np.array(audioData, dtype=np.int16)
            wavwrite(os.path.join(self.savePath, "synthesize.wav"), sampleRate, audioData)
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Connection to {self.model} timed out, please check your network status.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Connection to {self.model} failed, please check your host and secret.")
        return os.path.join(self.savePath, "synthesize.wav").replace('\\', '/')

    def checkConnection(self):
        """
        检查与远端Bert-VITS2的连接状态
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
            print("Bert-VITS2 remote mode connection check finished.")


class FastSpeech(TTSBase):
    """
    调用远端FastSpeech模型进行语音合成

    目标项目来自：https://github.com/ming024/FastSpeech2
    """

    def __init__(self, FastSpeech_config: dict):
        super().__init__(TTSEnum.FastSpeech_Finetune, FastSpeech_config.get("model", "FastSpeech"), "default")
        self.host, self.secret = None, None
        self.mode = FastSpeech_config.get("mode", "remote")
        if self.mode == "remote":
            self.host = FastSpeech_config.get("host", None)
            self.secret = FastSpeech_config.get("secret", None)
            if not self.host:
                raise ValueError("FastSpeech host is not set! Please check your 'config.json' file.")
            self.checkConnection()
        else:
            # 暂未进行本地运行FastSpeech的开发(本地运行的话直接部署FastSpeech就好了，不需要这套框架)
            raise NotImplementedError("FastSpeech local mode is not implemented yet!")

    def synthesize(self, text) -> str:
        """
        语音合成

        该方法调用远端FastSpeech的模型，将文本转换为语音。
        :param text: str 待合成的文本
        :return: str 合成后语音文件的绝对路径
        """
        try:
            response = requests.post(
                url=urljoin(self.host, 'synthesize'),
                params={"secret": self.secret},
                json={"text": text},
                timeout=20
            )
            fileData = response.content
            with open(os.path.join(self.savePath, "synthesize.wav"), "wb") as file:
                file.write(fileData)
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Connection to {self.model} timed out, please check your network status.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Connection to {self.model} failed, please check your host and secret.")
        return os.path.join(self.savePath, "synthesize.wav").replace('\\', '/')

    def checkConnection(self):
        """
        检查与远端FastSpeech的连接状态
        :return: bool 是否连接成功
        """
        try:
            request = requests.get(
                url=self.host,
                params={"secret": self.secret},
                timeout=10
            )
            if not request.status_code == 200:
                raise ConnectionError(f"Connection to {self.model} failed, please check your host and secret.")
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Connection to {self.model} timed out, please check your network status.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Connection to {self.model} failed, please check your host and secret.")
        finally:
            print("FastSpeech remote mode connection check finished.")


class OpenAITTS(TTSBase):
    """
    调用OpenAI的TTS模型进行语音合成

    API文档参考：https://platform.openai.com/docs/guides/text-to-speech?lang=python
    """

    def __init__(self, OpenAI_config: dict):
        from openai import OpenAI
        super().__init__(TTSEnum.OpenAI_TTS, OpenAI_config.get("tts_model", "tts-1"),
                         OpenAI_config.get("tts_voice", "nova"))
        self.api_key = OpenAI_config.get("api_key", None)
        if not self.api_key:
            raise ValueError("OpenAI api_key is not set! Please check your 'config.json' file.")
        self.voice = OpenAI_config.get("tts_voice", "nova")
        self.host = OpenAI(api_key=self.api_key)

    def synthesize(self, text) -> str:
        """
        语音合成

        该方法调用OpenAI的语音合成API，将文本转换为语音。
        :param text: str 待合成的文本
        :return: str 合成后语音文件的绝对路径
        """
        filePath = os.path.join(self.savePath, "synthesize.wav").replace('\\', '/')
        try:
            synthesize = self.host.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=text
            )
            synthesize.stream_to_file(filePath)
        except Exception as e:
            raise e
        return filePath

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
                raise ConnectionError(f"Connection to {self.model} failed, please check your host and secret.")
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Connection to {self.model} timed out, please check your network status.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Connection to {self.model} failed, please check your host and secret.")
        finally:
            print("OpenAI connection check finished.")


class BaiduTTS(TTSBase):
    """
    调用百度的TTS模型进行语音合成

    API文档参考：https://ai.baidu.com/ai-doc/SPEECH/mlbxh7xie
    """

    voice_dict = {
        "度小美": 0, "度小宇": 1, "度逍遥（基础）": 3, "度丫丫": 4, "度小娇": 5, "度米朵": 103, "度博文": 106,
        "度小童": 110, "度小萌": 111, "度逍遥（精品）": 5003, "度小鹿": 5118,
    }  # 详见：https://ai.baidu.com/ai-doc/SPEECH/mlbxh7xie “请求方式和参数”中“per”参数一栏

    def __init__(self, Baidu_config: dict):
        super().__init__(TTSEnum.Baidu_TTS, Baidu_config.get("tts_model", "Baidu-TTS"),
                         Baidu_config.get("tts_voice", "度小美"))
        self.api_key = Baidu_config.get("api_key", None)
        self.secret_key = Baidu_config.get("secret_key", None)
        self.access_token = Baidu_config.get("access_token", None)
        if not self.api_key or not self.secret_key:
            raise ValueError("Baidu TTS api_key or secret_key is not set! Please check your 'config.json' file.")
        self.host = "https://tsn.baidu.com/text2audio"
        if not self.access_token:
            self.OAuth()

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
            },
            timeout=10
        )
        access_token = response.json().get("access_token")
        Configs["Baidu"]["tts"]["access_token"] = access_token
        self.access_token = access_token
        return access_token

    def synthesize(self, text: str) -> str:
        """
        语音合成

        该方法调用百度的语音合成API，将文本转换为语音。
        :param text: str 待合成的文本
        :return: str 合成
        """
        params = {'tok': self.access_token, 'tex': text, 'cuid': getMacAddress(),
                  'lan': 'zh', 'ctp': 1, 'per': self.voice_dict[self.voice]}  # 相关参数
        try:
            response = requests.post(
                url="https://tsn.baidu.com/text2audio",
                headers={'Content-Type': 'application/x-www-form-urlencoded', 'Accept': '*/*'},
                data=urlencode(params).encode()
            )
            if not response.status_code == 200:
                raise ConnectionError(f"Connection to {self.model} failed, please check your host and secret.")
            if 'content-type' not in response.headers.keys() or response.headers['content-type'].find('audio/') < 0:
                raise ValueError("TTS API Error: " + response.text)
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Connection to {self.model} timed out, please check your network status.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Connection to {self.model} failed, please check your host and secret.")
        with open(os.path.join(self.savePath, "synthesize.mp3"), "wb") as file:
            file.write(response.content)
        return os.path.join(self.savePath, "synthesize.mp3").replace('\\', '/')

    def checkConnection(self):  # TODO: 设计检查连接的方法
        pass


if __name__ == '__main__':
    raise NotImplementedError("This module is not runnable!")
