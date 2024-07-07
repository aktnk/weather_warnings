import requests
import xmltodict
import datetime
from pytz import timezone
import os

from db_setting import session
from models import CityReport, Extra

class JMAFeed:
    """
    気象庁(Japan Meteorological Agency)Feed
    """
    EXTRA = 'https://www.data.jma.go.jp/developer/xml/feed/extra.xml'
    VPWW54_TITLE='気象警報・注意報（Ｈ２７）'
    DATADIR = 'data'
    FILENAME = os.path.join(DATADIR, EXTRA.split('/')[-1])

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
        if (os.path.isfile(JMAFeed.FILENAME)):
            with open(JMAFeed.FILENAME, mode="r", encoding='utf-8') as f:
                response = f.read()
        else:
            # extra.xmlファイルが存在しないとき
            time = datetime.datetime.now()
            response = requests.get(JMAFeed.EXTRA).content
            with open(JMAFeed.FILENAME, mode='wb') as f:
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
            with open(JMAFeed.FILENAME, mode='wb') as f:
                f.write(response)
            updateExtraDownloadedTime(time)
        self.dict = xmltodict.parse( response )

    def analyzeVPWW54ListbyLMO(self, obs):
        """
        地方気象台 obs が発表した気象特別警報・警報・注意報（VPWW54形式：気象警報・注意報（Ｈ２７））のリストを取得する
        """
        vpww54list = []
        for entry in self.dict['feed']['entry']:
            if entry['title'] == JMAFeed.VPWW54_TITLE and entry['author']['name'] == obs:
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
        filepath = os.path.join( JMAFeed.DATADIR, self.filename)
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

def isExtraWithin10Minutes():
    """
    extra.xmlを10分以内に取得済みか判定する
    """
    try:
        extra = session.query(Extra).first()
    except err:
        if (not os.path.isfile(JMAFeed.FILENAME)):
            print("Error: db file not found. Please run `python models.py`")
        print(f"{err}")
        sys.exit()

    if extra is None:
        print("no extra : without 9 minutes")
        return False
    else:
        if datetime.datetime.now()- extra.downloaded_at < datetime.timedelta(minutes = 9):
            print("within 9 minutes")
            return True
        else:
            print("without 9 minutes")
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