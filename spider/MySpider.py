#-*-coding:utf-8-*-
import requests
from bs4 import BeautifulSoup
import re
import pymysql.cursors
import time
from Crypto.Cipher import AES
import base64
import json
import os
from time import sleep


def aesEncrypt(text, secKey):
    pad = 16 - len(text) % 16
    text = text + pad * chr(pad)
    encryptor = AES.new(secKey, 2, '0102030405060708')
    ciphertext = encryptor.encrypt(text)
    ciphertext = base64.b64encode(ciphertext)
    return ciphertext


def rsaEncrypt(text, pubKey, modulus):
    text = text[::-1]
    rs = int(text.encode('hex'), 16) ** int(pubKey, 16) % int(modulus, 16)
    return format(rs, 'x').zfill(256)


def createSecretKey(size):
    return (''.join(map(lambda xx: (hex(ord(xx))[2:]), os.urandom(size))))[0:16]


def getCommentNum(songId):
    url = 'http://music.163.com/weapi/v1/resource/comments/R_SO_4_' + \
        str(songId) + '/?csrf_token='
    headers = {
        'Cookie': 'appver=1.5.0.75771;',
        'Referer': 'http://music.163.com/'}
    text = {'username': '', 'password': '', 'rememberLogin': 'true'}
    modulus = '00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7'
    nonce = '0CoJUm6Qyw8W8jud'
    pubKey = '010001'
    text = json.dumps(text)
    secKey = createSecretKey(16)
    encText = aesEncrypt(aesEncrypt(text, nonce), secKey)
    encSecKey = rsaEncrypt(secKey, pubKey, modulus)
    data = {'params': encText, 'encSecKey': encSecKey}
    req = requests.post(url, headers=headers, data=data)
    total = req.json()['total']
    return total


def isPlayListExist(title):
    # 注意 用 %() 来给参数赋值 的方式需要在给sql这种的字符串手动加上单引号,如果是用params的方式则不需要
    sql = "select rowid from playlist_info where title ='%s'" % title
    with conn.cursor() as cursor:
        cursor.execute(sql)
        rs = cursor.fetchone()
        # print rs
        if rs is not None:
            # print rs["rowid"]
            return rs["rowid"]
        else :
            return 0

def isSongExist(title):
    # 注意 用 %() 来给参数赋值 的方式需要在给sql这种的字符串手动加上单引号,如果是用params的方式则不需要
    sql = "select rowid from song_info where title ='%s'" % title
    with conn.cursor() as cursor:
        cursor.execute(sql)
        rs = cursor.fetchone()
        # print rs
        if rs is not None:
            # print rs["rowid"]
            return rs["rowid"]
        else :
            return 0

baseUrl = 'http://music.163.com/'
conn = pymysql.connect(host='127.0.0.1',
                       port=3306,
                       user='root',
                       password='11111',
                       db='python_test',
                       charset='utf8',
                       cursorclass=pymysql.cursors.DictCursor)

for i in range(0,41):
    # http://music.163.com/#/discover/playlist/?order=hot&cat=%E5%85%A8%E9%83%A8&limit=35&offset=0
    playlistFullUrl = baseUrl + 'discover/playlist/?order=hot&cat=全部&limit=35&offset='+str(i*35)
    response = requests.get(playlistFullUrl)
    # print(response.text)
    soup = BeautifulSoup(response.text, "html.parser")
    playlists = soup.find_all("a", class_=re.compile("tit f-thide s-fc0"))
    count = 0
    fout = open("output.html", "w")
    fout.write("<html>")
    fout.write("<head><meta http-equiv='content-type' content='text/html;charset=utf-8'></head>")
    fout.write("<body>")
    fout.write("<table border='1px' cellspacing='0px'>")
    for playlist in playlists:
        if playlist is not None:
            count = (count + 1)
            # 因为同一个IP短时间频繁请求服务器会导致服务器拒绝链接,所以每取10个歌单就休息五分钟
            if count%10 == 0:
                sleep(300)
            else:
                print count, playlist.get_text(), playlist["href"]
                fout.write("<tr>")
                fout.write("<td>")
                # fout.write("".join([str(count), "    ", playlist.get_text()]))
                fout.write("" + str(count) + "    " + playlist.get_text().encode("utf-8"))
                fout.write("</td>")
                songsListUrl = baseUrl + playlist["href"]
                response = requests.get(songsListUrl)
                # print(response.text)
                soup = BeautifulSoup(response.text, "html.parser")

                playlist_rowid = 0

                try:
                    # put playlist info into db
                    playlist_tile = soup.find("h2", class_="f-ff2 f-brk").get_text().encode("utf-8").strip()
                    author = soup.find("div", class_="user f-cb").find("a", href=re.compile("/user/home\?id=\d+"),
                                                                       class_="s-fc7").get_text().encode(
                        "utf-8").strip()
                    tags = soup.find_all("a", class_="u-tag")
                    tags_str = ""
                    for tag in tags:
                        print tag.find("i")
                        tags_str = tags_str + tag.find("i").get_text() + ";"
                    description = soup.find("p", id="album-desc-more").get_text().encode("utf-8").strip()
                    createDate = soup.find("div", class_="user f-cb").find("span", class_="time s-fc4").get_text()
                    createDate = re.compile("\d{4}-\d{2}-\d{2}").match(createDate).group().strip()

                    playedNum = soup.find("strong", id="play-count").get_text()

                    operationDiv = soup.find("div", id="content-operation")
                    collectedNum = operationDiv.find("a", attrs={"data-res-action": "fav"})["data-count"]
                    sharedNum = operationDiv.find("a", attrs={"data-res-action": "share"})["data-count"]

                    curTime = time.strftime('%Y-%m-%d', time.localtime(time.time()))

                    if isPlayListExist(playlist_tile) == 0:
                        insertSql = "insert into playlist_info(title,description,author,create_date,tag,played_num,operatedate,collected_num,shared_num) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                        params = (
                        playlist_tile, description, author, createDate, tags_str, playedNum, curTime, collectedNum,
                        sharedNum)
                        # 获取cursor
                        with conn.cursor() as cursor:
                            effectedRows = cursor.execute(insertSql, params)
                            conn.commit()
                            print "插入第" + str(count) + "条歌单信息,操作结果为-->" + str(effectedRows)
                            if effectedRows > 0:
                                playlist_rowid = isPlayListExist(playlist_tile)
                except Exception as e:
                    print e

                songs = soup.find_all("a", href=re.compile("/song\?id=\d+"))
                if songs is not None:
                    songIndex = 0
                    fout.write("<td>")
                    for song in songs:
                        songIndex = (songIndex + 1)
                        print songIndex, song.get_text(), song["href"]
                        songUrl = baseUrl + song["href"]
                        response = requests.get(songUrl)
                        soup = BeautifulSoup(response.text, "html.parser")
                        title = soup.find("em", class_="f-ff2").get_text().encode("utf-8").strip()
                        desDiv = soup.find_all("p", class_="des s-fc4")
                        singer = ""
                        album = ""
                        for des in desDiv:
                            s = des.find("a", href=re.compile("/artist\?id=\d+"))
                            if s is not None:
                                singer = s.get_text().encode("utf-8").strip()
                            a = des.find("a", href=re.compile("/album\?id=\d+"))
                            if a is not None:
                                album = a.get_text().encode("utf-8").strip()
                        songId = song["href"].split('=')[1]
                        commentNum = getCommentNum(songId)
                        print "songtitle&singer&album&commentNum", title, singer, album, commentNum
                        # fout.write("".join([str(songIndex), "    ", song.get_text(), "</br>"]))
                        fout.write(str(songIndex) + "    " + song.get_text().encode("utf-8") + "</br>")

                        try:
                            # put song info into db
                            # if isSongExist(title) == 0:
                            if True:
                                if playlist_rowid > 0:
                                    insertSql = "insert into song_info(title,singer,album,comment_num,playlist_id) values (%s,%s,%s,%s,%s)"
                                    params = (title, singer, album, commentNum, playlist_rowid)
                                else:
                                    insertSql = "insert into song_info(title,singer,album,comment_num) values (%s,%s,%s,%s)"
                                    params = (title, singer, album, commentNum)
                                # 获取cursor
                                with conn.cursor() as cursor:
                                    effectedRows = cursor.execute(insertSql, params)
                                    conn.commit()
                                    print "插入第" + str(songIndex) + "条歌曲信息,操作结果为-->" + str(effectedRows)
                        except Exception as e:
                            print e
                            # fout.write(song.get_text())

                    fout.write("</td>")
                fout.write("</tr>")
    fout.write("</table>")
    fout.write("</body>")
    fout.write("</html>")
    fout.close()

conn.close()



