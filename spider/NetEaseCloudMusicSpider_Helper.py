#-*-coding:utf-8-*-
# Author : EricZhao

import requests
from Crypto.Cipher import AES
import base64
import json
import os
from bs4 import BeautifulSoup
import re
import time


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


def getComment(songId):
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
    return req.json()

def getCommentNum(songId):
    comment = getComment(songId)
    if comment is not None:
        return comment["total"]
    else:
        return False




def isPlayListExist(dbHelper, title):
    # 注意 用 %() 来给参数赋值 的方式需要在给sql这种的字符串手动加上单引号,如果是用params的方式则不需要
    sql = "select rowid from playlist_info where title =%s"
    param = (title)
    rs = dbHelper.query_one(sql,param)
    # print rs
    if rs is not None:
        # print rs["rowid"]
        return rs["rowid"]
    else :
        return 0

def isSongExist(dbHelper, title):
    # 注意 用 %() 来给参数赋值 的方式需要在给sql这种的字符串手动加上单引号,如果是用params的方式则不需要
    sql = "select rowid from song_info where title =%s"
    param = (title)
    rs = dbHelper.query_one(sql, param)
    # print rs
    if rs is not None:
        # print rs["rowid"]
        return rs["rowid"]
    else:
        return 0



def savePlayListInfo(dbHelper,playlistUrl):
    # print playlist_href
    if playlistUrl is None:
        return None

    effectedRows = 0
    playlist_rowid = 0

    response = requests.get(playlistUrl)
    # print(response.text)
    soup = BeautifulSoup(response.text, "html.parser")

    try:
        # put playlist info into db
        playlist_tile = soup.find("h2", class_="f-ff2 f-brk").get_text().encode("utf-8").strip()
        author = soup.find("div", class_="user f-cb").find("a", href=re.compile("/user/home\?id=\d+"),
                                                           class_="s-fc7").get_text().encode("utf-8").strip()
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

        if isPlayListExist(dbHelper, playlist_tile) == 0:
            insertSql = "insert into playlist_info(title,description,author,create_date,tag,played_num,operatedate,collected_num,shared_num) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            params = (
            playlist_tile, description, author, createDate, tags_str, playedNum, curTime, collectedNum, sharedNum)
            effectedRows = dbHelper.insert_update_delete(insertSql, params)
            dbHelper.commit()

            if effectedRows > 0:
                playlist_rowid = isPlayListExist(dbHelper, playlist_tile)
    except Exception as e:
        print e
    finally:
        dbHelper.close()

    songs = soup.find_all("a", href=re.compile("/song\?id=\d+"))
    return effectedRows,playlist_rowid,songs



def saveSongInfo(dbHelper,songUrl, songId,playlist_rowid):
    if songUrl is None:
        return 0

    effectedRows = 0

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
    commentNum = getCommentNum(songId)
    print "songtitle&singer&album&commentNum", title, singer, album, commentNum

    try:
        # save song info into db
        # if NetEaseCloudMusicSpider_Helper.isSongExist(dbHelper,title) == 0:
        if True:
            if playlist_rowid > 0:
                insertSql = "insert into song_info(title,singer,album,comment_num,playlist_id) values (%s,%s,%s,%s,%s)"
                params = (title, singer, album, commentNum, playlist_rowid)
            else:
                insertSql = "insert into song_info(title,singer,album,comment_num) values (%s,%s,%s,%s)"
                params = (title, singer, album, commentNum)
            effectedRows = dbHelper.insert_update_delete(insertSql, params)
            dbHelper.commit()
    except Exception as e:
        print e
    finally:
        dbHelper.close()
    return effectedRows