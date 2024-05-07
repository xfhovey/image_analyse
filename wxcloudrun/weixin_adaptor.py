import datetime
import hashlib
import os
from urllib import request

import requests


def HttpRequest(resp_func, logger=None):
    def check_result(func):
        def wrapper(*args, **kwargs):
            response = func(*args, **kwargs)
            if response.status_code != 200:
                logger.info(response) if logger else print(response)
                return None
            res = response.json()
            print(res)
            if 'errcode' in res and res["errcode"] != 0:
                logger.info(res) if logger else print(res)
                return None

            return resp_func(res)

        return wrapper

    return check_result


class WeixinAdaptor:
    def __init__(self, logger=None):
        self.appid = 'wx2ff607a6d3522e27' #'wxd8150c294734a1d1'
        self.app_secret = 'af53e3a54f64bced04453d11af24b982' # '6198d462c3c09ae6f21c73b6eb093f77'
        self.token = '1234567890'
        self._access_token = None
        self._access_token_period = None
        self.logger = logger

    @property
    def access_token(self):
        if self._access_token is None or self._accesstoken_timeout():
            token_info = self._get_token()
            if token_info is None:
                return None
            self._access_token, expires_in = token_info
            self._access_token_period = datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
            self.logger.info(self._access_token)
        return self._access_token

    def _accesstoken_timeout(self):
        return self._access_token_period is None \
               or datetime.datetime.now() > self._access_token_period

    def validate(self, signature, echostr, timestamp, nonce):
        lst = [self.token, timestamp, nonce]
        lst.sort()
        sha1 = hashlib.sha1()
        sha1.update(lst[0].encode("utf-8"))
        sha1.update(lst[1].encode("utf-8"))
        sha1.update(lst[2].encode("utf-8"))
        hashcode = sha1.hexdigest()

        if hashcode == signature:
            return echostr
        else:
            return ""

    @HttpRequest(resp_func=lambda resp: (resp['access_token'], resp['expires_in']))
    def _get_token(self):
        url = 'https://api.weixin.qq.com/cgi-bin/token'
        params = {
            'grant_type': 'client_credential',
            'appid': self.appid,
            'secret': self.app_secret,
        }
        response = requests.get(url, params=params, verify=False)
        return response

    def get_image(self, imageMsg, local_dir):
        fromUser = imageMsg.FromUserName[0:8]
        mediaId = imageMsg.MediaId[0:8]
        picUrl = imageMsg.PicUrl
        createTime = imageMsg.CreateTime
        image_name = f'{fromUser}_{mediaId}_{createTime}.jpg'
        image_path = os.path.join(local_dir, image_name)
        request.urlretrieve(picUrl, image_path)
        return image_path

    @HttpRequest(resp_func=lambda resp: resp['media_id'])
    def upload_image(self, image_path):
        url = f'https://api.weixin.qq.com/cgi-bin/media/upload?access_token={self.access_token}&type=image'

        with open(image_path, 'rb') as f:
            files = {'media': f}
            response = requests.post(url, files=files)
        return response


    @HttpRequest(resp_func=lambda resp: resp['errcode'])
    def send_msg(self, replyMsg):
        url = f'https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token={self.access_token}'
        headers = {'content-Type': 'application/json'}
        response = requests.post(url, headers=headers, data=replyMsg.to_json())
        return response

