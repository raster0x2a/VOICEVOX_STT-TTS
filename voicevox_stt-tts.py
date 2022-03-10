import os
import re
import sys
import datetime
import time
import wave
from six.moves import queue
import hashlib

from google.cloud import speech
import pyaudio
import requests

from credentials import voicevox_api_key, google_tts_crediential_file_name


# Google Text-to-Speech Searviceの認証情報JSONファイルのパスを環境変数に設定
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), google_tts_crediential_file_name)


def speak(text):
    try:
        response = requests.get(f"https://api.su-shiki.com/v2/voicevox/audio/?key={voicevox_api_key}&text={text}")
        # 末尾に読み上げテキストのハッシュを付したファイル名
        filename = f"audio_{hashlib.md5(text.encode('utf-8')).hexdigest()}.wav"
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio", filename)
        if not os.path.isfile(file_path):
            with open(file_path, 'wb') as save_file:
                save_file.write(response.content)
        
        wf = wave.open(file_path, "r")

        p = pyaudio.PyAudio()
        p. get_device_info_by_index(2)  # 任意の入力デバイスを指定
        
        stream = p.open(
            format=p.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            frames_per_buffer=1024,
            output_device_index=7,  # 任意の出力デバイスを指定
            output=True
        )

        chunk = 1024
        data = wf.readframes(chunk)
        while data != b"":
            stream.write(data)
            data = wf.readframes(chunk)
        stream.close()

    except Exception as e:
        print(e)


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
