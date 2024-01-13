"""此文件以ChatGLM为例，展示了如何将一个AI模型包装为API，并允许远程调用"""
from APIWrapper import APIWrapper
from flask import request, send_file, abort
import re
import argparse
from string import punctuation
from types import SimpleNamespace
from synthesize import preprocess_mandarin, synthesize
import torch
import yaml
import numpy as np
from torch.utils.data import DataLoader
from g2p_en import G2p
from pypinyin import pinyin, Style
from utils.model import get_model, get_vocoder
from utils.tools import to_device, synth_samples
from dataset import TextDataset
from text import text_to_sequence

if __name__ == "__main__":
    api_app = APIWrapper()  # 创建一个api_app对象
    args = {
        'restore_step': 600000,
        'mode': 'single',
        'source': None,
        'text': None,
        'speaker_id': 44,
        'preprocess_config': 'config/AISHELL3/preprocess.yaml',
        'model_config': 'config/AISHELL3/model.yaml',
        'train_config': 'config/AISHELL3/train.yaml',
        'pitch_control': 1.0,
        'energy_control': 1.0,
        'duration_control': 1.0
    }
    device = "cpu"


    @api_app.addRoute('/transcribe', methods=['POST'])  # 定义一个路由，用于处理单次聊天(不带历史记录)
    def transcribe():
        """
        将文本转换为音频文件，并发送
        """
        secret = request.values.get("secret", None)
        data = request.get_json()
        text = data.get("text", None)
        if text is None:
            abort(400)
        global args
        args["text"] = text
        args = SimpleNamespace(**args)

        # 以下执行部分拷贝自synthesize.py

        # Check source texts
        if args.mode == "batch":
            assert args.source is not None and args.text is None
        if args.mode == "single":
            assert args.source is None and args.text is not None

        # Read Config
        preprocess_config = yaml.load(
            open(args.preprocess_config, "r"), Loader=yaml.FullLoader
        )
        model_config = yaml.load(open(args.model_config, "r"), Loader=yaml.FullLoader)
        train_config = yaml.load(open(args.train_config, "r"), Loader=yaml.FullLoader)
        configs = (preprocess_config, model_config, train_config)

        # Get model
        model = get_model(args, configs, device, train=False)

        # Load vocoder
        vocoder = get_vocoder(model_config, device)

        # Preprocess texts
        if args.mode == "batch":
            # Get dataset
            dataset = TextDataset(args.source, preprocess_config)
            batchs = DataLoader(
                dataset,
                batch_size=8,
                collate_fn=dataset.collate_fn,
            )
        if args.mode == "single":
            ids = raw_texts = [args.text[:100]]
            speakers = np.array([args.speaker_id])
            texts = np.array([preprocess_mandarin(args.text, preprocess_config)])
            text_lens = np.array([len(texts[0])])
            batchs = [(ids, raw_texts, speakers, texts, text_lens, max(text_lens))]

        control_values = args.pitch_control, args.energy_control, args.duration_control

        synthesize(model, args.restore_step, configs, vocoder, batchs, control_values)
        file = open('output/result/AISHELL3/output.wav', 'rb')
        return send_file(file, mimetype="audio/wav")


    api_app.run()
