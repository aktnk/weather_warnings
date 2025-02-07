# sample_UseDB

sqlite を使い、下記を実現する

- extra.xml ファイルの 10 分以内取得を行わない
- ある市町に発表された警報・注意報について、状態に変更が無ければ、通知しない
- Microsoft Teams にメンションをつけて通知可能

## 使い方

1. 本リポジトリをクローンする

   ```
   $ git clone https://github.com/aktnk/weather_warnings.git

   $ cd weather_warinigs/samples/sample_UseDB
   ```

1. pyenv を使い、python 3.10.3 をインストール

   ```
   $ pyenv install 3.10.3

   $ pyenv local 3.10.3
   ```

1. venv で仮想環境を準備する

   ```
   $ python -m venv venv310

   $ source venv310/bin/activate

   (venv310) $ pip install -r requirements.txt
   ```

1. データベースの作成

   ```
   (venv310) $ python models.py
   ```

1. ダウンロードした XML ファイルを一時保管するディレクトリを .env ファイルの DATADIR へ設定する

   ```.env
   DATADIR="data"
   ```

1. MS Teams へ通知する場合

   1. .env ファイルに　 TEAMS_WEBHOOK、MENTION_USERID、MENTION_USERNAME を設定する

      ```.env
      TEAMS_WEBHOOK="(PowerAutomateに設定したTEAMS WEBHOOKのURL)"
      MENTION_USERID="(TeamsのアカウントID)"
      MENTION_USERNAME="(Teamsでメンションに表示する名前)"
      ```

   1. 通知先の MSTeams のインスタンスを作成

   ```
   myteams = MSTeams(WEBHOOK_URL, MENTION_USERID, MENTION_USERNAME)
   ```

   1. `weather.py`の`__main__`にて、`printJMAwarningsInfo()`の 3 番目の引数に、通知する MSTeams のインスタンスを指定する

   （例）下記のようにメンション付きで通知できる
   ![MS Teams Message Sample by Incomming Webhook](./image/MSTeamsSample.png)
   ![MS Teams Message Sample by PowerAutomete Workflow](./image/MSTeamsSample2.png)

1. 指定した市町の警報・注意報を取得する

   ```
   (venv310) $ python weather.py
   without 10 minutes
   xmlfile read:20240621105730_0_VPWW54_220000.xml
   === 裾野市 ===
   Head, title:静岡県気象警報・注意報, reportDateTime:2024-06-21 19:57:00+09:00, infoType:発表, infoKind:気象警報・注意報
   Control, title:気象警報・注意報（Ｈ２７）, datetime:2024-06-21 19:57:30+09:00, status:通常, publishedBy:静岡地方気象台
   Warning, type:気象警報・注意報（市町村等）, city:裾野市, changeStatus:None, Item, kindName:None, status:発表警報・注意報はなし
   ===============
   === 御殿場市 ===
   Head, title:静岡県気象警報・注意報, reportDateTime:2024-06-21 19:57:00+09:00, infoType:発表, infoKind:気象警報・注意報
   Control, title:気象警報・注意報（Ｈ２７）, datetime:2024-06-21 19:57:30+09:00, status:通常, publishedBy:静岡地方気象台
   Warning, type:気象警報・注意報（市町村等）, city:御殿場市, changeStatus:None, Item, kindName:None, status:発表警報・注意報はなし
   ===============
   === 三島市 ===
   Head, title:静岡県気象警報・注意報, reportDateTime:2024-06-21 19:57:00+09:00, infoType:発表, infoKind:気象警報・注意報
   Control, title:気象警報・注意報（Ｈ２７）, datetime:2024-06-21 19:57:30+09:00, status:通常, publishedBy:静岡地方気象台
   Warning, type:気象警報・注意報（市町村等）, city:三島市, changeStatus:None, Item, kindName:None, status:発表警報・注意報はなし
   ===============
   === 熱海市 ===
   Head, title:静岡県気象警報・注意報, reportDateTime:2024-06-21 19:57:00+09:00, infoType:発表, infoKind:気象警報・注意報
   Control, title:気象警報・注意報（Ｈ２７）, datetime:2024-06-21 19:57:30+09:00, status:通常, publishedBy:静岡地方気象台
   Warning, type:気象警報・注意報（市町村等）, city:熱海市, changeStatus:None, Item, kindName:None, status:発表警報・注意報はなし
   ===============
   神奈川地方気象台では現在警報・注意報の発表なし
   xmlfile read:20240621112341_0_VPWW54_012000.xml
   === 士別市 ===
   Head, title:上川・留萌地方気象警報・注意報, reportDateTime:2024-06-21 20:23:00+09:00, infoType:発表, infoKind:気象警報・注意報
   Control, title:気象警報・注意報（Ｈ２７）, datetime:2024-06-21 20:23:40+09:00, status:通常, publishedBy:旭川地方気象台
   Warning, type:気象警報・注意報（市町村等）, city:士別市, changeStatus:警報・注意報種別に変化有, Item, kindName:雷注意報, status:解除, Item, kindName:濃霧注意報, status:継続
   ===============
   判定: 旭川地方気象台, 士別市, 雷注意報, 解除, 20240621112341_0_VPWW54_012000.xml
   CityReportに同じデータあり
   {'kindName': '雷注意報', 'status': '解除'}は公開済み
   判定: 旭川地方気象台, 士別市, 濃霧注意報, 継続, 20240621112341_0_VPWW54_012000.xml
   CityReportに同じデータあり
   {'kindName': '濃霧注意報', 'status': '継続'}は公開済み
   (venv310) $
   ```

1. 指定した日数より前のデータを削除する

- `remove_data.py` の `period = 30` で指定した日数をデフォルトで 30 日としている

  ```
  if __name__ == '__main__':
    print(f"filepath:{__file__}")
    print(f"dirname:{os.path.dirname(__file__)}")
    period = 30
    targetpath = os.path.join(os.path.dirname(__file__), "del","*.xml")
    deleteFileBefore(targetpath, days = period)
    deleteCityReportBefore( days = period )
    deleteVPWW54xmlBefore( days = period )
  ```

- 削除の実行は下記のように remove_data.py を実行すればよい
  ```
  (venv310) $ python remove_data.py
  filepath:/home/aktnk/projects/weather_warnings/samples/sample_UseDB/remove_data.py
  dirname:/home/aktnk/projects/weather_warnings/samples/sample_UseDB
  20240726124741_0_VPWW54_220000.xml:2024-07-26 21:57:07.146880
  2024-11-28 18:07:04.510635
  20240726124741_0_VPWW54_220000.xml:2024-07-26 21:57:07.146880:remove
  20240723120410_0_VPWW54_220000.xml:2024-07-23 21:08:06.705197
  2024-11-28 18:07:04.510698
  20240723120410_0_VPWW54_220000.xml:2024-07-23 21:08:06.705197:remove
  20240722120415_0_VPWW54_220000.xml:2024-07-23 00:28:07.464098
  2024-11-28 18:07:04.510742
  20240824141623_0_VPWW54_220000.xml:2024-08-24 23:40:42.268878:remove
  **delete CR table: 1, 静岡地方気象台, 20240826124631_0_VPWW54_220000.xml, 裾野市, 雷注意報, 継続, True
  **delete CR table: 2, 静岡地方気象台, 20240826124631_0_VPWW54_220000.xml, 御殿場市, 雷注意報, 継続, True
  **remove xmlfile: 2, 静岡地方気象台, 20240826124631_0_VPWW54_220000.xml, True
  (venv310) $
  ```

## 動作確認環境

本サンプルは下記環境にて動作確認を実施

- WSL2 Ubuntu 20.04.6 LTS on Windows 11 Professional
- Python 3.10.3

## 参照

- MS Teams へメンション付きで投稿をするには adaptivecard を使うことで可能となる
  - [Learn]>[Microsoft Team]s>[Teams でカードを書式設定する]>[アダプティブ カード内でのサポートのメンション](https://learn.microsoft.com/ja-jp/microsoftteams/platform/task-modules-and-cards/cards/cards-format?tabs=adaptive-md%2Cdesktop%2Cconnector-html#mention-support-within-adaptive-cards)
