# weather_warnings

気象庁防災情報の取得

## はじめに

気象庁が XML フォーマットで気象情報を公開している。

**実現したいこと**

- 指定した市町の警報・注意報を取得し表示すること

利用にあたっては、下記に公開されている利用方法や注意事項に従う必要がある。
[気象庁防災情報 XML フォーマット形式電文の公開（PULL 型）](https://xml.kishou.go.jp/xmlpull.html)

## 実現方法

- 警報・注意報の情報を取得するため、気象庁が公開している[高頻度フィードの随時情報](https://www.data.jma.go.jp/developer/xml/feed/extra.xml)を取得する
- 上記を情報から指定した市町の気象情報を発表している地方気象台が公開している情報を解析し、最新の警報・注意報を公開している URL を取得する
- URL から再度 XML を取得し、指定した市町の情報を確認し、該当する情報があれば表示する
- XML のダウンロード量を極力減らずため、HTTP リクエストした際に返される Last-Modified,Etag 情報を考慮したキャッシュを利用する

## 実現したサンプル

- [旭川地方気象台　が公開する　美瑛町　での　警報・注意報　を取得するサンプル](https://github.com/aktnk/weather_warnings/tree/main/samples/sample_BieiTown)

## 実行環境

下記環境にて Python 仮想環境構築＆有効化した上で、`pip install -r requirements.txt`で必要なモジュールをインストールします。

- Windows 11 Professional
- Python 3.10.5
