import os
from datetime import datetime

from flask import render_template, request

from run import app
from wxcloudrun import reply
from wxcloudrun.ImageAnalyser import ImageAnalyser
from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid
from wxcloudrun.model import Counters
from wxcloudrun.mylog import Mylog
from wxcloudrun.receive import ReceiveMsg, TextMsg, ImageMsg
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response
from wxcloudrun.weixin_adaptor import WeixinAdaptor

logger = Mylog()
weixin = WeixinAdaptor(logger)


@app.route('/')
def index():
    """
    :return: 返回index页面
    """
    return render_template('index.html')


@app.route('/api/count', methods=['POST'])
def count():
    """
    :return:计数结果/清除结果
    """

    # 获取请求体参数
    params = request.get_json()

    # 检查action参数
    if 'action' not in params:
        return make_err_response('缺少action参数')

    # 按照不同的action的值，进行不同的操作
    action = params['action']

    # 执行自增操作
    if action == 'inc':
        counter = query_counterbyid(1)
        if counter is None:
            counter = Counters()
            counter.id = 1
            counter.count = 1
            counter.created_at = datetime.now()
            counter.updated_at = datetime.now()
            insert_counter(counter)
        else:
            counter.id = 1
            counter.count += 2
            counter.updated_at = datetime.now()
            update_counterbyid(counter)
        return make_succ_response(counter.count)

    # 执行清0操作
    elif action == 'clear':
        delete_counterbyid(1)
        return make_succ_empty_response()

    # action参数错误
    else:
        return make_err_response('action参数错误')


@app.route('/api/count', methods=['GET'])
def get_count():
    """
    :return: 计数的值
    """
    counter = Counters.query.filter(Counters.id == 1).first()
    return make_succ_response(0) if counter is None else make_succ_response(counter.count)


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
    if recMsg is None:
        return ''

    toUser = recMsg.FromUserName
    fromUser = recMsg.ToUserName
    if isinstance(recMsg, TextMsg):
        content = recMsg.Content
        reply_content = f'回复:{content}'
        replyMsg = reply.TextMsg(toUser, fromUser, reply_content)

    elif isinstance(recMsg, ImageMsg):
        current_file_path = os.path.abspath(__file__)
        current_dir_path = os.path.dirname(current_file_path)
        image_dir = os.path.join(current_dir_path, 'image')
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
