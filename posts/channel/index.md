<!-- 
.. title: Vim の channel と json のパフォーマンス
.. date: 2016-02-06 10:00 UTC+09:00
.. slug: channel
.. tags: vim
.. category: vim
.. link: 
.. description: 
.. type: text
-->

先日公開した [livemark.vim](https://github.com/miyakogi/livemark.vim) には想像以上にたくさんの反響をいただきました。
ありがとうございます。
最近では海外の方からもGithubのスターをいただきました。
思いつきで作ったプラグインでしたが、せっかくなので普段使いできるようにいくつか更新しました。

<!-- more -->

- channel をサポートしない vim では python を使うように修正
    - channelをサポートするvimでもpythonを使いたい場合は `let g:livemark_force_pysocket=1` で使えます
- マークダウンの変換及びプレビュー表示をするpythonを指定する設定追加
    - `let g:livemark_python='/path/to/python'` で指定できます
- プレビューを表示するブラウザを vim から設定できるように修正
    - `let g:livemark_browser='[ブラウザ名]'` で設定できます
    - 設定可能なブラウザと名前は[ここ](http://docs.python.jp/3/library/webbrowser.html#webbrowser.register)を参照してください
- プレビュー表示に使うポートと vim からデータを送るために使うポートの設定を追加
    - それぞれ `g:livemark_browser_port` と `g:livemark_vim_port` です
    - デフォルト値はそれぞれ 8089, 8090 です

とはいえ、まだ安定しているとは言いがたい状態なので、マークダウンのプレビューには [previm](https://github.com/kannokanno/previm) などを使うのがいいと思います。

今の実装だと変更がある度に画面全体を再描画していて大きいファイルのプレビューは厳しいので、差分だけ更新するような処理を実装中です。

そんな感じで地味に更新したりしてたのですが、[このパッチ](http://ftp.vim.org/vim/patches/7.4/7.4.1244)でchannel関係の関数名が全部変わったので動かなくなりました（つらい

![channel error](/images/channel_error.png)

修正してもまた仕様変更あったら面倒だなぁ、と微妙にやる気が減退気味だったのと、pythonでデータ送ってもそんなにもたつきを感じなかったりして「もしかして Vim の channel より python の方が速い・・・？いや channel も json も C で書かれてるしそんなはずは・・・でも Vim だし何が起きるかわからん」という疑問が沸き起こったので測ってみました。

Livemark.vim では編集中のバッファの文字列を取得して json として送っているので、

1. データをjsonに変換する処理
2. 変換されたデータをサーバーに送りつける処理

に分けて計測しました。また、Vimは一旦jsonに変換してから送る場合 (raw channel) とjsonへの変換も一気に行う場合 (json channel) の両方を測りました。

データを送りつけられるサーバーがボトルネックになると意味ないので、サーバーは Nim で書きました。 サーバーのコードはこんな感じです。

```nim
import nativesockets
import net

var server = newSocket()
let port = Port(8090)
server.bindAddr(port, "localhost")
server.listen()

while true:
  var client = newSocket()
  server.accept(client)
  echo "accepted"

  while true:
    var data = ""
    var res_client = client.recv(data, 4000)
    if res_client <= 0:
      echo "connection closed"
      client.close()
      break

server.close()
```

ベンチマークのコードはこんな感じ

```vim
scriptencoding utf-8

let s:data = readfile('data.txt')

function! s:py_eval() abort
  python <<EOF
import socket, json, vim
data = vim.eval('s:data')
EOF
endfunction

function! s:json_vim() abort
  let s:json_data = jsonencode(s:data)
endfunction

function! s:json_py() abort
  python <<EOF
json_data = json.dumps(data)
EOF
endfunction

function! s:send_data_raw() abort
  let handler = ch_open('localhost:8090', {'mode': 'raw'})
  call ch_sendraw(handler, s:json_data, 0)
  call ch_close(handler)
endfunction

function! s:send_data_py() abort
  python <<EOF
# data = json.dumps(vim.eval('s:data')).encode('utf-8')
sock = socket.create_connection(('localhost', 8090))
sock.send(json_data.encode('utf-8'))
sock.close()
EOF
endfunction

function! s:send_data_sock() abort
  let handler = ch_open('localhost:8090', {'mode': 'json'})
  call ch_sendexpr(handler, s:data, 0)
  call ch_close(handler)
endfunction

let start_time = reltime()
call s:py_eval()
echo 'py_eval:' . reltimestr(reltime(start_time))

let start_time = reltime()
call s:json_vim()
echo 'json_vim:' . reltimestr(reltime(start_time))

let start_time = reltime()
call s:json_py()
echo 'json_py:' . reltimestr(reltime(start_time))

let start_time = reltime()
call s:send_data_raw()
echo 'raw_channel:' . reltimestr(reltime(start_time))

let start_time = reltime()
call s:send_data_py()
echo 'python:' . reltimestr(reltime(start_time))

let start_time = reltime()
call s:send_data_sock()
echo 'json_channel:' . reltimestr(reltime(start_time))
```

`data.txt` には `This is sample data\n\n` が10万回、合計20万行入っています。
Pythonの場合は Vim で読み込んだデータを python に渡す処理も入ってくるので、そこは別で計測しています。

結果はこうなりました。（単位は秒、Vim のバージョンは 7.4.1265 です）

|      | vim (json) | vim (raw) | python |
|------|---------------|--------------|--------|
| vim -> py | - | - |0.165894|
| json化 | - |0.496177|0.300104|
| データ送信 | 0.488828 |0.023818|0.087396|
| 合計 | 0.488828 | 0.519995 | 0.553394 |

合計あまり変わらない・・・<s>Pythonよりは速くて「channelすごい！jsonすごい！」って記事になる予定だったのに・・・・</s>jsonのエンコードにすごい時間かかってますね・・・よく考えたら、一度Vim scriptになってるのでむしろよく頑張ってる方だと思います。
「あれ、たしかpython標準のjsonモジュールって・・・」って[などの疑問](http://postd.cc/memory-use-and-speed-of-json-parsers/)を持ってはいけません。

というわけで！Pythonで処理してもあまりパフォーマンスに影響なさそうなので！むしろ20万行のマークダウンとか書かないと思うので！channelの仕様変更に負けずに地味に更新していきたいと思います！レッツポジティブ！
