"""此文件以Bert-VITS2为例，展示了如何将一个AI模型包装为API，并允许远程调用"""
import os

from flask import request, abort, jsonify

from APIWrapper import APIWrapper
from webui import format_utils, tts_fn
from config import config
import utils
from infer import latest_version, get_net_g

param = {
    'sdp_ratio': 0.5,
    'noise_scale': 0.6,
    'noise_scale_w': 0.9,
    'length_scale': 1.1,
    'language': 'mix',  # 注意此时应当将输入文本重新组织
    'reference_audio': None,
    'emotion': 'Happy',
    'prompt_mode': 'Text prompt',
    'style_text': '',
    'style_weight': 0.7
}


if __name__ == "__main__":
    device = "cpu"
    if device == "mps":
        os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
    api_app = APIWrapper()
    hps = utils.get_hparams_from_file(config.webui_config.config_path)
    version = hps.version if hasattr(hps, "version") else latest_version
    net_g = get_net_g(
        model_path=config.webui_config.model, version=version, device=device, hps=hps
    )


    @api_app.addRoute('/synthesize', methods=['POST'])  # 定义一个路由，用于处理文字转语音任务(不带历史记录)
    def synthesize():
        """
        将文本转换为音频文件，并发送
        """
        secret = request.values.get("secret", None)
        data = request.get_json()
        text = data.get("text", None)
        speaker = data.get("speaker", '刻晴')
        if text is None:
            abort(400)
        _, text = format_utils(text, speaker)  # 组织后的文本内容
        _, audio = tts_fn(text, speaker, **param)  # 生成音频
        sampleRate, audio = audio
        audio = audio.tolist()
        return jsonify({"sampling_rate": sampleRate, "raw": audio})


    api_app.run()