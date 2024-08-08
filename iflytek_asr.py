# -*- encoding:utf-8 -*-
import hashlib
import hmac
import base64
from socket import *
import json, time, threading
from websocket import create_connection
import websocket
from urllib.parse import quote
import logging
import pyaudio

# reload(sys)
# sys.setdefaultencoding("utf8")
class Client():
    def __init__(self):
        base_url = "ws://rtasr.xfyun.cn/v1/ws"
        ts = str(int(time.time()))
        tt = (app_id + ts).encode('utf-8')
        md5 = hashlib.md5()
        md5.update(tt)
        baseString = md5.hexdigest()
        baseString = bytes(baseString, encoding='utf-8')

        apiKey = api_key.encode('utf-8')
        signa = hmac.new(apiKey, baseString, hashlib.sha1).digest()
        signa = base64.b64encode(signa)
        signa = str(signa, 'utf-8')
        self.end_tag = "{\"end\": true}"

        self.ws = create_connection(base_url + "?appid=" + app_id + "&ts=" + ts + "&signa=" + quote(signa) + "&roleType=2")
        self.trecv = threading.Thread(target=self.recv)
        self.trecv.start()
        self.role = 0




    def send(self,):
        # 配置音频流
        chunk_size = 1280  # 每次读取的字节数
        sample_format = pyaudio.paInt16  # 16位采样深度
        channels = 1  # 单声道
        rate = 16000  # 采样率

        p = pyaudio.PyAudio()

        # 打开音频流
        stream = p.open(format=sample_format,
                        channels=channels,
                        rate=rate,
                        input=True,
                        frames_per_buffer=chunk_size)

        try:
            print("开始录音...")
            while True:
                chunk = stream.read(chunk_size)
                self.ws.send(chunk)
                time.sleep(0.04)  # 控制发送速率
        finally:
            # 关闭音频流
            stream.stop_stream()
            stream.close()
            p.terminate()
            print("录音结束")

        self.ws.send(bytes(self.end_tag.encode('utf-8')))
        print("send end tag success")


    def recv(self):
        try:
            while self.ws.connected:
                result = str(self.ws.recv())
                if len(result) == 0:
                    print("receive result end")
                    break
                result_dict = json.loads(result)

                
                if  result_dict['code']=='0' and result_dict['action'] == 'result':
                    data = json.loads(result_dict['data'])
                    tmp = data['cn']['st']['rt'][0]['ws']
                    for seg in tmp:
                        ret = seg['cw'][0]
                        text = ret['w']
                        rl = int(ret['rl'])
                        if rl>0:
                            self.role = rl
                        print(f"Speaker-{self.role}: {text}")
                    # for result in results:
                    #     result

                # print(result_dict)
                # # 解析结果
                # if result_dict["action"] == "started":
                #     print("handshake success, result: " + result)

                # if result_dict["action"] == "result":
                #     result_1 = result_dict
                #     # result_2 = json.loads(result_1["cn"])
                #     # result_3 = json.loads(result_2["st"])
                #     # result_4 = json.loads(result_3["rt"])
                #     print("rtasr result: " + result_1["data"])

                # if result_dict["action"] == "error":
                #     print("rtasr error: " + result)
                #     self.ws.close()
                #     return
        except websocket.WebSocketConnectionClosedException:
            print("receive result end")

    def close(self):
        self.ws.close()
        print("connection closed")


if __name__ == '__main__':
    logging.basicConfig()

    app_id = "8e901072"
    api_key = "5fb0231d9ab71f7961025f351bcbd804"
    file_path = r"./test_1.pcm"

    client = Client()
    client.send()
