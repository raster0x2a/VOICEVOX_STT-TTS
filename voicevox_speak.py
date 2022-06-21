import os
import datetime
import wave

import pyaudio
import requests

from credentials import voicevox_api_key


def speak(text):
    SPEAKER_DEFAULT = 0
    #speaker_info = []
    #speaker_api_endpoint = "https://api.su-shiki.com/v2/voicevox/speakers/?key={voicevox_api_key}"
    api_endpoint = f"https://api.su-shiki.com/v2/voicevox/audio/?key={voicevox_api_key}&text={text}&speaker={SPEAKER_DEFAULT}"
        
    try:
        response = requests.get(api_endpoint)
        filename = f"audio_{datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')}.wav"
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio", filename)
        with open(file_path, 'wb') as save_file:
            save_file.write(response.content)
        
        wf = wave.open(file_path, "r")
        p = pyaudio.PyAudio()
        
        OUTPUT_DEVICE_INDEX = 5  # 出力音声デバイス番号
        stream = p.open(
            format=p.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            frames_per_buffer=1024,
            output_device_index=OUTPUT_DEVICE_INDEX,
            output=True)

        chunk = 1024
        data = wf.readframes(chunk)
        while data != b"":
            stream.write(data)
            data = wf.readframes(chunk)
        stream.close()
        #p.terminate()

    except Exception as e:
        print(e)


if __name__ == "__main__":
    print("テスト")
    speak("テスト")