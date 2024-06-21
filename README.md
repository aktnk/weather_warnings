# weather_warnings

気象庁防災情報の取得

## はじめに

気象庁が XML フォーマットで気象情報を公開している。

**実現したいこと**

- 指定した市町の警報・注意報を取得し表示すること

利用にあたっては、下記に公開されている利用方法や注意事項に従う必要がある。
[気象庁防災情報 XML フォーマット形式電文の公開（PULL 型）](https://xml.kishou.go.jp/xmlpull.html)

## 実現したサンプル

- [旭川地方気象台　が公開する　美瑛町　での　警報・注意報　を取得するサンプル](https://github.com/aktnk/weather_warnings/tree/main/samples/sample_BieiTown)
- [SQLite を使って取得動作、警報・注意報出力動作を改善する](https://github.com/aktnk/weather_warnings/tree/main/samples/sample_UseDB)
