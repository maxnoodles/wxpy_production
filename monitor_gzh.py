#coding:utf-8
import time
import threading
import os

from wxpy import *
import requests
import pymongo
from faker import Faker
from lxml.html import fromstring
import logging
import yaml
import logging.config

import email_test
from setting import *
from baidu_ocr import BaiDuOcr
from until import regex_extract


class GzhMessage:
    """监听微信公众号消息"""
    def __init__(self):
        # 初始化wxpy Bot对象
        self.qr_flag = False
        self.start_time = time.time()
        self.bot = Bot(qr_callback=self.qr_callback)
        self.bot.enable_puid('wxpy_puid.pkl')
        # 连接数据库
        self.client = pymongo.MongoClient(host=MONGO_HOST,
                                          port=MONGO_PORT,
                                          # username=MONGO_USERNAME,
                                          # password=MONGO_PASSWORD,
                                          # authMechanism='SCRAM-SHA-1',
                                          # authSource=MONGO_DB
                                          )

        self.col = self.client[MONGO_DB][MONGO_COLLECTION]
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
        self.informer_one = self.bot.groups().search('洗稿群')
        # 信息接收人
        self.informer_two = self.bot.friends().search('洗稿2群')

        # 测试小号
        # self.test_user = self.bot.friends().search('max')

        # 关键词
        self.keywords = KEYWORDS
        # 加载日记配置文件
        self.logger = self.setup_logging()
        # 分发标识
        self.flag = 0

    def qr_callback(self, **kwargs):
        """获取二维码后将其写入文件再通过邮件发送到登录账号"""
        send_time = time.time()
        if not self.qr_flag:
            qr_path = 'QR.png'
            with open(qr_path, 'wb') as fp:
                fp.write(kwargs['qrcode'])
            email_test.send_qr('QR.png')
            self.qr_flag = True
        if send_time - self.start_time > 120:
            self.start_time = time.time()
            self.qr_flag = False

    def setup_logging(self, default_path='config.yaml', default_level=logging.INFO):
        """
        初始化日记对象
        :param default_path: logging配置文件，采用yaml格式
        :param default_level: logging默认等级
        :return: logger对象
        """
        # 判断日记文件夹是否存在
        log_dir = os.path.dirname(__file__) + '/logs'
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)

        # 如果日记配置文件存在，则加载配置，不存在则配置一个基础logging
        if os.path.exists(default_path):
            with open(default_path, 'r', encoding='utf-8') as f:
                # 读取yaml配置文件
                config = yaml.full_load(f)
                logging.config.dictConfig(config)
        else:
            logging.basicConfig(level=default_level)
        # 使用日记子类'gzh.core'
        logger = logging.getLogger('gzh.core')
        # 创建一个微信日志处理器
        wechat_handler = WeChatLoggingHandler(receiver=self.bot)
        wechat_handler.setLevel(logging.WARN)
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
        content_text = html.xpath('//div[@id="js_content"]//span//text()|//div[@id="js_content"]//strong//text()')
        # 匹配url连接
        img_urls = html.xpath('//div[@id="js_content"]//img/@data-src')
        # 将匹配的文章连接成长文本
        long_text = ''.join(content_text)
        resp_text = response.text

        # 判断文章文本中有活动关键字存在，有则直接返回状态码和关键词信息
        for keyword in self.keywords:
            if keyword in long_text:
                text = f'文章"文本"含有关键词, 关键词为"{keyword}"'
                time_list, result = regex_extract(long_text, resp_text)
                return 200, text, time_list, result

        # 若没有关键字，调用百度通用文字ocr接口下载图片并识别
        # 若图片识别结果中有活动关键字，返回status=200, pic_text='文章第{i}张"图片"含有关键词, 关键词为{j}
        # 若图片识别结果无活动，返回status=500, None
        # 若接口出错，返回status=400, pic_text=traceback.format_exc()
        if len(img_urls):
            status, pic_text, *word = BaiDuOcr().pic_ocr(img_urls)
            if status == 200:
                time_list, result = regex_extract(word[0], word[0])
                return status, pic_text, time_list, result
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
                self.logger.debug(f'信息成功向"{informer}"发送成功,信息:{str(msg)}')
            except ResponseError:
                self.logger.exception(f'发送失败或者接收人"{informer}"无法接收信息, 信息:{str(msg)}')
        else:
            self.logger.warning(f'找不到"{informer}"信息接收人, 信息:{str(msg)}!')

    def distribute_send(self, dic):

        # 向不同的群分发消息, 记得把新建的群加入到通讯录！！！
        if self.flag == 0:
            self.send_informer(self.informer_one, dic)
            self.flag += 1
        else:
            self.send_informer(self.informer_two, dic)
            self.flag = 0

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
                    # 获取文章Url
                    dic['url'] = article.url
                    # 获取创建时间
                    dic['create_time'] = msg.create_time.strftime('%Y-%m-%d %H:%M:%S')
                    print(dic)
                    # 将url传入检测函数
                    status, text, *result = self.get_info(dic['url'])
                    # self.logger.info(status, text, *result)
                    # 如果status返回值为200，表示公众号文章含有活动关键字
                    if status == 200:
                        dic['factor'] = text
                        # 分发消息
                        if len(result):
                            dic['time_list'] = result[0]
                            dic['result'] = result[1]

                        self.logger.debug(f'{text}, 信息:{str(dic)}')
                        self.col.update_one({'url': dic['url']}, {'$set': dic}, True)
                    # status返回值为400，则百度云接口出错
                    elif status == 400:
                        dic['Warning'] = '百度云文字识别模块错误'
                        dic['Error'] = text
                        self.logger.warning(f'{dic["Warning"]}, 信息:{str(dic)}')

                    else:
                        self.logger.info(f'{text}, 信息:{str(dic)}')

        embed()


if __name__ == '__main__':
    gzh = GzhMessage()
    t1 = threading.Thread(target=gzh.run)
    t1.start()

    listen_thread = None
    for i in threading.enumerate():
        if i.name == '_listen':
            listen_thread = i

    while True:
        if not listen_thread.is_alive() or listen_thread is None:
            content = f'公众号监听线程死亡, 请重新登录'
            email_test.error_alarm(content)
            print(content)
            break
        time.sleep(300)





