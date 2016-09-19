#-*-coding:utf-8-*-
import requests
from bs4 import BeautifulSoup
import re
from Crypto.Cipher import AES
import base64
import json
import os
import sys

reload(sys)
sys.setdefaultencoding("utf-8")

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

baseUrl = 'http://music.163.com/'

# http://music.163.com/#/discover/playlist/?order=hot&cat=%E5%85%A8%E9%83%A8&limit=35&offset=0
playlistFullUrl = baseUrl + 'discover/playlist/?order=hot&cat=全部&limit=3000&offset=0'
response = requests.get(playlistFullUrl)
# print(response.text)
soup = BeautifulSoup(response.text, "html.parser")
playlists = soup.find_all("a", class_=re.compile("tit f-thide s-fc0"))
count = 0
for playlist in playlists:
    if playlist is not None and count == 0:
        count = (count + 1)
        print count, playlist.get_text(), playlist["href"]
        songsListUrl = baseUrl + playlist["href"]
        response = requests.get(songsListUrl)
        soup = BeautifulSoup(response.text, "html.parser",from_encoding="utf-8")
        # print(response.text)

        playlist_tile = soup.find("h2", class_="f-ff2 f-brk").get_text()
        author = soup.find("div",class_="user f-cb").find("a",href=re.compile("/user/home\?id=\d+"),class_="s-fc7").get_text()
        createDate = soup.find("div",class_="user f-cb").find("span",class_="time s-fc4").get_text()
        createDate = re.compile("\d{4}-\d{2}-\d{2}").match(createDate).group().strip()
        tags = soup.find_all("a", class_="u-tag")
        tags_str = ""
        for tag in tags:
            print(tag.find("i"))
            tags_str = tags_str + tag.find("i").get_text() + ";"
        print "title&author&tags",playlist_tile,"<-->",author,"<-->",tags_str,"<-->",createDate

        playedNum = soup.find("strong", id="play-count").get_text()
        operationDiv = soup.find("div", id="content-operation")
        collectedNum = operationDiv.find("a", attrs={"data-res-action": "fav"})["data-count"]
        sharedNum = operationDiv.find("a", attrs={"data-res-action": "share"})["data-count"]
        print "playedNum&collectedNum&sharedNum",playedNum,"<-->",collectedNum,"<-->",sharedNum

        songs = soup.find_all("a", href=re.compile("/song\?id=\d+"))
        if songs is not None:
            songIndex = 0
            for song in songs:
                songIndex = (songIndex + 1)
                print(songIndex, song.get_text(), song["href"])
                songUrl = baseUrl + song["href"]
                response = requests.get(songUrl)
                soup = BeautifulSoup(response.text, "html.parser",from_encoding="utf-8")
                title = soup.find("em", class_="f-ff2").get_text()
                desDiv = soup.find_all("p", class_="des s-fc4")
                for des in desDiv:
                    s = des.find("a", href=re.compile("/artist\?id=\d+"))
                    if s is not None:
                        singer = s.get_text()
                    a = des.find("a", href=re.compile("/album\?id=\d+"))
                    if a is not None:
                        album = a.get_text()
                songId = song["href"].split('=')[1]
                commentNum = getCommentNum(songId)
                commentNum = 0
                print "songtitle&singer&album&commentNum",title, singer, album, commentNum
