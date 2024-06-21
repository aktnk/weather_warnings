import requests
import xmltodict
import datetime
import os
from pytz import timezone

from db_setting import session
from models import CityReport, Extra

EXTRA = 'https://www.data.jma.go.jp/developer/xml/feed/extra.xml'
FILENAME = os.path.join("data",EXTRA.split('/')[-1])

class JMAFeed:
    """
    気象庁(Japan Meteorological Agency)Feed
    """
    VPWW54_TITLE='気象警報・注意報（Ｈ２７）'

    def __init__(self):
        self.dict = None
        self.LMO = ""
        self.VPWW54list = []

    def readExtraFile(self):
        """
        xmlfile で指定したXMLファイルを読み取り、文字列として返す
        xmlfile が存在しない場合は、""空文字列を返す
        """
        response = ""
        if (os.path.isfile(FILENAME)):
            with open(FILENAME, mode="r", encoding='utf-8') as f:
                response = f.read()
        else:
            # extra.xmlファイルが存在しないとき
            time = datetime.datetime.now()
            response = requests.get(EXTRA).content
            with open(FILENAME, mode='wb') as f:
                f.write(response)
            updateExtraDownloadedTime(time)
        return response

    def getFeed(self, url=EXTRA):
        """
        url から Feed を取得し、dict形式で結果を保持する
        """
        if isExtraWithin10Minutes():
            response = self.readExtraFile()
        else:
            time = datetime.datetime.now()
            response = requests.get( url ).content
            with open(FILENAME, mode='wb') as f:
                f.write(response)
            updateExtraDownloadedTime(time)
        self.dict = xmltodict.parse( response )

    def analyzeVPWW54ListbyLMO(self, obs):
        """
        地方気象台 obs が発表した気象特別警報・警報・注意報（VPWW54形式：気象警報・注意報（Ｈ２７））のリストを取得する
        """
        vpww54list = []
        for entry in self.dict['feed']['entry']:
            if entry['title'] == self.VPWW54_TITLE and entry['author']['name'] == obs:
                warning = JMAFeedEntryData(
                    title = entry['title'],
                    id = entry['id'],
                    updated = datetime.datetime.strptime(entry['updated'][:-1]+'+0000','%Y-%m-%dT%H:%M:%S%z').astimezone(timezone('Asia/Tokyo')),
                    author_name=entry['author']['name'],
                    content = entry['content']['#text']
                )
                if len(vpww54list) == 0:
                    vpww54list.append(warning)
                else:
                    # 日付の新しいものから古いものへ順に並べて、wpww54listに保存する
                    found = False
                    for idx, item in enumerate(vpww54list):
                        if warning.updated > item.updated:
                            vpww54list.insert( idx, warning)
                            found = True
                            break
                        else:
                            continue
                    if not found:
                        vpww54list.append(warning)
        self.VPWW54list = vpww54list
        return vpww54list
    
    def getLatestVPWW54EntryByLMO(self, obs):
        self.LMO = obs
        if self.dict is None:
            self.getFeed()
        self.analyzeVPWW54ListbyLMO(obs)
        if len(self.VPWW54list) > 0:
            return self.VPWW54list[0]
        else:
            return None

class JMAFeedEntryData:
    """
    JMAFeedクラスのanalyzeVPWW54ListbyLMO(obs)メソッドが生成する気象情報リストに保管されるEntryデータのクラス
    """

    def __init__(self, title, id, updated, author_name, content):
        self.title = title
        self.id = id
        self.updated = updated
        self.author_name = author_name
        self.content = content

    def __str__(self):
        return f'title:{self.title}, id:{self.id}, updated:{self.updated}, LMO:{self.author_name}, msg:{self.content}'


class VPWW54XMLData:
    """
    VPWW54形式のXMLデータのクラス
    """
    
    def __init__(self, url):
        self.url = url
        self.filename = url.split('/')[-1]
        self.warnings = []
        self.dict = {}

    def getData(self):
        """
        VPWW54形式のxmlファイルがダウンロード済みであればファイルから、そうでなければURLから取得する
        """
        # 当該xmlファイルが存在するか？
        filepath = os.path.join("data",self.filename)
        if (os.path.isfile(filepath)):
            print(f"xmlfile read:{self.filename}")
            response = self.readXMLfile(filepath)
        else:
            response = requests.get(self.url).content
            print(f"xmlfile download 1:{self.filename}")
            with open(filepath, mode='wb') as f:
                    f.write(response)

        self.dict = xmltodict.parse( response )

    def readXMLfile(self, xmlfile):
        """
        xmlfile で指定したXMLファイルを読み取り、文字列として返す
        xmlfile が存在しない場合は、""空文字列を返す
        """
        response = ""
        if (os.path.isfile(xmlfile)):
            with open(xmlfile, mode="r", encoding='utf-8') as f:
                response = f.read()
        return response

    def analyzeAll(self, warning_type='気象警報・注意報（市町村等）' ):
        """
        取得したxmlデータを解析し、警報・注意報に関する情報を得る
        """
        # Controlタグ情報の取得
        self.control = VPWW54Control(
            title = self.dict['Report']['Control']['Title'],
            datetime = datetime.datetime.strptime(self.dict['Report']['Control']['DateTime'][:-1]+'+0000','%Y-%m-%dT%H:%M:%S%z').astimezone(timezone('Asia/Tokyo')),
            status = self.dict['Report']['Control']['Status'],
            publishing_office = self.dict['Report']['Control']['PublishingOffice']
        )
        # Headタグ情報の取得
        self.head = VPWW54Head(
            title = self.dict['Report']['Head']['Title'],
            report_datetime = datetime.datetime.strptime(self.dict['Report']['Head']['ReportDateTime'],'%Y-%m-%dT%H:%M:%S%z'),
            info_type = self.dict['Report']['Head']['InfoType'],
            info_kind = self.dict['Report']['Head']['InfoKind'],
        )
        # Body>Warningタグ情報の取得
        for warning in self.dict['Report']['Body']['Warning']:
            if warning['@type'] == warning_type:
                for item in warning['Item']:
                    # Area>NameタグとChangeStatusタグの取得
                    if 'ChangeStatus' in item:
                        city_warnings = VPWW54BodyWarningTypeCity(
                            area_name=item['Area']['Name'],
                            change_status = item['ChangeStatus']
                        )
                    else:
                        city_warnings = VPWW54BodyWarningTypeCity(
                            area_name=item['Area']['Name'],
                            change_status = None
                        )
                    # Kindタグ情報の取得
                    if type(item['Kind']) is dict:
                        if 'Name' in item['Kind']:
                            city_warnings.addKind(
                                kind_name = item['Kind']['Name'],
                                status = item['Kind']['Status']
                            )
                        else:
                            city_warnings.addKind(
                                kind_name = None,
                                status = item['Kind']['Status']
                            )
                    elif type(item['Kind']) is list:

                        for kind in item['Kind']:
                            city_warnings.addKind(
                                kind_name = kind['Name'],
                                status = kind['Status']
                            )
                    # 解析結果をwarnings属性へ追加
                    if city_warnings is not None:
                        self.warnings.append( city_warnings )

    def getCityWarnings( self, city ):
        """
        VPWW54形式xmlデータを取得し、指定されたcityの警報・注意報を取り出す
        """
        if len(self.warnings) == 0:
            self.getData()
            self.analyzeAll()
            #print("analyzeAll:::")
        for warning in self.warnings:
            #print(warning)
            if warning.areaName == city:
                return warning, self.control, self.head
                

class VPWW54Control:
    """
    VPWW54形式xmlデータのControlタグに含まれるデータのクラス
    """

    def __init__(self, title, datetime, status, publishing_office):
        self.title = title
        self.datetime = datetime
        self.status = status
        self.publishedBy = publishing_office

    def __str__(self):
        return f'Control, title:{self.title}, datetime:{self.datetime}, status:{self.status}, publishedBy:{self.publishedBy}'

class VPWW54Head:
    """
    VPWW54形式xmlデータのHeadタグに含まれるデータのクラス
    """
    def __init__(self, title, report_datetime, info_type, info_kind):
        self.title = title
        self.reportDateTime = report_datetime
        self.infoType = info_type
        self.infoKind = info_kind

    def __str__(self):
        return f'Head, title:{self.title}, reportDateTime:{self.reportDateTime}, infoType:{self.infoType}, infoKind:{self.infoKind}'

class VPWW54BodyWarningTypeCity:
    """
    VPWW54形式xmlデータのBodyタグに含まれる市町村の警報・注意報データのクラス
    """

    warningType = '気象警報・注意報（市町村等）'

    def __init__(self, area_name, change_status):
        self.areaName = area_name
        self.changeStatus = change_status
        self.kind = []

    def __str__(self):
        ans = f'Warning, type:{self.warningType}, city:{self.areaName}, changeStatus:{self.changeStatus}'
        for item in self.kind:
            ans = ans + f", Item, kindName:{item['kindName']}, status:{item['status']}"
        return ans

    def addKind( self, kind_name, status):
        self.kind.append( {'kindName': kind_name, 'status': status})

def printJMAwarningsInfo(feed, obs, cities):
    entry = feed.getLatestVPWW54EntryByLMO(obs)
    if entry is None:
        print(f"{obs}では現在警報・注意報の発表なし")
        # lmoがobsのデータあれば、削除
        deleteCityReportByLMO(obs)
    else:
        vpww54 = VPWW54XMLData( url = entry.id )
        for city in cities:
            warning, control, head = vpww54.getCityWarnings(city)
            print(f"=== {city} ===")
            print(f"{head}")
            print(f"{control}")
            print(f"{warning}")
            print(f"===============")
            for item in warning.kind:
                # lmoがobsで、cityがcity、kind_nameがitem['kindName']、statusがitem['status']があるか
                # xmlfileがvpww54.filenameであれば、表示しない（すでに展開済み）
                # xmlfileが無ければ、表示し、CityReportに登録する。
                # xmlfileが違うものがあれば、表示しないが、xmlfileを更新する
                if item['kindName'] is None:
                    continue
                if isDataInCityReport(obs,warning.areaName,item['kindName'],item['status'],vpww54.filename):
                    # 登録済み＝公開済み
                    print(f"{item}は公開済み")
                else:
                    # 登録データなし＝未公開
                    if isNonXmlfileDataInCityReport(obs,warning.areaName,item['kindName'],item['status'],vpww54.filename):
                        # 違うxmlfileならデータあれば、xmlfileを更新するが発表しない
                        print(f"{item}はxmlfile違いあり")
                        updateCityReportByXmlfile(obs,warning.areaName,item['kindName'],item['status'],vpww54.filename)
                    else:
                        print(f"{item}は未公開")
                        createCityReport(obs,warning.areaName,item['kindName'],item['status'],vpww54.filename)


def isNonXmlfileDataInCityReport(obs,city,kind_name,status,xmlfile):
    """
    CityReportテーブルにlmoがobs,cityがcity,kind_nameがitem.kindName,statusがitem.status,xmlfileがxmlfile以外のデータあるか調べる
    """
    print(f"nonXMLfile判定: {obs}, {city}, {kind_name}, {status}, {xmlfile}")
    report = session.query(CityReport).filter(
        CityReport.lmo==obs,
        CityReport.city==city,
        CityReport.kind_name==kind_name,
        CityReport.status==status,
        CityReport.xmlfile!=xmlfile,
        CityReport.is_delete==False).first()
    
    if report is None:
        print("CityReporにxmlfilaが同じデータなし")
        return False
    print("CityReportにxmlfilaが同じデータあり")
    return True

def isDataInCityReport(obs,city,kind_name,status,xmlfile):
    """
    CityReportテーブルにlmoがobs,cityがcity,kind_nameがitem.kindName,statusがitem.statusのデータあるか調べる
    """
    print(f"判定: {obs}, {city}, {kind_name}, {status}, {xmlfile}")
    report = session.query(CityReport).filter(
        CityReport.lmo==obs,
        CityReport.city==city,
        CityReport.kind_name==kind_name,
        CityReport.status==status,
        CityReport.xmlfile==xmlfile,
        CityReport.is_delete==False).first()
    
    if report is None:
        print("CityReporに同じデータなし")
        return False
    print("CityReportに同じデータあり")
    return True

def createCityReport(obs, city, kind_name, status, xmlfile):
    """
    CiryReportテーブルに新規にデータを登録する
    """
    print(f"create: {obs}, {city}, {kind_name}, {status}, {xmlfile}")
    report = CityReport()
    report.lmo = obs
    report.city = city
    report.kind_name = kind_name
    report.status = status
    report.xmlfile = xmlfile
    session.add(report)
    session.commit()

def updateCityReportByXmlfile(obs, city, kind_name, status, xmlfile):
    """
    CityReportテーブルのxmlfileを更新する
    """
    print(f"delete: {obs}, {city}, {kind_name}, {status}, {xmlfile}")
    report = session.query(CityReport).filter(
        CityReport.lmo==obs,
        CityReport.city==city,
        CityReport.kind_name==kind_name,
        CityReport.status==status,
        CityReport.xmlfile!=xmlfile,
        CityReport.is_delete==False).first()
    report.xmlfile=xmlfile
    session.commit()

def deleteCityReportByXmlfile(obs, city, kind_name, status, xmlfile):
    """
    CityReportテーブルの指定したデータを削除する
    """
    print(f"delete: {obs}, {city}, {kind_name}, {status}, {xmlfile}")
    report = session.query(CityReport).filter(
        CityReport.lmo==obs,
        CityReport.city==city,
        CityReport.kind_name==kind_name,
        CityReport.status==status,
        CityReport.xmlfile==xmlfile,
        CityReport.is_delete==False).first()
    report.is_delete=True
    session.commit()

def deleteCityReportByLMO(obs):
    """
    CityReportテーブルから、lmoがobsのデータがあれば、削除する
    """
    reports = session.query(CityReport).filter(CityReport.lmo == obs).all()
    for report in reports:
        print(f"delete: {report.id}, {report.lmo}, {report.xmlfile}, {report.city}, {report.kind_name}, {report.status}, {report.is_delete}")
        report.is_delete = True
        session.commit()
    
def isExtraWithin10Minutes():
    """
    extra.xmlを10分以内に取得済みか判定する
    """
    extra = session.query(Extra).first()
    if extra is None:
        print("no extra : without 10 minutes")
        return False
    else:
        if datetime.datetime.now()- extra.downloaded_at < datetime.timedelta(minutes = 10):
            print("within 10 minutes")
            return True
        else:
            print("without 10 minutes")
            return False


def updateExtraDownloadedTime( time ):
    """
    extra.xmlのダウンロード時間をtimeに更新する
    """
    extra = session.query(Extra).first()
    if extra is None:
        new_extra = Extra()
        session.add( new_extra )
        session.commit()
    else:
        extra.downloaded_at = time
        session.commit()
    session.close()

if __name__ == '__main__':
    feed = JMAFeed()
    printJMAwarningsInfo(feed, '静岡地方気象台',['裾野市','御殿場市','三島市','熱海市'])
    printJMAwarningsInfo(feed, '神奈川地方気象台',['横浜市'])
    printJMAwarningsInfo(feed, '旭川地方気象台',['士別市'])
