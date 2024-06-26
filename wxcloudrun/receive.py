# -*- coding: utf-8 -*-#
# filename: receive.py
import xml.etree.ElementTree as ET


class ReceiveMsg(object):
    def __init__(self, xmlData):
        self.ToUserName = xmlData.find('ToUserName').text
        self.FromUserName = xmlData.find('FromUserName').text
        self.CreateTime = xmlData.find('CreateTime').text
        self.MsgType = xmlData.find('MsgType').text
        self.MsgId = xmlData.find('MsgId').text

    @staticmethod
    def parse_xml(web_data):
        if len(web_data) == 0:
            return None
        xmlData = ET.fromstring(web_data)
        msg_type = xmlData.find('MsgType').text
        if msg_type == 'text':
            return TextMsg(xmlData)
        elif msg_type == 'image':
            return ImageMsg(xmlData)
        else:
            return None


class TextMsg(ReceiveMsg):
    def __init__(self, xmlData):
        ReceiveMsg.__init__(self, xmlData)
        self.Content = xmlData.find('Content').text


class ImageMsg(ReceiveMsg):
    def __init__(self, xmlData):
        ReceiveMsg.__init__(self, xmlData)
        self.PicUrl = xmlData.find('PicUrl').text
        self.MediaId = xmlData.find('MediaId').text
