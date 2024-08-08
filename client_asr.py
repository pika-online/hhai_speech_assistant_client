import websockets
import asyncio
import json
import ssl
import queue
import sounddevice as sd
import numpy as np

class SpeechRecognitionAssistant:
    """
    Automatic Speech Recognition (ASR) Assistant class for handling the recognition of speech using WebSocket connections.
    """

    def __init__(self,
                 uri_asr="wss://47.96.15.141:10095",
                 words_asr={"鸿合科技": 20}) -> None:
        """
        Initializes the ASR Assistant with the WebSocket URL and hotword configurations.
        
        Args:
            uri_asr (str): URL for the ASR WebSocket server.
            words_asr (dict): Dictionary of hotwords and their weights for ASR.
        """
        self.uri_asr = uri_asr
        self.words_asr = words_asr
        self.sample_rate = 16000

    async def init_websocket_asr(self):
        """Initialize WebSocket connection for ASR."""
        ssl_context = ssl.SSLContext()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        self.ws_session_asr = await websockets.connect(self.uri_asr, subprotocols=["binary"], ping_interval=None, ssl=ssl_context)
        print("Connected to websocket_asr")

    async def close_websocket_asr(self):
        """Close WebSocket connection for ASR."""
        if self.ws_session_asr:
            await self.ws_session_asr.close()
            print("Closed websocket_asr")

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
        print(conf)
        await self.ws_session_asr.send(json.dumps(conf))
        print("Successfully initialized ASR model")

    async def receiver_asr(self):
        """Receive ASR results and print recognized text."""
        try:
            text_online = ""
            text_offline = ""
            while True:
                response = json.loads(await self.ws_session_asr.recv())
                if response['mode'] == '2pass-online':
                    text_online += response['text']
                    
                if response['mode'] == '2pass-offline':
                    text_offline += response['text'].replace(" ", "")
                    text_online = text_offline
                    
                print(f'\r[我]：{text_online}', end="")


        except websockets.ConnectionClosedError as e:
            print(f"Connection closed with error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    async def run(self):
        """Main run loop for handling recording, sending audio streams, and managing ASR state."""

        # Initialize WebSocket connection
        await self.init_websocket_asr()

        # Initialize the ASR model
        await self.init_model_asr()

        chunk_size_unit = 320
        chunk_size_asr = 960
        asr_times = chunk_size_asr // chunk_size_unit
        asr_queue = queue.Queue()

        try:
            # Start the receiver task for ASR
            receive_task_asr = asyncio.create_task(self.receiver_asr())

            # Start recording audio and sending it to the ASR model
            with sd.InputStream(channels=1, dtype="int16", samplerate=self.sample_rate) as stream:
                print("Recording... Press Ctrl+C to stop.")
                while True:
                    samples, _ = stream.read(chunk_size_unit)  # Blocking read
                    samples = samples.flatten().tolist()

                    # ASR Stream
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
            receive_task_asr.cancel()
            await self.close_websocket_asr()


if __name__ == "__main__":
    """Main entry point to load configurations and run the Speech Recognition Assistant."""

    # Load hotword list and weights for ASR
    with open('words_asr.txt', 'rt', encoding='utf-8') as f:
        words_asr = f.readlines()
        words_asr = [line.strip() for line in words_asr]
        words_asr_dct = {}
        for line in words_asr:
            word, weight = line.split()
            words_asr_dct[word] = int(weight)

    # Instantiate and run the Speech Recognition Assistant
    assistant = SpeechRecognitionAssistant(uri_asr="wss://47.96.15.141:10095", words_asr=words_asr_dct)
    asyncio.get_event_loop().run_until_complete(assistant.run())
