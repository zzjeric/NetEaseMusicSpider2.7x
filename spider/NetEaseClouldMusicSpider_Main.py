#!/usr/bin/env python
#-*-coding:utf-8-*-
# Author : EricZhao

import requests
from bs4 import BeautifulSoup
import re
from time import sleep
import DbHelper
import NetEaseCloudMusicSpider_Helper




baseUrl = 'http://music.163.com/'
dbHelper = DbHelper.DBHelper()
dbHelper.connect()

# 抓取热门歌单(从1到42页)
for i in range(0,41):
    # http://music.163.com/#/discover/playlist/?order=hot&cat=%E5%85%A8%E9%83%A8&limit=35&offset=0
    playlistFullUrl = baseUrl + 'discover/playlist/?order=hot&cat=全部&limit=35&offset='+str(i*35)
    response = requests.get(playlistFullUrl)
    # print(response.text)
    soup = BeautifulSoup(response.text, "html.parser")
    playlists = soup.find_all("a", class_=re.compile("tit f-thide s-fc0"))
    count = 0
    # 遍历歌单
    for playlist in playlists:
        if playlist is not None:
            count = (count + 1)
            # 因为同一个IP短时间频繁请求服务器会导致服务器拒绝链接,所以每取10个歌单就休息五分钟
            if count%10 == 0:
                sleep(300)
            else:
                # 解析并保存歌单信息
                playListUrl = baseUrl + playlist["href"]
                rtn = NetEaseCloudMusicSpider_Helper.savePlayListInfo(dbHelper,playListUrl)
                if rtn is None:
                    continue
                effectedRows = rtn[0]
                print "插入第" + str(count) + "条歌单信息,操作结果为-->" + str(effectedRows)
                print count, playlist.get_text(), playlist["href"]

                # 遍历歌单里的歌曲
                playlist_rowid = rtn[1]
                songs = rtn[2]
                if songs is not None:
                    songIndex = 0
                    for song in songs:
                        songIndex = (songIndex + 1)

                        # 解析并保存歌曲信息
                        print songIndex, song.get_text(), song["href"]
                        songUrl = baseUrl + song["href"]
                        songId = song["href"].split('=')[1]
                        rtn = NetEaseCloudMusicSpider_Helper.saveSongInfo(dbHelper, songUrl, songId,playlist_rowid)
                        if rtn is None :
                            continue
                        print "插入第" + str(songIndex) + "条歌曲信息,操作结果为-->" + str(rtn)
# close db connection
dbHelper.close()

