"""该文件尝试调用OpenAI Whisper API，在进行前端调试时作为后端使用"""
from openai import OpenAI
from modules.utils import ASREnum


class WhisperAPI:
    """
    通过API调用Whisper进行语音识别

    API文档参考：https://platform.openai.com/docs/guides/speech-to-text?lang=python
    """

    def __init__(self, OpenAI_config: dict):
        self.api_key = OpenAI_config.get("api_key", None)
        self.botType = ASREnum.WHISPER
        self.prompt = None  # 暂时先不启用prompt
        self.model = OpenAI_config.get("asr_model", "whisper-1")
        if not self.api_key:
            raise ValueError("OpenAI api_key is not set! Please check your 'config.json' file.")
        self.client = OpenAI(api_key=self.api_key)

    def asr(self, audioPath) -> str:
        """
        语音识别

        该方法调用OpenAI的语音识别API，将语音文件转换为文本。
        :param audioPath: str 语音文件路径
        :return: str 识别结果
        """
        audioFile = open(audioPath, "rb")
        transcript = self.client.audio.transcriptions.create(
            model=self.model,
            file=audioFile,
            response_format="text"
        )
        return transcript
