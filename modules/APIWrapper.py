"""该文件定义了一个API封装类，可以将Python代码封装为API形式，以实现远程调用"""

import warnings
from datetime import datetime, timezone, timedelta

from flask import Flask


class APIWrapper:
    """
    使用Flask将后端封装为API形式，以实现远程调用

    若需要启用secret，请以Get参数(secret=...)的形式携带
    """
    defaultDescription = {
        "title": "It's a simple API.",
        "content": [
            "This is a developing and temporary “API wrapper” based on Flask.",
            "This class will allow you to wrap Python code as an API for simple server setup",
            "This class was originally used in the 'YNU-IST Project Chatbot' project to solve the problem of not "
            "being able to run all models on a single computer",
            "If you like it, you can star our chatbot project in <https://github.com/YNU-IST-Project-Chatbot/Chatbot>"
        ],
        "author": "Steven-Zhl"
    }

    def __init__(
            self,
            secretKey: str = None,
            description: dict = None,
            timeZone: int = 8,
            port: int = 5000,
            version: str = "1.0-alpha",
            listen: bool = True
    ):
        """
        初始化APIWrapper
        :param secretKey: 加密密钥，建议设置。
        :param description: 关于本API的描述，可以使用str(简单的一段文字描述)或dict(多字段描述)进行配置
        :param timeZone: 时区，作者所在的时区为UTC+8
        :param port: Flask实例监听的端口
        :param version: 设定版本，默认为"1.0-alpha"，表示当前API只是个最初的内部测试版
        :param listen: 是否监听0.0.0.0，默认开启，监听后可以通过局域网IP访问，否则只能通过127.0.0.1访问
        """
        self.description = description if description else self.defaultDescription
        self.secretKey = secretKey if secretKey else None
        self.timezone = timeZone
        if not self.secretKey:
            warnings.warn("No valid secret set, your API is not secure!", RuntimeWarning)
        self.port = port
        self.version = version
        self.host = "0.0.0.0" if listen else "127.0.0.1"

        self.flaskApp = Flask(__name__)
        self._basicRoute()  # 添加基本的路由规则

    def _basicRoute(self):
        """
        初始化一些基础的地址路由
        :return: None
        """

        @self.flaskApp.route('/', methods=['GET'])
        def getDescription():
            """
            返回关于本API的描述
            :return: {{time: str, content: dict}, 200}
            """
            if isinstance(self.description, dict):
                return {"time": self.getISOTime(), "content": self.description}, 200
            else:
                return {"time": self.getISOTime(), "content": self.description}, 200

        @self.flaskApp.route('/version', methods=['GET'])
        def getVersion():
            """
            返回API版本
            :return: {{time: str, version: str}, 200}
            """
            return {"time": self.getISOTime(), "version": self.version}, 200

        @self.flaskApp.route('/love', methods=['GET'])
        def love():
            """
            希望你们终能找到，爱的含义。
            :return: {{time: str, content: list[str]}, 200}
            """
            return {
                "time": self.getISOTime(),
                "content": [
                    "The need to find another human being to share one's life with, has always puzzled me.",
                    "Maybe because I'm so interesting all by myself.",
                    "With that being said, may you find as much happiness with each other as I find on my own."
                ]
            }, 200

        @self.flaskApp.errorhandler(Exception)
        def error(e):
            """
            各种网络异常处理
            :param e: InternalServerError
            :return: {{time: str, content: dict}, 404}
            """
            return {
                "time": self.getISOTime(),
                "content": {"code": e.code, "description": e.description, "name": e.name}
            }, e.code

    def run(self):
        """
        运行Flask实例，启动API服务
        :return: None
        """
        self.flaskApp.run(host=self.host, port=self.port)

    def getISOTime(self) -> str:
        """
        获取ISO格式的当前时间(服务器时间)
        :return: str ISO格式的当前时间(服务器时间)
        """
        return datetime.now(timezone(timedelta(hours=self.timezone))).strftime('%Y-%m-%dT%H:%M:%S%z')

    def addRoute(self, route: str, methods: list = None):
        """
        该方法用于添加路由，可以通过装饰器的形式添加路由，也可以直接调用该方法添加路由。
        :param route: str 路由地址
        :param methods: list 允许的请求方法
        :return: None
        """

        def decorator(func):
            """
            内部包装器
            :param func: function 被装饰的函数
            :return: function 被装饰的函数
            """
            self.flaskApp.add_url_rule(route, func.__name__, func, methods=methods)
            return func

        return decorator
