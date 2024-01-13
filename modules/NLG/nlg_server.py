"""此文件以ChatGLM为例，展示了如何将一个AI模型包装为API，并允许远程调用"""
from APIWrapper import APIWrapper
from transformers import AutoTokenizer, AutoModel
from flask import request

if __name__ == "__main__":
    api_app = APIWrapper()  # 创建一个api_app对象
    tokenizer = AutoTokenizer.from_pretrained("THUDM/chatglm3-6b", trust_remote_code=True)  # 创建tokenizer
    model = AutoModel.from_pretrained("THUDM/chatglm3-6b", trust_remote_code=True, device='cuda')  # 创建model
    model = model.eval()


    @api_app.addRoute('/singleQuery', methods=['POST'])  # 定义一个路由，用于处理单次聊天(不带历史记录)
    def singleQuery():
        """
        处理单次查询时的请求
        """
        secret = request.values.get('secret')  # 暂且不使用secret
        data = request.get_json()
        prompt, message = list(data.get("prompt", "")), data.get("message", "")
        response, _ = model.textChat(tokenizer, message, history=prompt)
        return {"time": api_app.getISOTime(), "content": response}, 200


    @api_app.addRoute('/continuedQuery', methods=['POST'])  # 定义一个路由，用于处理带有历史记录的聊天
    def continuedQuery():
        """
        处理带有历史记录的查询时的请求
        """
        secret = request.values.get('secret')  # 暂且不使用secret
        data = request.get_json()
        history, message = data.get("history", []), data.get("message", "")
        response, _ = model.textChat(tokenizer, message, history=history)
        return {"time": api_app.getISOTime(), "content": response}, 200


    api_app.run()
