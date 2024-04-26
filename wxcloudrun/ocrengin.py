import base64

import pandas as pd
import requests


def get_ocr_engins():
    return {
        "baidu": BaiduOCR,
        # "tesseract": TesseractOCR,
        # "easyocr": EasyOCR
    }


#
# class EasyOCR:
#     def __init__(self):
#         pass
#
#     def identify(self, binary_image):
#         reader = easyocr.Reader(['en'])
#         results = reader.readtext(binary_image)
#         for (bbox, text, prob) in results:
#             pass
#
# class TesseractOCR:
#     def __init__(self):
#         pass
#
#     def identify(self, binary_image):
#         custom_config = r"--oem 1 --psm 1 -c tessedit_char_whitelist='0123456789+-*/÷=()'"
#         d = image_to_data(binary_image, lang='chi_sim', config=custom_config, output_type=Output.DATAFRAME)
#         return d[['text', 'left', 'top', 'width', 'height', 'probility']]


class BaiduOCR:
    def __init__(self):
        self.api_key = 'yKQWhdioXAuXtx9udEsG1zE9'
        self.secret_key = 'OFifluWbgdLHNti1wrLqqvy7MQRo5cbB'
        self._access_token = ''

    @property
    def access_token(self):
        if self._access_token == '':
            self._access_token = self.get_access_token()
        return self._access_token

    def get_access_token(self):
        url = "https://aip.baidubce.com/oauth/2.0/token"
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.api_key,
            'client_secret': self.secret_key
        }
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        response = requests.post(url, headers=headers, data=data)
        res = response.json()
        return res['access_token']

    def _identify_request(self, image_path):
        '''
        试卷分析与识别
        '''

        request_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/handwriting"
        # 二进制方式打开图片文件
        f = open(image_path, 'rb')
        img = base64.b64encode(f.read())

        params = {"image": img,
                  'recognize_granularity': 'big',
                  "probability": "true",
                  }

        request_url = request_url + "?access_token=" + self.access_token
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        response = requests.post(request_url, data=params, headers=headers)
        return response.json()

    def identify(self, image_path):
        data_list = []
        ret = self._identify_request(image_path)
        for result in ret['words_result']:
            location = result['location']
            probability = result['probability']
            data_list.append({
                'text': result['words'],
                'left': location['left'],
                'top': location['top'],
                'width': location['width'],
                'height': location['height'],
                'probability': probability['average']
            })

        df = pd.DataFrame(data_list)

        return df
