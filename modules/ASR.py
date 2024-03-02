"""该文件定义了语音识别的后端类"""
import os
from abc import abstractmethod
from os import PathLike
from typing import Union
from urllib.parse import urljoin

import requests
from scipy.io.wavfile import read as wavread

from modules.utils import ASREnum


class ASRBase:
    """语音识别后端基类，建议在进行语音识别后端开发时继承该类"""

    def __init__(self, asrType: ASREnum, model: str):
        self.type = asrType  # 语音识别类型
        self.model = model  # 语音识别模型

    @abstractmethod
    def transcribe(self, audio: Union[tuple, PathLike]) -> str:
        """
        语音识别

        该方法将调用实际的语音识别模型，将语音转换为文本，具体参数详见子类。
        :param audio: 语音数据，可能为tuple[int, np.array]或PathLike，具体类型详见子类
        """
        pass

    @staticmethod
    def getAllASRModels():
        """
        返回当前支持的全部语音识别模型
        :return dict[ASRBase: list[str]] 语音识别模型字典，key为类，value为该类支持的全部模型列表
        """
        return {WhisperAPI: ['whisper-1'],
                Whisper: ['whisper-tiny', 'whisper-base', 'whisper-small', 'whisper-tiny-finetune',
                          'whisper-base-finetune']}


class Whisper(ASRBase):
    """
    调用远端Whisper-Finetune模型进行语音识别

    目标项目来自：https://github.com/yeyupiaoling/Whisper-Finetune
    """

    def __init__(self, Whisper_config: dict):
        super().__init__(ASREnum.Whisper_Finetune, Whisper_config.get("model", "Whiper-Finetune"))
        self.host, self.secret = None, None
        self.mode = Whisper_config.get("mode", "remote")
        if self.mode == "remote":
            self.host = Whisper_config.get("host", None)
            self.secret = Whisper_config.get("secret", None)
            if not self.host:
                raise ValueError("Whisper host is not set! Please check your 'config.json' file.")
            self.checkConnection()
        else:
            # 暂未进行本地运行Whisper的开发(本地运行的话直接部署Whisper-Finetune就好了，不需要这套框架)
            raise NotImplementedError("Whisper local mode is not implemented yet!")

    def transcribe(self, audio: PathLike) -> str:
        """
        语音识别

        该方法调用远端Whisper-Finetune的模型，将语音文件转换为文本。
        :param audio: PathLink 语音文件路径
        :return: str 识别结果
        """
        sampleRate, raw = wavread(audio)
        raw = raw.tolist()
        try:
            response = requests.post(
                url=urljoin(self.host, 'transcribe'),
                params={"secret": self.secret},
                json={"sampling_rate": sampleRate, "raw": raw},
                timeout=20
            )
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Connection to {self.model} timed out, please check your network status.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Connection to {self.model} failed, please check your host and secret.")
        return response.json().get("content", "")

    def checkConnection(self):
        """
        检查与远端Whisper的连接状态
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
            print("Whisper remote mode connection check finished.")


class WhisperAPI(ASRBase):
    """
    通过API调用Whisper进行语音识别

    API文档参考：https://platform.openai.com/docs/guides/speech-to-text?lang=python
    """

    def __init__(self, OpenAI_config: dict):
        from openai import OpenAI
        super().__init__(ASREnum.WhisperAPI, OpenAI_config.get("asr_model", "whisper-1"))
        self.api_key = OpenAI_config.get("api_key", None)
        if not self.api_key:
            raise ValueError("OpenAI api_key is not set! Please check your 'config.json' file.")
        self.host = OpenAI(api_key=self.api_key)

    def transcribe(self, audio: PathLike) -> str:
        """
        语音识别

        该方法调用OpenAI的语音识别API，将语音文件转换为文本。
        :param audio: PathLike 语音文件路径
        :return: str 识别结果
        """
        if not os.path.exists(audio):
            raise FileNotFoundError("Audio file not found!")
        audioFile = open(audio, "rb")
        try:
            transcript = self.host.audio.transcriptions.create(
                model=self.model,
                file=audioFile,
                response_format="text"
            )
            return str(transcript)
        except Exception as e:
            raise e

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


class BaiduASR(ASRBase):
    """
    通过百度API调用百度语音识别进行语音识别

    API文档参考：https://ai.baidu.com/ai-doc/SPEECH/0lbxfnc9b
    注：由于使用了百度SDK(baidu-aip)，因此不需要手动进行OAuth2.0认证
    """

    def __init__(self, Baidu_config: dict):
        from aip import AipSpeech
        super().__init__(ASREnum.Baidu_ASR, Baidu_config.get("asr_model", "baidu-1"))
        self.app_id = Baidu_config.get("app_id", None)
        self.api_key = Baidu_config.get("api_key", None)
        self.secret_key = Baidu_config.get("secret_key", None)
        if not self.app_id or not self.api_key or not self.secret_key:
            raise ValueError("Baidu app_id, api_key or secret_key is not set! Please check your 'config.json' file.")
        self.host = AipSpeech(self.app_id, self.api_key, self.secret_key)

    def transcribe(self, audio: PathLike) -> str:
        """
        语音识别

        该方法调用百度的语音识别API，将语音文件转换为文本。
        :param audio: PathLike 语音文件路径
        :return: str 识别结果
        """
        if not os.path.exists(audio):
            raise FileNotFoundError("Audio file not found!")
        with open(audio, "rb") as file:
            audioFile = file.read()
        try:
            responseDict = self.host.asr(audioFile, options={"dev_pid": 1537})
            return responseDict.get("result", [""])[0]
        except Exception as e:
            raise e


if __name__ == '__main__':
    raise NotImplementedError("This module is not runnable!")
