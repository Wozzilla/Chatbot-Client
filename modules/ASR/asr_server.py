"""此文件将本地Whisper模型包装成可远程调用的API"""
from APIWrapper import APIWrapper
from transformers import pipeline
from flask import request
import numpy as np

if __name__ == "__main__":
    api_app = APIWrapper()  # 创建一个api_app对象
    transcriber = pipeline("automatic-speech-recognition", model="models/whisper-tiny-finetune")


    @api_app.addRoute('/transcribe', methods=['POST'])  # 定义一个路由，用于处理语音识别任务
    def transcribe(self):
        """
        处理语音识别任务
        """
        secret = request.values.get('secret')  # 暂且不使用secret
        audio = request.get_json()
        sr = audio.get("sampling_rate", 48000)  # 采样率，默认为48kHz
        y = audio.get("raw")  # 为保证数据传输时的稳定性，这里使用Python原生的数据类型(list)进行传输
        if not y:
            return {"time": api_app.getISOTime(), "content": "No audio data received!"}, 400
        y = np.array(y)  # 将list的数据重新转换为np.array
        y = y.astype(np.float32)
        y /= np.max(np.abs(y))
        result = self.transcriber({"sampling_rate": sr, "raw": y})["text"]
        return {"time": api_app.getISOTime(), "content": result}, 200
