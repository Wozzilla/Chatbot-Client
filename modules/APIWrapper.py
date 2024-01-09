from abc import abstractmethod

from flask import Flask, request, make_response
import warnings


class APIWrapper:
    """
    使用Flask将后端封装为API形式，以实现远程调用

    若需要启用secret，请以Get参数(secret=...)的形式携带
    """
    defaultDescription = {
        "title": "It's a simple API.",
        "content":
            [
                "This is a developing and temporary “API wrapper” based on Flask.",
                "This class will allow you to wrap Python code as an API for simple server setup",
                "This class was originally used in the 'YNU-IST Project Hatbot' project to solve the problem of not being able to run all models on a single computer",
                "If you like it, you can star our chatbot project in <https://github.com/YNU-IST-Project-Chatbot/Chatbot>"
            ],
        "author": "Steven-Zhl"
    }

    def __init__(
            self,
            secretKey: str = None,
            description: dict = None,
            port: int = 5000,
            returnType: str = "json",
            version: str = "1.0-alpha",
            listen: bool = True
    ):
        """
        初始化APIWrapper
        :param secretKey: 加密密钥，建议设置。
        :param description: 关于本API的描述，可以使用str(简单的一段文字描述)或dict(多字段描述)进行配置
        :param port: Flask实例监听的端口
        :param version: 设定版本，默认为"1.0-alpha"，表示当前API只是个最初的内部测试版
        :param listen: 是否监听0.0.0.0，默认开启，监听后可以通过局域网IP访问，否则只能通过127.0.0.1访问
        """
        self.description = description if description else self.defaultDescription
        self.secretKey = secretKey if secretKey else None
        if not self.secretKey:
            warnings.warn("No valid secret set, your API is not secure!", RuntimeWarning)
        self.port = port
        self.returnType = returnType
        self.version = version
        self.host = "0.0.0.0" if listen else "127.0.0.1"

        global api_app
        api_app = Flask(__name__)  # 全局Flask实体
        self.basicRoute()  # 添加基本的路由规则

    def basicRoute(self):
        """
        初始化一些基础的地址路由
        :return: None
        """

        @api_app.route('/', methods=['GET'])
        def getDescription():
            if isinstance(self.description, dict):
                return self.description
            else:
                return {"description": ""}

        @api_app.route('/status', methods=['GET'])
        def getStatus():
            pass

        @api_app.route('/version', methods=['GET'])
        def getVersion():
            return {"version": "1.0-alpha"}

        @api_app.errorhandler(404)
        def error404(e):
            return {"status": 404,"content":"Unable to find the resource you requested."}, 404

    def run(self):
        api_app.run(host=self.host, port=self.port)


if __name__ == "__main__":
    apiEntity = APIWrapper()
    apiEntity.run()
