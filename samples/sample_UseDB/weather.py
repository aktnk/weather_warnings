import datetime
import os
from dotenv import load_dotenv

from db_setting import session
from models import CityReport, Extra, VPWW54xml
from JMAFeed import JMAFeed, VPWW54XMLData
from MSteams import MSTeams
from weather_DB import deleteCityReportByLMO, deleteVPWW54xmlByLMO, deleteCityReportByStatus, updateCityReportByStatus, updateCityReportByXmlfile, checkCityAndKindDataSameInCityReport, addVPWW54xml, createCityReport

load_dotenv()
WEBHOOK_URL = os.getenv('TEAMS_WEBHOOK')
MENTION_USERID = os.getenv('MENTION_USERID')
MENTION_USERNAME = os.getenv('MENTION_USERNAME')

def printJMAwarningsInfo(feed, obs, cities, teams = None):
    entry = feed.getLatestVPWW54EntryByLMO(obs)
    if entry is None:
        print(f"**{obs}では現在警報・注意報の発表なし")
        # lmoがobsのデータのデータ（の中で注意報はstatusが解除、警報は解除でなくても）は削除
        deleteCityReportByLMO(obs)
        deleteVPWW54xmlByLMO(obs)
    else:
        vpww54 = VPWW54XMLData( url = entry.id, obs = obs )
        for city in cities:
            warning, control, head = vpww54.getCityWarnings(city)
            print(f"=== {city} ===")
            print(f"{head}")
            print(f"{control}")
            print(f"{warning}")
            print(f"===============")
            for item in warning.kind:
                if item['kindName'] is None:
                    if item['status'] == "発表警報・注意報はなし":
                        deleteCityReportByStatus(obs, warning.areaName)
                    continue
                # lmoがobsで、cityがcity、kind_nameがitem['kindName']、statusがitem['status']があるか
                ret, report = checkCityAndKindDataSameInCityReport(obs,warning.areaName,item['kindName'])
                if ret:
                    # 同じ市町で同じ警報・注意報のデータあり
                    if report.status != item['status']:
                        # statusが異なれば、Teams通知して、DB更新
                        if teams is not None:
                            teams.send_message(control.publishedBy, warning.areaName, item['kindName'], item['status'], control.datetime)
                        xmlchanged = updateCityReportByStatus(obs,warning.areaName,item['kindName'],item['status'],vpww54.filename)
                        if xmlchanged:
                            addVPWW54xml(obs, vpww54.filename)
                    elif report.xmlfile != vpww54.filename:
                        # statusが同じだが、xmlfileが異なれば、DBに追加
                        print(f"{item}はstatus同じだが、xmlfile違いあり")
                        updateCityReportByXmlfile(obs,warning.areaName,item['kindName'],item['status'],vpww54.filename)
                        addVPWW54xml(obs, vpww54.filename)
                    else:
                        # 全て同じデータ登録済み＝公開済み
                        print(f"{item}は全て同じデータ＝公開済み")
                else:
                    print(f"{item}は未公開")
                    if teams is not None:
                        teams.send_message(control.publishedBy, warning.areaName, item['kindName'], item['status'], control.datetime,)
                    createCityReport(obs,warning.areaName,item['kindName'],item['status'],vpww54.filename)
                    addVPWW54xml(obs, vpww54.filename)


if __name__ == '__main__':
    print(f"******** start: {datetime.datetime.now()}")
    print(f"{WEBHOOK_URL}")
    print(f"{MENTION_USERID} : {MENTION_USERNAME}")
    myteams = MSTeams(WEBHOOK_URL, MENTION_USERID, MENTION_USERNAME)

    feed = JMAFeed()
    printJMAwarningsInfo(feed, '静岡地方気象台',['裾野市','御殿場市','三島市','熱海市'], myteams)
    #printJMAwarningsInfo(feed, '松山地方気象台',['松山市'])
    #printJMAwarningsInfo(feed, '旭川地方気象台',['士別市'], myteams)
    #printJMAwarningsInfo(feed, '宮崎地方気象台',['都城市'])
    #printJMAwarningsInfo(feed, '鹿児島地方気象台',['南九州市'])
    #printJMAwarningsInfo(feed, '青森地方気象台',['つがる市'], myteams)

    print(f"******** end: {datetime.datetime.now()}")
    
