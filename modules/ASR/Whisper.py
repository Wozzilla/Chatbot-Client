"""该文件声明一个Whisper类，用于调用Whisper-Finetune模型进行问答"""
import requests
from urllib.parse import urljoin

from modules.utils import ASREnum


class Whisper:
    """
    调用Whisper-Finetune模型进行语音识别
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
            raise NotImplementedError("Whisper local mode is not implemented yet!")

    def checkConnection(self):
        """
        检查与远端Whisper的连接状态
        :return: bool 是否连接成功
        """
        try:
            request = requests.get(url=self.host, params={"secret": self.secret}, timeout=5)
            return request.status_code == 200
        except requests.exceptions.Timeout:
            raise TimeoutError("Connection to Whisper timed out, please check your network status.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Connection to Whisper failed, please check your host and secret.")
        finally:
            print("Whisper remote mode connection check finished.")

    def asr(self, audioData: tuple) -> str:
        """
        语音识别

        该方法调用OpenAI的语音识别API，将语音文件转换为文本。
        :param audioData: tuple[int, np.array] 语音数据，分别为采样率和以np.array形式存储的采样数据
        :return: str 识别结果
        """
        # TODO: 待测试
        sampleRate, audio = audioData
        audio = audio.tolist()
        response = requests.post(
            url=urljoin(self.host, 'asr'),
            params={"secret": self.secret},
            json={"sampling_rate": sampleRate, "raw": audio}
        )
        return response.json().get("content", "")
