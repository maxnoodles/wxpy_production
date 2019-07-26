# coding:utf-8
import re
import requests

headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
           'Accept-Encoding': 'gzip, deflate, br',
           'Accept-Language': 'zh-CN,zh;q=0.9',
           'Cache-Control': 'max-age=0',
           'Connection': 'keep-alive',
           'Cookie': 'pgv_pvid=4535698504; pgv_pvi=9152003072; pac_uid=0_6ec3c73fbe29b; tvfe_boss_uuid=1ab31030987ad921; ua_id=PXWcE37497OaZwVTAAAAAP2bQ4EURrMJ2TV3wACj7-Y=; mm_lang=zh_CN; RK=WNRAkWjsUA; ptcz=a0f39d1062f7dd4e46ca766b7f13a683e7f7fbfa4d62ef10a4159d839b8bc114; xid=e9117bd08005d3539f4b81251ff9d889; ptui_loginuin=309600517; rewardsn=; wxtokenkey=777',
           'Host': 'mp.weixin.qq.com',
           'Upgrade-Insecure-Requests': '1',
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}
url = 'https://mp.weixin.qq.com/s/otdjF4Wues3I38KvHDapmg'
resp = requests.get(url, headers=headers).text
# (?:pattern)非获取匹配
regex_content = re.compile(r'([a-zA-Z0-9\u4e00-\u9fff，%“”.、\s]*(?:限量|优惠|折|领券)[a-zA-Z0-9\u4e00-\u9fff，%“”.、\s]*)')
regex_time = re.compile(r'[即日起至]*?\d{1,4}[年月日号.\-/]+\d{1,2}[年月日号.\-/]+\d{0,2}[.至年月日号\-]?\d{0,4}[至年月日号.\-/]?\d{0,2}[年月日号.\-/]?\d{0,2}[年月日号.\-]?')
sales_info = regex_content.findall(resp)  # 活动信息
act_time = regex_time.findall(resp)  # 活动时间
# 过滤掉act_time中的非活动时间字符
time_list = []
for i in act_time:
    error_time = re.findall(r'\d+\.\d+\.\d+/', i)
    if len(error_time) == 0:
        time_list.append(i)
print(time_list)
print(len(sales_info))
wechat_sales = [i.strip() for i in sales_info]
wechat_sales = list(set(wechat_sales))
result = '，'.join(wechat_sales)
print(result)