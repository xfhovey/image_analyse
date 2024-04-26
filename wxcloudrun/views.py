import os

from flask import request

from run import app
from wxcloudrun import weixin, reply
from wxcloudrun.ImageAnalyser import ImageAnalyser
from wxcloudrun.receive import ReceiveMsg, TextMsg, ImageMsg


@app.route('/index')
def hello_world():
    return 'Hello World!'


@app.route('/wx', methods=['GET'])
def validate():
    signature = request.args['signature']
    echostr = request.args['echostr']
    timestamp = request.args['timestamp']
    nonce = request.args['nonce']
    return weixin.validate(signature, echostr, timestamp, nonce)


@app.route('/wx', methods=['POST'])
def work():
    webData = request.data

    recMsg = ReceiveMsg.parse_xml(webData)
    toUser = recMsg.FromUserName
    fromUser = recMsg.ToUserName

    if isinstance(recMsg, TextMsg):
        content = recMsg.Content
        reply_content = f'回复:{content}'
        replyMsg = reply.TextMsg(toUser, fromUser, reply_content)

    elif isinstance(recMsg, ImageMsg):
        image_dir = os.path.join(os.getcwd(), 'image')
        image_path = weixin.get_image(recMsg, image_dir)
        analyser = ImageAnalyser(beta=-50, thresh=100)
        correct_num, wrong_num = analyser.analyse(image_path)
        text = f'正确{correct_num}道，错误{wrong_num}道'
        txtMsg = reply.TextMsg(toUser, fromUser, text)
        weixin.send_msg(txtMsg)

        file_root, file_extension = os.path.splitext(image_path)
        analysed_path = f"{file_root}_analysed{file_extension}"
        analyser.to_path(analysed_path)
        mediaId = weixin.upload_image(analysed_path)
        replyMsg = reply.ImageMsg(toUser, fromUser, mediaId)

    else:
        replyMsg = reply.TextMsg(toUser, fromUser, "无法识别的消息")

    return replyMsg.send()
