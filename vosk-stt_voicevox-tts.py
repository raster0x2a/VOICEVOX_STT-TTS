#!/usr/bin/env python3

import argparse
import os
import queue
import sounddevice as sd
import sys
import json
import datetime
import wave
import re

import pyaudio
import vosk
import requests


def speak(text):
    try:
        key = "I_4655M-6_p5104"
        response = requests.get(f"https://api.su-shiki.com/v2/voicevox/audio/?key={key}&text={text}")
        filename = f"audio_{datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')}.wav"
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio", filename)
        with open(file_path, 'wb') as save_file:
            save_file.write(response.content)
        
        wf = wave.open(file_path, "r")

        p = pyaudio.PyAudio()
        
        stream = p.open(
            format=p.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            frames_per_buffer=1024,
            output_device_index=5,  # 2, 8, 14, 19 X
            output=True)

        chunk = 1024
        data = wf.readframes(chunk)
        while data != b"":
            stream.write(data)
            data = wf.readframes(chunk)
        stream.close()
        #p.terminate()
        
        
        """
        talker = win32com.client.Dispatch("CeVIO.Talk.RemoteService.Talker")
        talker.Cast = "さとうささら"
        talker.Speed = 44
        talker.Tone = 20
        #talker.ToneScale = 70
        state = talker.Speak(text)
        state.Wait()
        #cevio.CloseHost(0)
        """

    except Exception as e:
        print(e)


q = queue.Queue()


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text


def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    '-l', '--list-devices', action='store_true',
    help='show list of audio devices and exit')
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
parser.add_argument(
    '-f', '--filename', type=str, metavar='FILENAME',
    help='audio file to store recording to')
parser.add_argument(
    '-d', '--device', type=int_or_str,
    help='input device (numeric ID or substring)')
parser.add_argument(
    '-r', '--samplerate', type=int, help='sampling rate')
args = parser.parse_args(remaining)

try:
    if args.samplerate is None:
        device_info = sd.query_devices(args.device, 'input')
        # soundfile expects an int, sounddevice provides a float:
        args.samplerate = int(device_info['default_samplerate'])

    model = vosk.Model(lang="ja")

    if args.filename:
        dump_fn = open(args.filename, "wb")
    else:
        dump_fn = None

    with sd.RawInputStream(
            samplerate=args.samplerate, blocksize=8000, device=args.device,
            dtype='int16', channels=1, callback=callback):
        print('#' * 80)
        print('Press Ctrl+C to stop the recording')
        print('#' * 80)

        rec = vosk.KaldiRecognizer(model, args.samplerate)
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                tmp_result = json.loads(str(rec.Result()))
                result_text = tmp_result["text"].replace(" ", "")
                trans_data = {
                    "Python": "パイソン",
                    "今日は": "こんにちは",
                }
                speak_text = result_text
                for before, after in trans_data.items():
                    speak_text = re.sub(before, after, speak_text)
                if not speak_text == "":
                    print("RESULT: ", speak_text)
                    speak(speak_text)
                
            else:
                tmp_partial_result = json.loads(str(rec.PartialResult()))
                if not tmp_partial_result["partial"] == "":
                    print(tmp_partial_result)
                #print(rec.PartialResult())
            if dump_fn is not None:
                dump_fn.write(data)

except KeyboardInterrupt:
    print('\nDone')
    parser.exit(0)
except Exception as e:
    parser.exit(type(e).__name__ + ': ' + str(e))
