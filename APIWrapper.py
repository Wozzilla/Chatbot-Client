"""该文件定义了一个API封装类，可以将Python代码封装为API形式，以实现远程调用"""

import warnings
from datetime import datetime, timezone, timedelta

from flask import Flask
from werkzeug.exceptions import HTTPException


class APIWrapper:
    """
    使用Flask将任意后端封装为API形式，以实现远程调用

    若需要启用secret，请以Get参数(secret=...)的形式携带
    """
    # noinspection SqlNoDataSourceInspection
    defaultDescription = {
        "title": "It's a simple API.",
        "content": [
            [
                "这是一个基于Flask开发的API包装器，您可以利用它轻松地将您的Python代码包装为API，以服务器的形式运行（当然，前提是您的IP能否被访问）。",
                "这个类最初用于“YNU-IST Project Chatbot”项目，以解决单台计算机无法部署全部服务的需求。",
                "您可以在<https://github.com/Wozzilla/Chatbot-Client/wiki/APIWrapper>中查看详细用法。",
                "如果您喜欢，希望您能为我们的项目<https://github.com/Wozzilla/Chatbot-Client>点一个star！"
            ],
            [
                "This is an API wrapper developed based on Flask.",
                "With it, you can easily wrap your Python code as an API and run it as a server (provided, of course, that your IP can be accessed).",
                "This class was initially used in the 'YNU-IST Project Chatbot' project to address the need for deploying all services on a single computer.",
                "You can find detailed usage instructions at <https://github.com/Wozzilla/Chatbot-Client/wiki/APIWrapper>.",
                "If you find it helpful, we would appreciate it if you could give a star to our project at <https://github.com/Wozzilla/Chatbot-Client>."
            ]
        ],
        "author": "@Steven-Zhl",
        "Co-author": ["@Aut0matas", "@ShirokaneShizuku", "@YukiShionji", "@wanlan5201314"]
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
        self._addBasicRoute()  # 添加基本的路由规则
        self._addBasicErrorHandlers()  # 添加基本的错误处理

    def _addBasicRoute(self):
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

        # noinspection SqlNoDataSourceInspection
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

    def _addBasicErrorHandlers(self):
        @self.flaskApp.errorhandler(HTTPException)
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
