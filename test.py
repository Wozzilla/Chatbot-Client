import random
import gradio as gr


def alternatingly_agree(message, history):
    """
    This function will be called whenever the user submits a message.
    :param message:
    :param history:
    :return:
    """
    if len(history) % 2 == 0:
        return f"Yes, I do think that '{message}'"
    else:
        return "I don't think so"


gr.ChatInterface(
    fn=alternatingly_agree,
    title="云·原神",
    description="云·原神 description",
    css="./assets/css/GenshinChat.css",
    js="./assets/js/GenshinChat.js",
    submit_btn="发送"
).launch()
