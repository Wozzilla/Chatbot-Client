# Chatbot

## 使用方法

> 请注意，应首先启动后端服务，再启动前端界面进程，允许前端界面和若干后端服务在不同服务器中运行，但请确保不同服务器之间可以通过网络通讯。

### 后端 ChatGLM3

1. 克隆仓库：`git clone https://github.com/YNU-IST-Project-Chatbot/ChatGLM3.git`
2. 安装该仓库的依赖：`pip install -r requirements.txt`
3. 通过`python -u nlg_server.py`启动服务

### 后端 Whisper-Finetune

### 后端 FastSpeech2

1. 克隆仓库：`git clone https://github.com/YNU-IST-Project-Chatbot/FastSpeech2.git`
2. 安装该仓库的依赖：`pip install -r requirements.txt`
3. 通过`python -u tts_server.py`启动服务

### 前端 gradio

1. 安装依赖：`pip install gradio requests --upgrade`，如需使用ChatGPT或Whisper请额外安装`pip install OpenAI --upgrade`
2. 配置相关信息(所有配置文件均在`config.json`中)
3. 启动界面：`python -u gradio-app.py`
4. Enjoy it!
