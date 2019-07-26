from lxml.html import fromstring
import requests
from until import regex_extract


url = 'https://mp.weixin.qq.com/s?__biz=MzIwMjU4Nzc2Nw==&mid=2247487200&idx=1&sn=e6cb16fd653ca4471f9cd47247a8d8b1&chksm=96dd25f8a1aaacee6b0528199a79c810d8b6f3e5e8ff2ef6b905e81d48d2765078162a20f9c8&scene=0&xtrack=1#rd'

keywords = ['发售', '折', '特卖', '特惠', '优惠', '免费', '立省', '钜惠', '秒杀', '领券',
            '预售', '半价', '买一送一', '减', '促销', '新品', '兑换', '全新', '半价', '赠送']

response = requests.get(url, timeout=10)
html = fromstring(response.text)
# 匹配文字
content_text = html.xpath('//div[@id="js_content"]//span//text()|//div[@id="js_content"]//strong//text()')
# 匹配url连接
img_urls = html.xpath('//div[@id="js_content"]//img/@data-src')
# 将匹配的文章连接成长文本
long_text = ''.join(content_text)
resp_text = response.text

# 判断文章文本中有活动关键字存在，有则直接返回状态码和关键词信息
for keyword in keywords:
    if keyword in long_text:
        text = f'文章"文本"含有关键词, 关键词为"{keyword}"'
        time_list, result = regex_extract(long_text, resp_text)
        print(200, text, time_list, result)
        break