#!/usr/bin/env/ python3
# -*- coding: utf-8 -*

# *********************
__author__ = 'Frank Lv'
# *********************

"""
待完善，完善自动加入开机自启动
完善界面
"""

import asyncio
from json import dumps, loads
from os import walk, remove, listdir, rmdir, getcwd, makedirs, chmod, getlogin
from os.path import join, exists, splitext
from collections import OrderedDict
from aiohttp import ClientSession
from uvloop import EventLoopPolicy
from sys import platform
from appscript import app, mactypes
import ctypes

asyncio.set_event_loop_policy(EventLoopPolicy())


class BingPicture:
    def __init__(self):
        # bing的图片获取地址，其中n=8为获取前8张，可以根据自己的喜爱获取
        self.base_url = "https://cn.bing.com/HPImageArchive.aspx?format=js&idx=0&n=8&mkt=zh-CN"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) '
                          'Version/17.2 Safari/605.1.15'}
        # 设置不同平台对应的存储目录
        self.path = '/Users/franklv/Documents/Python/bing_python/Pic' if platform == 'darwin' else ('C:\\Users'
                                                                                                    '\\Public\\Pictures\\bingImage')
        self.database = 'data.db'

    # 请求网页，异步获取bing的数据
    async def get_img_url(self, session):
        # 设置异步http的get命令
        async with session.get(self.base_url, headers=self.headers, ssl=False) as response:
            content = await response.text()
        # 将获取的json数据转化为python的字典对象
        j = loads(content)
        img = j['images']
        # 设置为collections中的有序字典，保证获取的顺序
        url_dict = OrderedDict()
        for i in range(len(img)):
            # 获取图片的信息，保存为元组方式，其中元组的第一项为图片的信息，作为后续保存的文件名（考虑到window中无法使用/，故将其替换为空格）；
            # 第二项是图片的地址，将返回的1080P的图片替换为UHD的地址
            url_dict.update({img[i]['copyright'].replace('/', ' '): 'https://www.bing.com' + img[i]['url'].replace(
                '1920x1080', 'UHD')})
        # 修改程序所在的文件夹权限
        chmod(getcwd(), 0x0777)
        file = join(getcwd(), self.database)
        # 存储相关信息，首次文件夹中生成data.db的文件，后续判断文件存储的数据是否和获取的数据一致，如果一致不做任何操作。
        try:
            with open(file, 'r+') as f:
                url_data = f.read()
                if url_data != dumps(url_dict):
                    f.truncate(0)  # 或者使用f.seek(0, 0)和f.truncate()
                    f.write(dumps(url_dict))
        except FileNotFoundError as e:
            with open(file, 'w') as f:
                f.write(dumps(url_dict))
        return url_dict

    # 异步获取图片
    async def get_img(self, session, name, url):
        file = join(self.path, '{}.jpg'.format(name))
        # 判断文件是否存在，如果不存在就下载，如果存在不做任何操作
        if not exists(file):
            async with session.get(url, headers=self.headers, ssl=False) as response:
                content = await response.content.read()
                with open(file, 'wb') as f:
                    f.write(content)

    # 清除文件夹中空文件夹和非img_url对应的图片，即保留最新的bing上面的图片
    @staticmethod
    async def clean_dir(dirname, url_dict=None):
        if exists(dirname):
            # 遍历整个文件夹及其子文件夹
            for dir_path, dir_names, filenames in walk(dirname, topdown=False):
                # 对文件的判断，不是img_url中的文件（旧文件）进行产出操作
                for filename in filenames:
                    if splitext(filename)[0] not in url_dict.keys():
                        remove(join(dir_path, filename))
                # 对空文件夹进行删除操作
                for dir_name in dir_names:
                    dir_ = str(join(dir_path, dir_name))
                    if len(listdir(dir_)) == 0:
                        rmdir(dir_)

    # 设置不同系统的壁纸
    async def set_wallpaper(self, wallpaper_path):
        path = join(self.path, '{}.jpg'.format(wallpaper_path))
        if exists(path):
            if platform == 'darwin':
                app('Finder').desktop_picture.set(mactypes.File(path))
            else:
                ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)

    # 待完善，设置快捷方式
    async def set_shortcut(self):
        user = getlogin()
        url = f'C:\\Users\\{user}\\APPData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup'

    # 后续可以增加一个选项，让其手动更新图片，则需要get_img_url返回值不能为None
    async def main(self):
        # 如图片存储目录不存在，则会创建相应的目录
        if not exists(self.path):
            makedirs(self.path)
        async with ClientSession() as session:
            # 创建获取图片地址的task
            task1 = asyncio.create_task(self.get_img_url(session))
            url_dict = await task1
            # 创建获取图片的task序列
            tasks = [asyncio.create_task(self.get_img(session, name, url)) for name, url in url_dict.items()]
            tasks.append(asyncio.create_task(self.clean_dir(self.path, url_dict)))
            await asyncio.gather(*tasks)    # 或者使用await asyncio.wait(tasks)
            # 创建设置壁纸的task
            task2 = asyncio.create_task(self.set_wallpaper(url_dict.popitem(last=False)[0]))
            await task2


if __name__ == '__main__':
    data = BingPicture()
    asyncio.run(data.main())
