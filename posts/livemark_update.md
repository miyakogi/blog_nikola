<!-- 
.. title: Livemark.vimを色々更新しました
.. date: 2016-02-14 13:00 UTC+09:00
.. slug: livemark_update
.. tags: python, vim
.. category: vim
.. link: 
.. description: 
.. type: text
-->

Markdown文書をリアルタイムで更新するVimプラグイン、[Livemark.vim](https://github.com/miyakogi/livemark.vim)を更新しました。

`+channel`なVimじゃなくても`+python`なら動作するので、よければお試し下さい。
安定したものがいい場合は[previm](https://github.com/kannokanno/previm)などをおすすめします。

オプションはGitHubの[README](https://github.com/miyakogi/livemark.vim)に一応全て書いてあります。
まだバグがあるかもしれませんが、その時は[Issue](https://github.com/miyakogi/livemark.vim/issues)に報告していただけると喜んで対応します。Issueを書くのが面倒でしたら、Twitterで[@MiyakoDev](https://twitter.com/MiyakoDev)にメンションしていただいても大丈夫です。

<!--more-->

### 変更点

[先日の記事](http://h-miyako.hatenablog.com/entry/2016/02/06/135203)以降に追加した機能（オプション）は以下のとおりです。

- ユーザー指定のcss/jsを読み込む設定追加
- シンタックスハイライトのテーマ指定追加
- プレビュー画面のスクロール同期を止めるオプション追加

ついでに、Pythonで書かれたプレビュー用のサーバー部分を[別リポジトリ](https://github.com/miyakogi/livemark)に分離しました。
まだ分離しただけに近い状態ですが、機能を整理してドキュメントやテストを追加して、Vim以外のエディタからも使えるような形にできたらいいなぁ、と思っています。

#### CSS/JSファイルの読み込み

デフォルトでは日本語向けBootstrapテーマの[Honoka](http://honokak.osaka/)を読み込んでいます。
それに伴い、CDNからjQueryもロードしています。

ちょっと使うには十分だと思いますが、自分のブログのテーマと同じデザインで使いたいなどの希望があるだろうと考え、CSSやJSを指定できるようにしました。
パスの処理が雑なので、Windowsだと動かないかもしれません。

指定方法は、例えばCSSを追加してデフォルトのCSSを使わない場合は以下のようになります。

```vim
let g:livemark_css_files = [expand('~/dotfiles/static/css/bootstrap.ja.min.css')]
let g:livemark_no_default_css = 1
```

複数のCSSファイルを指定したい場合はそれぞれリストに追加してください。
リストに追加された順番で読み込みます。
URLを指定すれば（たぶん）Web上のリソースを読み込むこともできます。
その場合はURLを指定してください。
例えば、`let g:livemark_css_files = ['https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js']`のような感じです。

デフォルトのCSSを使用し、CSSを追加したいだけの場合は二行目は不要です。
その場合、ブラウザ上での読み込み順は デフォルトのCSS -> 追加されたCSSの順になります。

JSについても同様です。各オプションの`css`を`js`に変更してください。

#### シンタックスハイライトのテーマ設定

シンタックスハイライトには[pygments](http://pygments.org/)を使っています。
デフォルトでは特に指定していないのでpygmentsのデフォルトテーマが使われますが、他にも色々なテーマがあるので変更できるようにしました。

変更するには以下の設定をvimrcに追加してください。

```vim
let g:livemark_highlight_theme = 'テーマ名'
```

使用可能なテーマはインストールされているpygmentsに依存します。
コマンドラインで確認するには、以下のコマンドを実行して下さい。

```sh
python3 -c "import pygments.styles; print(pygments.styles.STYLE_MAP.keys())"
```

表示されたキーが利用可能なテーマ名です。
Livemarkのオプションで特定のpythonを指定している場合はpython3の部分をそちらに変えてください。

#### スクロールの同期を止めるオプションの追加

デフォルトではVimのカーソル位置に応じて画面をスクロールしています。
具体的には、Vimのバッファに表示されている最初の行が画面の最上部に来るように調整しています。

とはいえ、MarkdownからHTMLに変更する時に行番号がずれてしまうので、一応頑張って調整していますが完璧ではありません。
また、書いている時に動かない方がいい場合もあるかと思います。

ということで、以下のオプションでスクロールを停止できます。

```vim
let g:livemark_disable_scroll = 1
```

### 内部的な話

内部的にはかなり大きな変更を行いました。

当初はカーソル移動やテキストの編集が行われるたびに全文をhtmlにパースし、プレビュー画面全部を書き換えるという力技で実装されていたのですが、さすがにこれだと大きなファイルの時に描画の遅れが深刻だったので修正しました。
今は差分を検出して変更のあった部分だけを更新しています。
個人的にはJSツラいのでJSではなくPythonで処理しました。

ちょうど今[wdom](https://github.com/miyakogi/wdom_py)というPythonからブラウザ上のDOMを操作するライブラリを開発しているので、これを使ってHTMLからDOMにパースして変更箇所だけをブラウザ上で変更、という処理にしています。Livemark用のJSはスクロール用の関数を数行書いただけで、他はPythonで実装できました。変更がない時はHTMLへの変換も行わないので、カーソル移動はかなりスムーズになったと思います。

なお、このライブラリ（wdom）は絶賛開発途中です。
Livemarkにバグがあっても「まぁ、そういう時もあるよね」という温かい心で接してください。

ちなみに、wdomで目指すところはほぼJSフリーでelectron/ブラウザを使ったGUIアプリの開発です。
昨年からelectronが流行ってますけど、JSでデスクトップアプリ作りたい人だけじゃなくて、CSSフレームワーク（Bootstrapとか）のために渋々JS書いてる人も多いんじゃないの？というのが開発の動機です。
<s>つまり既存のGUIライブラリは見た目が残念・・・</s>
今はLivemarkで色々使ってみて、必要な機能の確認とバグを洗い出している感じです。
なのでまだドキュメントもありませんし、APIも変わる可能性があります。
落ち着いたらPyPIに登録して **「まだじゃわすくりぷとで消耗しているの？」** 的な煽りタイトルの記事を書きたいと思っています。
ヘタれたらもっと穏便なタイトルにするので優しくしてください。

以上です。
開発中のものを色々取り入れているのでバグがある可能性大ですが、人柱精神旺盛な方、よろしければお試しください。
