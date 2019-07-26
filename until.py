from setting import KEYWORDS
import re


def regex_extract(long_text, resp_text):
    regex_content = re.compile(
        r'([a-zA-Z0-9\u4e00-\u9fff，%“”.、\s]*(?:{})[a-zA-Z0-9\u4e00-\u9fff，%“”.、\s]*)'.format('|'.join(KEYWORDS))
    )
    regex_time = re.compile(
        r'[即日起至]*?\d{1,4}'
        r'[年月日号.\-/]+\d{1,2}'
        r'[年月日号.\-/]+\d{0,2}'
        r'[.至年月日号\-]?\d{0,4}'
        r'[至年月日号.\-/]?\d{0,2}'
        r'[年月日号.\-/]?\d{0,2}'
        r'[年月日号.\-]?'
    )
    sales_info = regex_content.findall(resp_text)  # 活动信息
    act_time = regex_time.findall(long_text)  # 活动时间
    # 过滤掉act_time中的非活动时间字符
    time_list = []

    for i in act_time:
        error_time = re.search(r'\d+[.\-年月/]\d+[.\-月号日]\d*/?[日号]?', i)
        if error_time is not None:
            if error_time.group() != i:
                time_list.append(i)

    wechat_sales = [i.strip() for i in sales_info]
    wechat_sales = list(set(wechat_sales))
    result = '，'.join(wechat_sales)

    return time_list, result


if __name__ == '__main__':
    from lxml.html import fromstring
    import requests
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
