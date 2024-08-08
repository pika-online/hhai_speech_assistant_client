import sounddevice as sd
import websockets
import asyncio
import json
import ssl 
import queue 
import numpy as np 
import requests

class Speech_Assistant():
    """
    Speech Assistant class for handling Keyword Spotting (KWS), Automatic Speech Recognition (ASR), 
    and Natural Language Understanding (NLU) tasks using WebSocket connections.
    """

    def __init__(self,
                 uri_kws="ws://0.0.0.0:10094",
                 uri_asr="wss://0.0.0.0:10095",
                 uri_nlu="http://0.0.0.0:10096",
                 words_kws=['小新小新', '小爱同学'],
                 words_asr={"小米手机":20},
                 words_nlu=[]) -> None:
        """
        Initializes the Speech Assistant with URLs and keyword configurations.
        
        Args:
            uri_kws (str): URL for the KWS WebSocket server.
            uri_asr (str): URL for the ASR WebSocket server.
            uri_nlu (str): URL for the NLU HTTP server.
            words_kws (list): List of keywords for KWS.
            words_asr (dict): Dictionary of hotwords and their weights for ASR.
            words_nlu (list): List of sentences to compare for NLU.
        """
        self.uri_kws = uri_kws
        self.uri_asr = uri_asr
        self.uri_nlu = uri_nlu
        self.words_kws = words_kws
        self.words_asr = words_asr
        self.words_nlu = words_nlu
        self.sample_rate = 16000
        self.state = 'kws'
        self.assistant = "unknown"

    async def init_websocket_kws(self):
        """Initialize WebSocket connection for KWS."""
        self.ws_session_kws = await websockets.connect(self.uri_kws)
        print("Connected to websocket_kws")

    async def init_websocket_asr(self):
        """Initialize WebSocket connection for ASR."""
        ssl_context = ssl.SSLContext()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        self.ws_session_asr = await websockets.connect(self.uri_asr, subprotocols=["binary"], ping_interval=None, ssl=ssl_context)
        print("Connected to websocket_asr")

    async def close_websockets(self):
        """Close WebSockets ."""
        if self.ws_session_kws:
            await self.ws_session_kws.close()
            print("Closed websocket_kws")
        if self.ws_session_asr:
            await self.ws_session_asr.close()
            print("Closed websocket_asr")

    async def init_model_kws(self):
        """Initialize KWS model by sending configuration."""
        conf = {
            'remote': 'init',
            'words': self.words_kws
        }
        await self.ws_session_kws.send(json.dumps(conf))
        response = json.loads(await self.ws_session_kws.recv())
        print(response)
        print("Successfully initialized KWS model")

    async def init_model_asr(self):
        """Initialize ASR model by sending configuration."""
        conf = {
            "mode": "2pass",
            "chunk_size": [5, 10, 5],
            "chunk_interval": 10,
            "encoder_chunk_look_back": 4,
            "decoder_chunk_look_back": 0,
            "wav_name": "microphone",
            "hotwords": json.dumps(self.words_asr),
            "itn": True,
            "is_speaking": True
        }
        await self.ws_session_asr.send(json.dumps(conf))
        print("Successfully initialized ASR model")

    async def init_model_nlu(self):
        """Initialize NLU model by uploading the word list."""
        payload = {
            'sentences_to_compare': self.words_nlu
        }
        headers = {'Content-Type': 'application/json'}
        response = requests.post(f'{self.uri_nlu}/upload_words', data=json.dumps(payload), headers=headers)
        if response.status_code == 200:
            print("NLU word list uploaded successfully.")
        else:
            print(f"Failed to upload word list: {response.json()}")
        print("Successfully initialized NLU model")
        

    async def receiver_kws(self):
        """Receive KWS results and transition to ASR state upon successful keyword detection."""
        try:
            while True:
                response = json.loads(await self.ws_session_kws.recv())
                if response['code'] == 0:
                    self.assistant = response['message']
                    print(f"\n[{self.assistant}]: 我在")
                    self.state = 'asr'
                    

        except websockets.ConnectionClosedError as e:
            print(f"Connection closed with error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")


    async def receiver_asr(self):
        """Receive ASR results, process text, and interact with NLU for command matching."""
        try:
            text_online = ""
            text_offline = ""
            while True:
                response = json.loads(await self.ws_session_asr.recv())
                if response['mode'] == '2pass-online':
                    text_online += response['text']
                    print(f'\r[我]：{text_online}', end="")

                if response['mode'] == '2pass-offline':
                    if len(response['stamp_sents']) > 1:
                        text_offline = response['text'][1:]
                    else:
                        text_offline = response['text']
                    text_offline = text_offline.replace(" ", "")
                    print(f'\r[我]：{text_offline}')

                    # NLU API call for sentence matching
                    url = f'{self.uri_nlu}/match_sentence'
                    payload = {'source_sentence': text_offline}
                    headers = {'Content-Type': 'application/json'}
                    response = requests.post(url, data=json.dumps(payload), headers=headers)
                    if response.status_code == 200:
                        result = response.json()
                        print(f"[{self.assistant}]: 匹配命令: <{result['best_match']}>, 得分：{result['score']}")
                    else:
                        print(f"{self.assistant}]: Failed to match sentence: {response.json()}")
                        
                    self.state = 'kws'
                    text_online = ""
                    text_offline = ""


        except websockets.ConnectionClosedError as e:
            print(f"Connection closed with error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    async def run(self):
        """Main run loop for handling recording, sending audio streams, and managing states."""

        # Initialize WebSocket connections
        await self.init_websocket_kws()
        await self.init_websocket_asr()

        # Initialize models
        await self.init_model_kws()
        await self.init_model_asr()
        await self.init_model_nlu()

        chunk_size_unit = 320
        chunk_size_kws = 1600
        chunk_size_asr = 960
        kws_times = chunk_size_kws // chunk_size_unit
        asr_times = chunk_size_asr // chunk_size_unit
        kws_queue = queue.Queue()
        asr_queue = queue.Queue()

        try:
            # Start receiver tasks for KWS and ASR
            receive_task_kws = asyncio.create_task(self.receiver_kws())
            receive_task_asr = asyncio.create_task(self.receiver_asr())

            # Start recording audio and sending it to the appropriate model
            with sd.InputStream(channels=1, dtype="int16", samplerate=self.sample_rate) as stream:
                print("Recording... Press Ctrl+C to stop.")
                while True:
                    samples, _ = stream.read(chunk_size_unit)  # Blocking read
                    samples = samples.flatten().tolist()

                    # KWS Stream 1600 points
                    if self.state == 'kws':
                        kws_queue.put(samples)
                        if kws_queue.qsize() >= kws_times:
                            kws_data = []
                            for _ in range(kws_times):
                                kws_data.extend(kws_queue.get())
                            data = {
                                "remote": 'listen',
                                "samples": kws_data,
                                "sample_rate": self.sample_rate
                            }
                            await self.ws_session_kws.send(json.dumps(data))

                    # ASR Stream 960 points
                    if self.state == 'asr':
                        asr_queue.put(samples)
                        if asr_queue.qsize() >= asr_times:
                            asr_data = []
                            for _ in range(asr_times):
                                asr_data.extend(asr_queue.get())
                            asr_data = np.array(asr_data, dtype='int16').tobytes()
                            await self.ws_session_asr.send(asr_data)

                    await asyncio.sleep(0.001)

        except KeyboardInterrupt:
            print("Recording stopped.")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            receive_task_kws.cancel()
            receive_task_asr.cancel()
            await self.close_websockets()


if __name__ == "__main__":
    """Main entry point to load configurations and run the Speech Assistant."""

    # Load keyword list for KWS
    with open('words_kws.txt', 'rt', encoding='utf-8') as f:
        words_kws = f.readlines()
        words_kws = [line.strip() for line in words_kws]

    # Load hotword list and weights for ASR
    with open('words_asr.txt', 'rt', encoding='utf-8') as f:
        words_asr = f.readlines()
        words_asr = [line.strip() for line in words_asr]
        words_asr_dct = {}
        for line in words_asr:
            word, weight = line.split()
            words_asr_dct[word] = int(weight)

    # Load sentences for NLU comparison
    with open('words_nlu.txt', 'rt', encoding='utf-8') as f:
        words_nlu = f.readlines()
        words_nlu = [line.strip() for line in words_nlu]

    # Instantiate and run the Speech Assistant
    host = '47.96.15.141'
    # host = 'www.funsound.cn'
    assistant = Speech_Assistant(uri_kws=f"ws://{host}:10094",
                                 uri_asr=f"wss://{host}:10095",
                                 uri_nlu=f"http://{host}:10096",
                                 words_kws=words_kws,
                                 words_asr=words_asr_dct,
                                 words_nlu=words_nlu)
    asyncio.get_event_loop().run_until_complete(assistant.run())
