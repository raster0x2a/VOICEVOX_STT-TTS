import os
import re
import sys
import datetime
import time
from six.moves import queue

from google.cloud import speech
import pyaudio

from credentials import google_tts_crediential_file_name
from voicevox_speak import speak

# Google Text-to-Speech Searviceの認証情報JSONファイルのパスを環境変数に設定
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), google_tts_crediential_file_name)


RATE = 16000
CHUNK = int(RATE / 10)  # 100ms


class MicrophoneStream(object):
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk
        
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)


def listen_print_loop(responses):
    num_chars_printed = 0
    for response in responses:
        if not response.results:
            continue

        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript

        overwrite_chars = " " * (num_chars_printed - len(transcript))

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + "\r")
            sys.stdout.flush()

            num_chars_printed = len(transcript)

        else:
            # 置換する単語のユーザー定義辞書
            trans_data = {
                "Python": "パイソン",
            }
            speak_transcript = transcript
            for before, after in trans_data.items():
                speak_transcript = re.sub(before, after, speak_transcript)
            
            # 音声入力での終了コマンド
            if re.search(r"コマンド終了.*", transcript, re.I):
                print("Exiting..")
                exit()
            
            print(speak_transcript)
            speak(speak_transcript)

            num_chars_printed = 0


def main():
    language_code = "ja-JP"

    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code,
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )

        for _ in range(30):
            print("start:", datetime.datetime.now())
            try:
                responses = client.streaming_recognize(streaming_config, requests)
            except Exception as e:
                print("Error1: None Exception iterating requests!", e)

            try:
                listen_print_loop(responses)
            except Exception as e:
                print("Error2: Excption handle : Exceeded maximum allowed stream duration of 65 seconds", e)

            time.sleep(1)
            
        speak("停止しました")
        

if __name__ == "__main__":
    main()
