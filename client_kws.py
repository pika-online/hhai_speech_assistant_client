import websockets
import asyncio
import json
import queue
import sounddevice as sd
import numpy as np

class KeywordSpottingAssistant:
    """
    Keyword Spotting (KWS) Assistant class for handling the detection of keywords using WebSocket connections.
    """

    def __init__(self,
                 uri_kws="ws://47.96.15.141:10094",
                 words_kws=['小新小新', '小爱同学']) -> None:
        """
        Initializes the KWS Assistant with the WebSocket URL and keyword configurations.
        
        Args:
            uri_kws (str): URL for the KWS WebSocket server.
            words_kws (list): List of keywords for KWS.
        """
        self.uri_kws = uri_kws
        self.words_kws = words_kws
        self.sample_rate = 16000
        self.state = 'kws'

    async def init_websocket_kws(self):
        """Initialize WebSocket connection for KWS."""
        self.ws_session_kws = await websockets.connect(self.uri_kws)
        print("Connected to websocket_kws")

    async def close_websocket_kws(self):
        """Close WebSocket connection for KWS."""
        if self.ws_session_kws:
            await self.ws_session_kws.close()
            print("Closed websocket_kws")

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

    async def receiver_kws(self):
        """Receive KWS results and print the detected keyword."""
        try:
            while True:
                response = json.loads(await self.ws_session_kws.recv())
                if response['code'] == 0:
                    detected_keyword = response['message']
                    print(f"\n[Keyword Detected]: {detected_keyword}")
                    self.state = 'kws'
        except websockets.ConnectionClosedError as e:
            print(f"Connection closed with error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    async def run(self):
        """Main run loop for handling recording, sending audio streams, and managing KWS state."""

        # Initialize WebSocket connection
        await self.init_websocket_kws()

        # Initialize the KWS model
        await self.init_model_kws()

        chunk_size_unit = 320
        chunk_size_kws = 1600
        kws_times = chunk_size_kws // chunk_size_unit
        kws_queue = queue.Queue()

        try:
            # Start the receiver task for KWS
            receive_task_kws = asyncio.create_task(self.receiver_kws())

            # Start recording audio and sending it to the KWS model
            with sd.InputStream(channels=1, dtype="int16", samplerate=self.sample_rate) as stream:
                print("Recording... Press Ctrl+C to stop.")
                while True:
                    samples, _ = stream.read(chunk_size_unit)  # Blocking read
                    samples = samples.flatten().tolist()

                    # KWS Stream
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

                    await asyncio.sleep(0.001)

        except KeyboardInterrupt:
            print("Recording stopped.")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            receive_task_kws.cancel()
            await self.close_websocket_kws()


if __name__ == "__main__":
    """Main entry point to load configurations and run the Keyword Spotting Assistant."""

    # Load keyword list for KWS
    with open('words_kws.txt', 'rt', encoding='utf-8') as f:
        words_kws = f.readlines()
        words_kws = [line.strip() for line in words_kws]

    # Instantiate and run the Keyword Spotting Assistant
    assistant = KeywordSpottingAssistant(uri_kws="ws://47.96.15.141:10094", words_kws=words_kws)
    asyncio.get_event_loop().run_until_complete(assistant.run())
