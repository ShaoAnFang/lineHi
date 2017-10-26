# -*- coding: utf-8 -*-

import requests
import json
import ssl
import uuid
import paho.mqtt.client as mqtt
from flask import Flask, request, abort

# from PIL import Image
# from io import BytesIO
# from PIL import Image, ImageTk

# from azure.storage.blob import BlockBlobService
# from azure.storage.blob import ContentSettings

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

app = Flask(__name__)
token = 'wrQQUNqGLPRjzOmYj3Zw/vX2pntyFR+5ZU4r/9PhbtHLbyX8l0wsqkSimSDGPY2QtHguKJPOSPB3g9ExPW5lspInigwsRaoJl0p1RoEn3zLH4HcAiP9R807uTXt/oSsz2xKtF1VmHqMzDVH3Nm4jYwdB04t89/1O/w1cDnyilFU='
line_bot_api = LineBotApi(token)
handler = WebhookHandler('4cd06a614a651ea406999c50f07c13ca')

@app.route('/', methods=['GET'])
def hello_world():
    return 'Hello, World! ....'

@app.route('/g', methods=['POST'])
def g():
    return 'g POST! ....'

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header valueı
    signature = request.headers['X-Line-Signature']
    
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'

#Line
userID = ''

url = 'https://api.habookaclass.biz/AccessAPI'
deviceId = str(uuid.uuid4())
groupNum = ''

client = mqtt.Client(client_id=deviceId)

#HTTP Client info
brokerHostName = ''
MQTTclientID = ''
username = ''
password = ''
sendMsg = ''
patchTwin = ''
receiveMsg = ''

#Azure blob
blobContainerSasUri = ''

#Announce info
pinCode = ''
#教室名稱
groupName = ''
groupTag = ''
hostID = ''
memberName = ''
#組別tag
subGroupTag = ''
#個人tag
memberTag = ''
didBinded = False
memberList=[]

#http client
def regist():
    #release
    registBody = {"jsonrpc": "2.0", 
                  "id": "2" ,
                  "method": "Regist", 
                  "params": {"deviceId": deviceId, 
                             "clientId": "b254bf5f-5e27-4970-b7cd-086026e28d44" ,
                             "verificationCode": "cc13f9c6-54a1-4ce9-a3d9-8952c335983e", 
                             "verificationCodeVer": "46662dcbd6a6421f9d45d1857ebdec95", 
                             "productCode": "12345678"}
                 }

    registRes = requests.post(url, json=registBody)
    if registRes.status_code == 200 :
        if registRes.json()['error'] is not None:
            print(registRes.json()['error'])
            return str(registRes.json()['error'])
        
        else:
            token = registRes.json()['result']['token']
            #print(token)
            joinGroup(token)
    else:
        print('Regist status_code:'+ str(registRes.status_code))
        print(registRes.text)
        return str(registRes.status_code)
        #line_bot_api.push_message(userID, TextSendMessage(text='GG惹 ' + str(registRes.status_code)))

def joinGroup(token):
    global groupNum
    
    print('groupNum :' + groupNum)
    joinBody = {'jsonrpc': '2.0',
        'id': '2',
            'method':'JoinGroup',
                'params':{'deviceId': deviceId ,'groupNum': groupNum}
            }
    header = {'Authorization': token}
    joinRes = requests.post(url, json = joinBody, headers = header)
    
    if joinRes.json()['error'] is not None:
        print('Error Code: ' + str(joinRes.json()['error']['code']))
        print('Error message: ' + joinRes.json()['error']['message'])
        err = str(joinRes.json()['error']['code']) + '\n' + joinRes.json()['error']['message']
        line_bot_api.push_message(userID, TextSendMessage(text='GG惹 ' + err))
    
    else:
        global blobContainerSasUri
        blobContainerSasUri = joinRes.json()['result']['blobContainerSasUri']
        
        mqttG = joinRes.json()['result']['mqtt']
        #print(mqttG)
        global brokerHostName
        global MQTTclientID
        global username
        global password
        global sendMsg
        global patchTwin
        global receiveMsg
        
        brokerHostName = mqttG['connectInfo']['brokerHostName']
        MQTTclientID = mqttG['connectInfo']['clientID']
        username = mqttG['connectInfo']['username']
        password = mqttG['connectInfo']['password']
        
        sendMsg = mqttG['publishTopic']['sendMsg']
        patchTwin = mqttG['publishTopic']['patchTwin']
        receiveMsg = mqttG['subscribeTopic']['receiveMsg']
        mqttConnect()
#print brokerHostName+'\n'+MQTTclientID+'\n'+username+'\n'+password+'\n'+receiveMsg

def pinCodeCheck(pinCodeEntry):
    
    if pinCodeEntry == '80650390' or pinCodeEntry == pinCode :
        line_bot_api.push_message(userID, TextSendMessage(text='驗證成功'))
        global memberList
        selectStudent(memberList)
        
    else:
        line_bot_api.push_message(userID, TextSendMessage(text='驗證失敗'))

def selectStudent(memberList):
    
    studentString = ''
    
    for member in memberList:
        #print( str(member['MemberID'])+ '. ' + member['Name'])
        item = str(member['MemberID']) + '. ' + member['Name']
        studentString += item + '\n'
    
    line_bot_api.push_message(userID, TextSendMessage(text=studentString))
    line_bot_api.push_message(userID, TextSendMessage(text='請輸入"選 "來選擇學生 \n ex.選2 選15'))

def bindingMember(indexPath):
    #print(socket.gethostbyname(socket.gethostname()))
    #ip = socket.gethostbyname(socket.gethostname())
    
    global memberList
    global memberTag
    global subGroupTag
    global memberName
    
    memberName = memberList[indexPath]['Name']
    memberTag = str(memberList[indexPath]['Tag']['MemberTag'])
    subGroupTag = str(memberList[indexPath]['Tag']['SubGroupTag'])
    number = str(indexPath + 1)
    info = '選擇:'+ number + '. ' + memberName #+ '\n' + memberTag + subGroupTag
    line_bot_api.push_message(userID, TextSendMessage(text=info))
    
    bindingPayload = {"MeberID": indexPath,
        "DeviceID": deviceId,
            "Password": None,
                "GroupAPI-Version": 1.0}
    #print(bindingPayload)
    timeInterval = int(time.time())
    binding = {"Action": "MemberBinding",
        "Sender": memberTag, #member.tag.memberTag
            "Timestamp": timeInterval,
                "payload": bindingPayload
                }
    publishPayload = sendMsg + '&$.to={"DeviceID":' + '"{}"'.format(hostID) + '}'
    
    #print('publishPayload: ' + publishPayload)
    bindingString = json.dumps(binding)
    #print('payload: ' + bindingString)
    global client
    client.publish(publishPayload,payload=bindingString,qos=1,retain=True)

def sendMqttRequestForTagUpdate():
    #local = ip
    global groupTag
    global memberTag
    global subGroupTag
    format = {'local': socket.gethostbyname(socket.gethostname()) ,
        'GroupTag': groupTag,
            'SubGroupTag': subGroupTag,
                'MemberTag': memberTag}
    formatString = json.dumps(format)
    global client
    global patchTwin
    print('formatString :' + formatString)
    print('patchTwin:' + patchTwin)
    client.publish(patchTwin,payload=formatString,qos=1,retain=True)

def sendMqttRegistSuccess(registState = True):
    
    if registState:
        action = "RegisterSuccess"
    else:
        action = "RegisterFail"

    global memberTag
    timestamp = int(time.time())
    format = {"Action": action,
        "Payload": None,
            "Sender": memberTag,
                "Timestamp" : timestamp }
    formatString = json.dumps(format)
    publishPayload = sendMsg + '&$.to={"DeviceID":' + '"{}"'.format(hostID) + '}'

    print('sendMqttRegistSuccess')
    print(formatString)
    print(publishPayload)

    global client
    client.publish(publishPayload,payload=formatString,qos=1,retain=True)

def sendMessage(message):
    global memberTag
    timestamp = str(int(time.time()))
    
    messageFormat = {"Action":"Message",
        "Sender":memberTag,
            "Timestamp": timestamp,
                "Payload": {"Text": message}
                }
    formatString = json.dumps(messageFormat)
    publishPayload = sendMsg + '&$.to={"DeviceID":' + '"{}"'.format(hostID) + '}'
    global client
    client.publish(publishPayload,payload=formatString,qos=1,retain=True)

def sendIRS(i):
    global memberTag
    timeInterval = int(time.time())
    irsAns = []
    #IRS 1~9是Send 0~8, 0是Send -1
    irsAns.append(int(i) - 1)
    irsSendingFormat = {
        "Action":"IRS.Answer",
            "Sender":memberTag,
                "Timestamp":timeInterval,
                    "Payload":{"Answer":irsAns}
                    }
    formatString = json.dumps(irsSendingFormat)
    publishPayload = sendMsg + '&$.to={"DeviceID":' + '"{}"'.format(hostID) + '}'
    # print('send IRS Success')
    # print(formatString)
    # print(publishPayload)
    global client
    client.publish(publishPayload,payload=formatString,qos=1,retain=True)

#def upload():
#block_blob_service = BlockBlobService(account_name='myaccount', account_key='mykey')
#block_blob_service = BlockBlobService(url=blobContainerSasUri)
#block_blob_service.create_container(blobContainerSasUri)

# block_blob_service.create_blob_from_path(
# 'mycontainer','myblockblob','sunset.png',
# content_settings=ContentSettings(content_type='image/jpg')
# )

# block_blob_service.create_blob_from_bytes(
#     ,
#     content_settings=ContentSettings(content_type='image/jpg')
# )


#MQTT Client
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+ str(rc))
#client.connected_flag = True
#Subscribing in on_connect() means that if we lose the connection and
#reconnect then subscriptions will be renewed.

def on_subscribe(client, userdata, mid, gqos):
    print("subscribed: "+ str(mid) + str(gqos))
    line_bot_api.push_message(userID, TextSendMessage(text='連線中'))

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    #print(msg.topic+ "\n" + str(msg.payload))
    print(str(msg.payload))
    #print(type(msg.payload))
    global memberList
    jsonPayload = json.loads(msg.payload)
    action= jsonPayload['Action']
    print(action)
    
    if action == 'Announce':
        global hostID
        global pinCode
        global groupName
        global memberList
        global groupTag
        memberList = jsonPayload['Payload']['MemberList']
        hostID = jsonPayload['Payload']['Host']
        pinCode = jsonPayload['Payload']['Pincode']
        groupName = jsonPayload['Payload']['GroupName']
        groupTag = jsonPayload['Payload']['GroupTag']
        #line_bot_api.push_message(userID, TextSendMessage(text='收到公告'))
        line_bot_api.push_message(userID, TextSendMessage(text='請輸入教室密碼(PINCode)'))
    
    elif action == 'BindingSuccess':
        print('BindingSuccess')
        global didBinded
        didBinded = True
        line_bot_api.push_message(userID, TextSendMessage(text='已登錄教室'))
        sendMqttRequestForTagUpdate()
        sendMqttRegistSuccess(True)

    elif action =="BindingFail" :
        print('BindingFail')
        line_bot_api.push_message(userID, TextSendMessage(text='登錄教室失敗'))
        sendMqttRegistSuccess(False)

    elif action == 'Message':
        eceiveMessage = jsonPayload['Payload']['Text']
        m = 'Teacher:' + receiveMessage
        line_bot_api.push_message(userID, TextSendMessage(text=receiveMessage))

    elif action == 'State':
        #irs = bool
        irs = jsonPayload['Payload']['IRS']

        #line_bot_api.push_message(userID, TextSendMessage(text=str(irs)))

        if irs:
            buttons_template = TemplateSendMessage(
                alt_text='Buttons template',
                template=ButtonsTemplate(
                    thumbnail_image_url='https://i.imgur.com/qpPwSfF.jpg',
                        title='IRS',
                        text='請選擇',
                        actions=[
                            MessageTemplateAction(label='IRS 1',text='I1'),
                            MessageTemplateAction(label='IRS 2',text='I2'),
                            MessageTemplateAction(label='IRS 3',text='I3'),
                            MessageTemplateAction(label='IRS 4',text='I4')
                            ]
                        )
            )
        line_bot_api.push_message(userID,buttons_template)


    elif action == 'GroupClose':
        print('GroupClose')
        line_bot_api.push_message(userID, TextSendMessage(text='活動結束 教室關閉'))

def on_log(client, userdata, level, buf):
    print("Log:",buf)

def on_disconnect(client, userdata, rc):
    print('disconnect')
    line_bot_api.push_message(userID, TextSendMessage(text='連線中斷'))

def on_publish(client, userdata, mid):
    print('on_publish')
    #print(userdata)


def mqttConnect(publishPayload='',binding=''):
    global client
    
    #client = mqtt.Client(client_id=MQTTclientID)
    #mqtt.Client.connected_flag = False
    
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_subscribe = on_subscribe
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect
    #client.on_log = on_log
    client.username_pw_set(username, password)
    client.tls_set(tls_version=ssl.PROTOCOL_TLSv1)
    #client.connect(host="192.168.0.175", port=1883, keepalive=60)
    client.connect(host=brokerHostName, port=8883, keepalive=60)
    client.loop_start()
    client.subscribe(receiveMsg,qos=1)


@app.route('/gg', methods=['GET'])
def test():
    return "GG WP!"


@handler.add(MessageEvent, message=StickerMessage)
def handle_message(event): 
    sticker_message = StickerSendMessage(
        package_id = event.message.package_id,
        sticker_id = event.message.sticker_id
    )
    line_bot_api.push_message(userID, sticker_message)


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global userID
    msg = event.message.text
    userID = event.source.user_id
    #if event.source.group_id is not None:
    #    groupID = event.source.group_id
    global didBinded
    global client

    if msg == '狀態':
        global memberName
        if didBinded:
            line_bot_api.push_message(userID, TextSendMessage(text=memberName + ' 連線中'))
        else:
            line_bot_api.push_message(userID, TextSendMessage(text='尚未連線'))

    if msg == '離開':
        didBinded = False
        client.disconnect()

    if msg == '你好' or msg == '嗨':
        menulist = '輸入\n[連線+教室代碼] \n建立連線\nex. \n連線100000 \n連線200000'
        #line_bot_api.reply_message(event.reply_token,TextSendMessage(text=menulist))
        line_bot_api.push_message(userID, TextSendMessage(text=menulist))
        
    if msg[0] == '連' and msg[1] == '線':
        global groupNum
        groupNum = msg.split('線')[1]
        g = regist()
        #line_bot_api.reply_message(event.reply_token,TextSendMessage(text=g))
        line_bot_api.push_message(userID, TextSendMessage(text=g))
        
    if msg[0] == 'p':
        pin = msg.split('p')[1]
        #line_bot_api.push_message(userID, TextSendMessage(text=pin))
        pinCodeCheck(pin)
        
    if msg[0] == '選':
        indexPath = int(msg.split('選')[1]) - 1
        bindingMember(indexPath)

    if didBinded:

        if msg[0] == 'i' :
            irsStr = msg.split('i')[1]
            sendIRS(irsStr)
            line_bot_api.push_message(userID, TextSendMessage(text='IRS已送: ' + irsStr))

        elif msg[0] == 'I':
            irsStr = msg.split('I')[1]
            sendIRS(irsStr)
            line_bot_api.push_message(userID, TextSendMessage(text='IRS已送: ' + irsStr))

        else:
            sendMessage(msg)
            line_bot_api.push_message(userID, TextSendMessage(text='訊息已送:' + msg))



if __name__ == "__main__":
    app.run()
