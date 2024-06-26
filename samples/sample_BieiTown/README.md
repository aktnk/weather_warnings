## 実現方法

- 警報・注意報の情報を取得するため、気象庁が公開している[高頻度フィードの随時情報](https://www.data.jma.go.jp/developer/xml/feed/extra.xml)を取得する
- 上記を情報から指定した市町の気象情報を発表している地方気象台が公開している情報を解析し、最新の警報・注意報を公開している URL を取得する
- URL から再度 XML を取得し、指定した市町の情報を確認し、該当する情報があれば表示する
- XML のダウンロード量を極力減らずため、HTTP リクエストした際に返される Last-Modified,Etag 情報を考慮したキャッシュを利用する

## 実行環境

下記環境にて Python 仮想環境構築＆有効化した上で、`pip install -r requirements.txt`で必要なモジュールをインストールします。

- Windows 11 Professional
- Python 3.10.5
