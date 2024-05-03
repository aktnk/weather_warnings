import requests
from cachecontrol import CacheControl 
from cachecontrol.caches import FileCache, SeparateBodyFileCache
import xmltodict
import datetime
import pandas as pd

EXTRA_URL='https://www.data.jma.go.jp/developer/xml/feed/extra.xml'
WARNINGS='気象特別警報・警報・注意報'
TARGET_OBSERVATORY='旭川地方気象台'
TARGET_INFORMATION='気象警報・注意報（市町村等）'
TARGET_CITY='美瑛町'

# extra.xmlの取得
session = requests.Session()
cached_session = CacheControl(session, cache=SeparateBodyFileCache('.webcache'))
response = cached_session.get(EXTRA_URL) 
print(f'from_cache: {response.from_cache}') 

# 取得したい気象台から警報・注意報がでているか確認
extra_dict = xmltodict.parse(response.content)
target_warnings = []
for entry in extra_dict['feed']['entry']:
    if entry['title'] == WARNINGS and entry['author']['name'] == TARGET_OBSERVATORY:
        target_warnings.append((entry['title'], entry['id'], datetime.datetime.fromisoformat(entry['updated'][:-1]), entry['author']['name'], entry['content']['#text']))
len(target_warnings)
if len(target_warnings) == 0:
    print("{}")

# 警報・注意報がでているようなら詳細情報を取得
df = pd.DataFrame(target_warnings, columns=['title', 'id', 'updated', 'author', 'content'])
sorted_df = df.sort_values('updated',ascending=False)
sorted_df.at[0,'id']
detail = cached_session.get(sorted_df.at[0,'id']) 
print(f'from_cache: {detail.from_cache}') 

# 取得結果を表示
detail_dict = xmltodict.parse(detail.content)
print(f"発表：{detail_dict['Report']['Control']['PublishingOffice']}")
print(f"時刻：{datetime.datetime.fromisoformat(detail_dict['Report']['Control']['DateTime'][:-1])}")

for info in detail_dict['Report']['Head']['Headline']['Information']:
    #print(info)
    if info['@type'] == TARGET_INFORMATION:
        print(f"<<{TARGET_CITY}>>")
        warn=False
        for item in info['Item']:
            #print(item['Areas']['Area']['Name'])
            if item['Areas']['Area']['Name'] == TARGET_CITY:
                for kind in item['Kind']:
                    print(kind['Name'])
                    warn=True
        if not warn:
            print(f"警報・注意報なし")
