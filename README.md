# Chatbot Client

> 本项目为[Wozzilla](https://github.com/orgs/Wozzilla)的Chatbot项目的客户端，WebUI基于[Gradio](https://www.gradio.app/)搭建，分布式部署与网络通讯基于[Flask](https://github.com/pallets/flask)和[Requests](https://requests.readthedocs.io/en/latest)实现

## 效果展示

![display1.png](display1.png)
![display2.png](display2.png)

## 使用方法

* 本项目为客户端，推理端(服务端)既可以自行部署(详见下文)，亦可以选择调用现有的公开API服务
* 请注意，应首先启动推理端服务，再启动前端界面进程，允许前端界面和若干推理端服务在不同服务器中运行，但请确保不同服务器之间可以通过网络通讯。

## 公开API适配情况

* ASR：
  * [x] [Whisper - OpenAI](https://platform.openai.com/docs/guides/speech-to-text)
  * [x] [ASR - 百度智能云](https://cloud.baidu.com/doc/SPEECH/s/qlcirqhz0)
* NLG：
  * [x] [GPT - OpenAI](https://platform.openai.com/docs/guides/text-generation)
  * [x] [ERNIE-Bot(文心一言) - 百度千帆](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/flfmc9do2)
  * [ ] [通义千问 - 阿里云]()
* TTS：
  * [x] [TTS - OpenAI](https://platform.openai.com/docs/guides/text-to-speech)
  * [x] [TTS - 百度智能云](https://cloud.baidu.com/doc/SPEECH/s/mlciskuqn)

### 客户端

> 请确保已安装ffplay并配置好环境变量，否则将无法自动播放语音。

1. 克隆仓库：`git clone https://github.com/Wozzilla/Chatbot-Client.git`
2. 安装依赖：`pip install -r requirements.txt`
3. 配置相关信息(所有配置文件均在`config.json`中)
4. 通过`python -u gradio-app.py`启动客户端。

### 推理端 ChatGLM3

1. 克隆仓库：`git clone https://github.com/Wozzilla/ChatGLM3.git`
2. 安装该仓库的依赖：`pip install -r requirements.txt`
3. 通过`python -u nlg_server.py`启动服务。

### 推理端 Whisper

1. 克隆仓库：`git clone https://github.com/Wozzilla/Whisper.git`
2. 安装该仓库的依赖：`pip install -r requirements.txt`
3. 通过`python -u tts_server.py`启动服务。

### 推理端 Bert-VITS2

1. 克隆仓库：`git clone https://github.com/Wozzilla/Bert-VITS2.git`
2. 安装该仓库的依赖：`pip install -r requirements.txt`
3. 通过`python -u tts_server.py`启动服务。

## TODO 改进计划

* [ ] 继续完善前端界面
* [ ] 将默认NLG效果改为流式显示

## Co-Authors

<a href="https://github.com/Aut0matas">
<img src="https://avatars.githubusercontent.com/u/43371529?v=4" alt="Aut0matas"
style="width: 48px; height: 48px; border-radius: 24px; border-width:2px; border-color: white;">
</a>
<a href="https://github.com/ShirokaneShizuku">
<img src="https://avatars.githubusercontent.com/u/102428923?v=4"  alt="ShirokaneShizuku"
style="width: 48px; height: 48px; border-radius: 24px; border-width:2px; border-color: white;">
</a>
<a href="https://github.com/YukiShionji">
<img src="https://avatars.githubusercontent.com/u/80265989?v=4"  alt="YukiShionji" 
style="width: 48px; height: 48px; border-radius: 24px; border-width:2px; border-color: white;">
</a>
<a href="https://github.com/wanlan5201314">
<img src="https://avatars.githubusercontent.com/u/112745268?v=4" alt="wanlan5201314"
style="width: 48px; height: 48px; border-radius: 24px; border-width:2px; border-color: white;">
</a>
<a href="https://github.com/Steven-Zhl">
<img src="https://avatars.githubusercontent.com/u/80385790?v=4" alt="Steven-Zhl"
style="width: 48px; height: 48px; border-radius: 24px; border-width:2px; border-color: white;">
</a>
