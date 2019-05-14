import time
import threading
from wxpy import *
import requests
import pymongo
import os
from baidu_ocr import BaiDuOcr
from faker import Faker
import email_test
from lxml.html import fromstring
import logging
import yaml
import logging.config
from setting import *
from datetime import datetime, timedelta



class GzhMessage:
    """监听微信公众号消息"""
    def __init__(self):
        # 初始化wxpy Bot对象
        self.qr_flag = False
        self.start_time = time.time()
        self.bot = Bot(cache_path=True, qr_callback=self.qr_callback)
        self.bot.enable_puid('wxpy_puid.pkl')
        # 连接数据库
        self.client = pymongo.MongoClient(host='127.0.0.1')
        self.col = self.client['D88']['gzh_message']
        # 自定义请求头
        self.headers = {
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': Faker().user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        # 信息接收群
        self.informer1 = self.bot.groups().search('洗稿')
        # 信息接收人
        self.informer2 = self.bot.friends().search('noodles')
        # 测试小号
        self.test_user = self.bot.friends().search('max')
        # 关键词
        self.keywords = KEYWORDS
        # 加载日记配置文件
        self.logger = self.setup_logging()

    def qr_callback(self, **kwargs):
        """获取二维码后将其写入文件再通过邮件发送到登录账号"""
        send_time = time.time()
        if not self.qr_flag:
            qr_path = 'QR.png'
            with open(qr_path, 'wb') as fp:
                fp.write(kwargs['qrcode'])
            email_test.send_qr('QR.png')
            self.qr_flag = True
        if send_time - self.start_time > 300:
            self.start_time = time.time()
            self.qr_flag = False

    def setup_logging(self, default_path='yaml.ini', default_level=logging.INFO):
        """
        初始化日记对象
        :param default_path: logging配置文件，采用yaml格式
        :param default_level: logging默认等级
        :return: logger对象
        """
        path = default_path
        # 如果日记配置文件存在，则加载配置，不存在则配置一个基础logging
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                # 读取yaml配置文件
                config = yaml.full_load(f)
                logging.config.dictConfig(config)
        else:
            logging.basicConfig(level=default_level)
        # 使用日记子类'main.core'
        logger = logging.getLogger('main.core')
        # 创建一个微信日志处理器
        wechat_handler = WeChatLoggingHandler(receiver=self.bot)
        wechat_handler.level = 'ERROR'
        logger.addHandler(wechat_handler)
        return logger

    def get_info(self, url):
        """
        处理公众号文章，检测是否含关键词
        :param url: 公众号文章url
        :return: 处理状态码，文章信息
        """
        # 使用request获取网页内容
        response = requests.get(url, headers=self.headers, timeout=10)
        html = fromstring(response.text)
        # 匹配文字
        long_text = html.xpath('//div[@id="js_content"]//span//text()')
        # 匹配url连接
        img_urls = html.xpath('//div[@id="js_content"]//img/@data-src')
        # 将匹配的文章连接成长文本
        long_text = ''.join(long_text)

        # 判断文章文本中有活动关键字存在，有则直接返回状态码和关键词信息
        for keyword in self.keywords:
            if keyword in long_text:
                text = f'文章"文本"含有关键词, 关键词为"{keyword}"'
                return 200, text

        # 若没有关键字，调用百度通用文字ocr接口下载图片并识别
        # print(f'无关键字，开始请求图片,共{len(img_urls)}张')
        # 若图片识别结果中有活动关键字，返回status=200, pic_text='文章第{i}张"图片"含有关键词, 关键词为{j}
        # 若图片识别结果无活动，返回status=500, None
        # 若接口出错，返回status=400, pic_text=traceback.format_exc()
        if len(img_urls):
            status, pic_text = BaiDuOcr().pic_ocr(img_urls)
            self.logger.debug(f'无关键字，开始请求图片,共{len(img_urls)}张')
            if status == 200:
                return status, pic_text
            elif status == 500:
                return status, pic_text
            elif status == 400:
                return status, pic_text
        # 若文章没有关键词和图片，返回500和文章信息
        else:
            no_text = '该文章不存在关键词且没有图片，没有活动'
            return 500, no_text

    def send_informer(self, informer, msg):
        """
        向信息接受人发送文章信息，存在接受人但是接收不了或者发送失败记录错误
        如果找不到联系人，则发送一个警告信息
        :param informer: 信息接受人
        :param msg: 文章信息
        """
        if len(informer):
            try:
                ensure_one(informer).send(str(msg))
                self.logger.debug(f'信息成功向"{informer}"发送成功')
            except ResponseError:
                self.logger.exception(f'发送失败或者接收人"{informer}"无法接收信息')
        else:
            self.logger.warning(f'找不到"{informer}"信息接收人!')

    def run(self):
        # 注册公众号消息
        @self.bot.register(chats=[MP], run_async=True)
        def gzh_msg(msg):
            # 获取公众号一次发送的所有消息条目
            articles = msg.articles
            if articles is not None:
                # 逐条操作
                for article in articles:
                    dic = dict()
                    # 获取公众号名字
                    dic['name'] = msg.sender.name
                    # 获取文章标题
                    dic['title'] = article.title
                    # 获取文章简介
                    dic['summary'] = article.summary
                    # 获取文章Url
                    dic['url'] = article.url
                    # 获取创建时间
                    dic['create_time'] = msg.create_time.strftime('%Y-%m-%d %H:%M:%S')
                    # 输出文章字典信息
                    self.logger.debug(str(dic))
                    try:
                        # 检测文章标题是否含有关键词
                        if any([keyword in dic['title'] for keyword in self.keywords]):
                            dic['factor'] = f'文章"标题"含有关键词'
                            # 输出有效信息
                            self.logger.info(str(dic))
                            # 向接受群发送信息
                            self.send_informer(self.informer1, dic)
                            # 向接受人发送信息
                            self.send_informer(self.informer2, dic)
                            # 插入mongo数据库
                            self.col.update_one({'url': dic['url']}, {'$set': dic}, True)
                            continue
                        # 将url传入检测函数
                        status, text = self.get_info(dic['url'])
                        # 如果status返回值为200，表示公众号文章含有活动关键字
                        if status == 200:
                            dic['factor'] = text
                            # 向信息接收人发送消息
                            self.logger.info(str(dic))
                            self.send_informer(self.informer1, dic)
                            self.send_informer(self.informer2, dic)
                            self.col.update_one({'url': dic['url']}, {'$set': dic}, True)
                        # status返回值为400，则百度云接口出错
                        elif status == 400:
                            dic['Warning'] = '百度云文字识别模块错误'
                            dic['Error'] = text
                            self.bot.file_helper.send(dic)
                            self.logger.error(str(dic))
                        # status返回值为500，则文章没有活动
                        elif status == 500:
                            self.logger.debug(f'{dic["title"]},text')
                    except Exception as e:
                        # 日记输出错误
                        self.logger.exception(dic['create_time'])

        # 监听测试小号的消息
        @self.bot.register(chats=[Friend])
        def cs_msg(msg):
            if self.test_user is not []:
                test_user = self.test_user[0]
                if msg.sender.puid == test_user.puid:
                    self.logger.debug(msg)
                    dic = dict()
                    url = msg.text
                    dic['url'] = url
                    try:
                        # 将url传入检测关键字函数
                        status, text = self.get_info(dic['url'])
                        # 如果status返回值为200，表示公众号文章含有活动关键字
                        if status == 200:
                            self.logger.info(str(dic))
                            self.bot.file_helper.send(dic)
                        # status返回值为400，则百度云接口出错
                        elif status == 400:
                            dic['Error'] = '百度云文字识别模块错误'
                            self.logger.error(str(dic))
                            self.bot.file_helper.send(dic)
                        # status返回值为500，则文章没有活动
                        elif status == 500:
                            self.logger.debug(text)
                    except Exception as e:
                        # 日记输出错误
                        self.logger.exception(dic['create_time'])

        # 阻塞线程
        embed()


if __name__ == '__main__':
    gzh = GzhMessage()
    gzh.run()
    # t1 = threading.Thread(target=gzh.run)
    # t1.start()

    listen_thread = None
    for i in threading.enumerate():
        if i.name == '_listen':
            listen_thread = i

    while True:
        if not listen_thread.is_alive():
            content = f'公众号监听线程死亡'
            email_test.error_alarm(content)
            break
        time.sleep(60)





