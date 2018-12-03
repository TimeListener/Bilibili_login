# -*-coding:utf-8 -*-
import datetime
import json
import pymongo
import random
import re
import time
import urllib.parse
from urllib.request import urlretrieve
import requests
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys

from packages.setting import *
from bs4 import BeautifulSoup
import PIL.Image as image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class Crack(object):
    def __init__(self):
        self.url = LOGIN_URL
        self.options = Options()
        self.options.add_argument('--headless')
        self.options.add_argument('--disable-gpu')
        self.browser = webdriver.Chrome(chrome_options=self.options)
        self.wait = WebDriverWait(self.browser, 30)
        self.username = USERNAME
        self.password = PASSWORD
        self.BORDER = 6
        self.client = pymongo.MongoClient(host='127.0.0.1')
        self.mydb = self.client['Bilibili']
        self.mycol = self.mydb['Luck']
        self.rid_list = self.read_rid_and_uid()['rid']
        self.uid_list = self.read_rid_and_uid()['uid']

    def open(self):
        """
        打开B站登录,并输入账号密码
        """
        try:
            self.browser.get(self.url)
            username = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#login-username'))
            )
            password = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#login-passwd'))
            )
            verify = self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '#gc-box > div > div.gt_slider > div.gt_ajax_tip.gt_ready'))
            )
            username.clear()
            username.send_keys(self.username)
            password.clear()
            password.send_keys(self.password)
            verify.click()
        except TimeoutException:
            print('Open ERROR')

    def get_images(self, bg_filename='bg.jpg', fullbg_filename='fullbg.jpg'):
        """
        获取验证码图片
        :return: 图片的location信息
        """
        bg = []
        fullgb = []
        while bg == [] and fullgb == []:
            bf = BeautifulSoup(self.browser.page_source, 'lxml')

            bg = bf.find_all('div', class_='gt_cut_bg_slice')
            fullgb = bf.find_all('div', class_='gt_cut_fullbg_slice')
        bg_url = re.findall('url\(\"(.*)\"\);', bg[0].get('style'))[0].replace('webp', 'jpg')
        fullgb_url = re.findall('url\(\"(.*)\"\);', fullgb[0].get('style'))[0].replace('webp', 'jpg')
        bg_location_list = []
        fullbg_location_list = []
        for each_bg in bg:
            location = {}
            location['x'] = int(re.findall('background-position: (.*)px (.*)px;', each_bg.get('style'))[0][0])
            location['y'] = int(re.findall('background-position: (.*)px (.*)px;', each_bg.get('style'))[0][1])
            bg_location_list.append(location)
        for each_fullgb in fullgb:
            location = {}
            location['x'] = int(re.findall('background-position: (.*)px (.*)px;', each_fullgb.get('style'))[0][0])
            location['y'] = int(re.findall('background-position: (.*)px (.*)px;', each_fullgb.get('style'))[0][1])
            fullbg_location_list.append(location)

        urlretrieve(url=bg_url, filename=bg_filename)
        print('缺口图片下载完成')
        urlretrieve(url=fullgb_url, filename=fullbg_filename)
        print('背景图片下载完成')
        return bg_location_list, fullbg_location_list

    def get_merge_image(self, filename, location_list):
        """
        根据位置对图片进行合并还原
        :filename:图片
        :location_list:图片位置
        """
        im = image.open(filename)
        new_im = image.new('RGB', (260, 116))
        im_list_upper = []
        im_list_down = []

        for location in location_list:
            if location['y'] == -58:
                im_list_upper.append(im.crop((abs(location['x']), 58, abs(location['x']) + 10, 166)))
            if location['y'] == 0:
                im_list_down.append(im.crop((abs(location['x']), 0, abs(location['x']) + 10, 58)))

        new_im = image.new('RGB', (260, 116))

        x_offset = 0
        for im in im_list_upper:
            new_im.paste(im, (x_offset, 0))
            x_offset += im.size[0]

        x_offset = 0
        for im in im_list_down:
            new_im.paste(im, (x_offset, 58))
            x_offset += im.size[0]

        new_im.save(filename)

        return new_im

    def is_pixel_equal(self, img1, img2, x, y):
        """
        判断两个像素是否相同
        :param image1: 图片1
        :param image2: 图片2
        :param x: 位置x
        :param y: 位置y
        :return: 像素是否相同
        """
        # 取两个图片的像素点
        pix1 = img1.load()[x, y]
        pix2 = img2.load()[x, y]
        threshold = 60
        if (abs(pix1[0] - pix2[0] < threshold) and abs(pix1[1] - pix2[1] < threshold) and abs(
                pix1[2] - pix2[2] < threshold)):
            return True
        else:
            return False

    def get_gap(self, img1, img2):
        """
        获取缺口偏移量
        :param img1: 不带缺口图片
        :param img2: 带缺口图片
        :return:
        """
        left = 43
        for i in range(left, img1.size[0]):
            for j in range(img1.size[1]):
                if not self.is_pixel_equal(img1, img2, i, j):
                    left = i
                    return left
        return left

    def get_track(self, distance):
        """
         模拟人为滑块移动, 即变加速运动.
         :param distance: 图片缺口距离.
         :return: 滑动轨迹列表.
         """
        # 增加distance使得距离加大，之后我们再将distance矫正，以达到模拟人操作
        inc_distance = distance + distance / 5
        # 移动轨迹
        track_1 = []
        track_2 = []
        # 当前位移
        current = 0
        # 减速阈值
        mid = inc_distance * 4 / 5
        # 计算间隔
        t = 0.2
        # 初速度
        v = 0

        while current < inc_distance:
            if current < mid:
                # 加速度为正2
                a = random.uniform(0, 3)
            else:
                # 加速度为负3
                a = random.uniform(-1, -3)
            # 初速度v0
            v0 = v
            # 当前速度v = v0 + at
            v = v0 + a * t
            # 移动距离x = v0t + 1/2 * a * t^2
            move = v0 * t + 1 / 2 * a * t * t
            # 当前位移
            current += move
            # 加入轨迹
            track_1.append(round(move))

        offset = distance / 5
        current = -1
        mid = offset * 4 / 5
        t = 0.2
        v = 0
        while current < offset:
            if current < mid:
                # 加速度为正2
                a = random.uniform(0, 3)
            else:
                # 加速度为负3
                a = random.uniform(-1, -3)
            # 初速度v0
            v0 = v
            # 当前速度v = v0 + at
            v = v0 - a * t
            # 移动距离x = v0t + 1/2 * a * t^2
            move = v0 * t - 1 / 2 * a * t * t
            # 当前位移
            current -= move
            # 加入轨迹
            track_2.append(round(move))

        return {'inc': track_1, 'offset': track_2}

    def get_slider(self):
        """
        获取滑块
        :return: 滑块对象
        """
        while True:
            try:
                slider = self.wait.until(
                    EC.visibility_of_element_located(((By.XPATH, "//div[@class='gt_slider_knob gt_show']")))
                )
                break
            except:
                time.sleep(0.5)
        return slider

    def move_to_gap(self, slider, track):
        """
        拖动滑块到缺口处
        :param slider: 滑块
        :param track: 轨迹
        :return:
        """
        ActionChains(self.browser).click_and_hold(slider).perform()
        while len(track['inc']):
            x = random.choice(track['inc'])
            ActionChains(self.browser).move_by_offset(xoffset=x, yoffset=0).perform()
            track['inc'].remove(x)
        time.sleep(0.5)
        while len(track['offset']):
            x = random.choice(track['offset'])
            ActionChains(self.browser).move_by_offset(xoffset=x, yoffset=0).perform()
            track['offset'].remove(x)
        time.sleep(0.5)
        ActionChains(self.browser).release().perform()

     # 数据保存到MongoDB，注意查重
    def client_mongodb(self, content, num):
        # 去重操作，数据库如果已经相同的rid则不进行添加
        flag = 1
        for con in self.mycol.find({}, {'rid': 1}):
            if con['rid'] == content['rid']:
                print('$$$$$$$$$<(￣︶￣)>已经参与过抽奖<(￣︶￣)>$$$$$$$$$$$$')
                print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
                flag = 0
                break
        if flag == 1:
            self.repost(num)

        self.mycol.update(
            {'rid': content['rid']},
            {'$set': {'rid': content['rid'], 'like': content['like'], 'is_attention': content['is_attention'],
                      'repost': content['repost'], 'uid': content['uid'], 'uname': content['uname'],
                      'image': content['image'], 'view': content['view'], 'TIME': content['TIME'],
                      'prize_url': content['prize_url']}},
            multi=True, upsert=True
        )
        self.client.close()

        # 获取抽奖动态最热18条动态的相关信息，返回HTML

    def get_html(self):
        header = {
            'user-agent': 'Baiduspider+'
        }
        data = {
            "topic_name": "转发抽奖"
        }
        # 构建Request URL
        request_url = 'https://api.vc.bilibili.com/topic_svr/v1/topic_svr/topic_new?' + urllib.parse.urlencode(
            data)
        r = requests.get(request_url, headers=header)
        if r.status_code == 200:
            r.encoding = 'utf-8'
            return r.text
        else:
            print('get_information ERROR: ' + r.status_code)
            return None

        # 解析get_html()返回的html

    def get_information(self, htl):
        htl = json.loads(htl)
        if 'data' in htl.keys():
            # items 为字典
            for items in htl.get('data').get('cards')[1:19]:
                yield {
                    'rid': items['desc']['rid'],
                    "like": items['desc']['like'],
                    'is_attention': items['desc']['recommend_info']['is_attention'],
                    'repost': items['desc']['repost'],
                    'uid': items['desc']['uid'],
                    'uname': items['desc']['user_profile']['info']['uname'],
                    'image': items['desc']['user_profile']['info']['face'],
                    'view': items['desc']['view'],
                    'TIME': datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S'),
                    'prize_url': 'https://h.bilibili.com/{}'.format(str(items['desc']['rid']) if
                                                                    items['desc']['rid'] <= 9999999999999999 else (
                            str(items['desc']['rid']) + "?tab=1"))
                }

        # 保存数据的主程序

    def save_content(self):
        num = 0
        print('\n')
        print('+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
        print('（◕(ｪ)◕）抽（◕(ｪ)◕）奖（◕(ｪ)◕）界（◕(ｪ)◕）面（◕(ｪ)◕）')
        print('+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
        print('\n')
        htl = self.get_html()

        for item in self.get_information(htl):
            if item['uid'] not in self.uid_list:
                self.attention(num + 5)
                print('UID:{},已经关注！'.format(item['uid']))
            else:
                print('\n')
                print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
                print('$$$$$$$$ㄟ( ▔, ▔ )ㄏ UID:{},关注过啦 ㄟ( ▔, ▔ )ㄏ$$$$$$$$$'.format(item['uid']))
            self.client_mongodb(item, num + 5)
            num = num + 1

        # 返回一个数据库中由rid和uid组成的字典
        # {'rid':[xxx, xxx, xxx] , 'uid':[xxx, xxx, xxx]}

    def read_rid_and_uid(self):
        rid_list = []
        uid_list = []
        for dit in self.mycol.find({}, {'rid': 1}):
            rid_list.append(dit['rid'])
        for dit in self.mycol.find({}, {'uid': 1}):
            uid_list.append(dit['uid'])

        return {'rid': rid_list, 'uid': uid_list}

        # 进行关注动作

    def attention(self, num):
        try:
            # 开始定位UP主抽奖动态的“+关注”按键
            uper = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR,
                                            '#app > div.change-content > div.feed-wrap > div > div:nth-child({}) > div.focus-btn.p-abs.c-pointer > div > p'.format(
                                                num)))
            )
            # 进行点击操作，完成关注
            uper.click()

            print('ㄟㄟㄟㄟㄟㄟㄟㄟ( =∩ω∩= ) 关注成功( =∩ω∩= ) ㄏㄏㄏㄏㄏㄏㄏㄏㄏㄏ')
            print('\n')
        except NoSuchElementException:
            print('ㄟ( ▔, ▔ )ㄏ关注过啦ㄟ( ▔, ▔ )ㄏ')

        # 进行转发动作

    def repost(self, num):
        try:
            # 分享按钮
            share = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, SHARE_LOCATION.format(num=num)))
            )
            share.click()
            print('   (✿✪‿✪｡)ﾉ点击分享(✿✪‿✪｡)ﾉ')
            print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')

            like = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, LIKE_LOCATION.format(num=num)))
            )
            like.click()

            # 分享评论框
            frame = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, COMMENT_LOCATION.format(num=num)))
            )
            frame.clear()
            # 输入你要@的内容，注意：在输入"@"后接你要@的人时要稍等一会儿，否则网站反应不过来，那么你的“@XXXX”内容只会做普通的字符
            # 起不到@人的作用
            frame.send_keys('@{string}'.format(string=random.choice(WORD)))
            time.sleep(2)
            frame.send_keys(Keys.ENTER)
            frame.send_keys('@{string}'.format(string=random.choice(WORD)))
            time.sleep(3)
            frame.send_keys(Keys.ENTER)
            frame.send_keys('@{string}'.format(string=random.choice(WORD)))
            time.sleep(2)
            frame.send_keys(Keys.ENTER)
            frame.send_keys('@{string}'.format(string=random.choice(WORD)))
            time.sleep(2)
            frame.send_keys(Keys.ENTER)
            frame.send_keys(
                random.choice(['万一中了呢~｡◕‿◕｡', '试一试~罒ω罒', '不抽奖难受(っ °Д °;)っ', '在爽一次', '再爽一次']))

            # 提交“转发”
            submit = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, SUBMIT_LOCATION.format(num=num)))
            )
            submit.click()
            print('｡◕‿◕｡参与抽奖成功｡◕‿◕｡~')
        except TimeoutException as EXC:
            print('Repost ERROR!')
            print(EXC)

    def crack(self):
        # 打开浏览器
        self.open()

        # 保存的图片名字
        bg_filename = 'bg.jpg'
        fullbg_filename = 'fullbg.jpg'

        # 获取图片
        bg_location_list, fullbg_location_list = self.get_images(bg_filename, fullbg_filename)

        # 根据位置对图片进行合并还原
        bg_img = self.get_merge_image(bg_filename, bg_location_list)
        fullbg_img = self.get_merge_image(fullbg_filename, fullbg_location_list)

        # 获取缺口位置
        gap = self.get_gap(fullbg_img, bg_img)
        print('缺口位置', gap)

        track = self.get_track(gap - self.BORDER)
        print('滑动滑块')
        print(track)

        # 点按呼出缺口
        slider = self.get_slider()
        # 拖动滑块到缺口处
        self.move_to_gap(slider, track)
        time.sleep(2)
        self.browser.get(PRIZE_URL)
        print(self.browser.current_url)
        while True:
            try:
                try:
                    judge = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, JUDGE))
                    )
                    break
                except NoSuchElementException:
                    print('-' * 15 + '登录失败，3s后重新登录' + '-' * 15)
                    time.sleep(3)
                    self.crack()
            except TimeoutException:
                print('-' * 15 + '登录失败，3s后重新登录' + '-' * 15)
                time.sleep(3)
                self.crack()
        time.sleep(1)
        print('***************************************************')
        print('**********"o((#`O′)o"登陆成功"o((#`O′)o"*********')
        print('***************************************************')
        self.save_content()
        self.browser.quit()


if __name__ == '__main__':
    print('***************************************************')
    print('**********"o((>ω< ))o"开始"o((>ω< ))o"***********')
    print('***************************************************')
    crack = Crack()
    crack.crack()
