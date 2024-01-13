"""该文件定义了语音识别的后端类"""
import os
from abc import abstractmethod
from os import PathLike
from typing import Union
from urllib.parse import urljoin

import numpy as np
import requests
from openai import OpenAI
from modules.utils import ASREnum


class ASRBase:
    """语音识别后端基类，建议在进行语音识别后端开发时继承该类"""

    def __init__(self, asrType: ASREnum, model: str):
        self.asrType = asrType  # 语音识别类型
        self.model = model  # 语音识别模型

    @abstractmethod
    def transcribe(self, audio: Union[tuple, PathLike]) -> str:
        """
        语音识别

        该方法将调用实际的语音识别模型，将语音转换为文本，具体参数详见子类。
        :param audio: 语音数据，可能为tuple[int, np.array]或PathLike，具体类型详见子类
        """
        pass


class Whisper(ASRBase):
    """
    调用远端Whisper-Finetune模型进行语音识别

    目标项目来自：https://github.com/yeyupiaoling/Whisper-Finetune
    """

    def __init__(self, Whisper_config: dict):
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
        super().__init__(ASREnum.WHISPER, Whisper_config.get("model", "Whiper-Finetune"))

    def transcribe(self, audio: tuple[int, np.array]) -> str:
        """
        语音识别

        该方法调用远端Whisper-Finetune的模型，将语音文件转换为文本。
        :param audio: tuple[int, np.array] 语音数据，分别为采样率和以np.array形式存储的采样数据
        :return: str 识别结果
        """
        sampleRate, audio = audio
        audio = audio.tolist()
        try:
            response = requests.post(
                url=urljoin(self.host, 'transcribe'),
                params={"secret": self.secret},
                json={"sampling_rate": sampleRate, "raw": audio},
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
            return request.status_code == 200
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
        self.api_key = OpenAI_config.get("api_key", None)
        if not self.api_key:
            raise ValueError("OpenAI api_key is not set! Please check your 'config.json' file.")
        self.host = OpenAI(api_key=self.api_key)
        super().__init__(ASREnum.WHISPER, OpenAI_config.get("asr_model", "whisper-1"))

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
            return response.status_code == 200
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Connection to {self.model} timed out, please check your network status.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Connection to {self.model} failed, please check your host and secret.")
        finally:
            print("OpenAI connection check finished.")


if __name__ == '__main__':
    raise NotImplementedError("This module is not runnable!")
