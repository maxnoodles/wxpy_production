import traceback

import requests
from aip import AipOcr
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from lxml.html import fromstring
from setting import *


class BaiDuOcr:
    """百度通用文字OCR"""

    def __init__(self):
        # 百度云申请秘钥
        self.APP_ID = APP_ID
        self.API_KEY = API_KEY
        self.SECRET_KEY = SECRET_KEY
        # 百度图像识别ocr接口
        self.client = AipOcr(self.APP_ID, self.API_KEY, self.SECRET_KEY)
        # 通用文字识别参数选项
        self.options = {
            'language_type': 'CHN_ENG',
            'detect_direction': 'true',
            'detect_language': 'true'
        }
        # 活动关键词
        self.words_base = KEYWORDS

    # 批量Url文字识别
    def pic_ocr(self, url_lists):

        # 使用多线程（最大10个）进行请求
        with ThreadPoolExecutor(max_workers=10) as thread:
            # self.client.basicGeneralUrl是百度ocr通用文字接口，传入参数为urls和options
            # 因为map只能传入1个参数，这里使用partial偏函数将options传入basicGeneralUrl
            results = thread.map(partial(self.client.basicGeneralUrl, options=self.options), url_lists)
        # 将结果生成器转化成列表
        # print(list(results))

        i = 0
        try:
            for result in results:
                i += 1
                # 对识别出文字的图片进行判断
                words_result_num = result.get('words_result_num')
                if words_result_num != 0 and words_result_num is not None:
                    a = result.get('words_result')
                    # 拼接识别出的文字
                    if a:
                        words = ''.join([i.get('words') for i in a])
                        # print(words)
                        # 判断关键词是否在图片的文字中,如果有就返回
                        for j in self.words_base:
                            if j in words:
                                text = f'文章第"{i}"张"图片"含有关键词, 关键词为"{j}"'
                                # 若正确返回200
                                return 200, text, words
        except Exception as e:
            # 如果百度云文字识别接口发送错误，返回错误信息
            return 400, traceback.format_exc()

        # 若没有识别出活动，返回500
        no_text = '该文章图片不含关键词，没有活动'
        return 500, no_text


if __name__ == '__main__':
    url = 'https://mp.weixin.qq.com/s?__biz=MzIxMTM0OTQ5NA==&mid=2247491225&idx=2&sn=bcd083e5b13bc32984006cf0cf483fcb&chksm=9757e400a0206d160306e1b674089a1b8f5ccbd8e91468b0348290adc4aeda2a48d46b954e83&scene=0&xtrack=1#rd'
    response = requests.get(url, timeout=10)
    html = fromstring(response.text)

    long_text = html.xpath('//div[@id="js_content"]//span//text()')

    img_urls = html.xpath('//div[@id="js_content"]//img/@data-src')
    print(img_urls)
    BaiDuOcr().pic_ocr(img_urls)


