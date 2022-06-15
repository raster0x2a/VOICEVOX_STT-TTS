# VOICEVOX STT-TTS

以下のツールを使用して、音声入力->テキスト書き起こし->音声読み上げを行うツールです。
音声入力: [Google Cloud Speech-to-Text API](https://cloud.google.com/speech-to-text), [Vosk](https://alphacephei.com/vosk/)
音声合成: [VOICEVOX](https://voicevox.hiroshiba.jp/)の[非公式WebAPI](https://voicevox.su-shiki.com/su-shikiapis/)
Windows 11、Python 3.9.6で仮想オーディオデバイスを使用した環境で動作を確認しています。  
  
google-stt_voicevox-tts.py: Google Cloud Speech-to-Text API + VOICEVOX  
vosk-stt_voicevox-tts.py: Vosk + VOICEVOX  

## 出力用仮想オーディオデバイスの設定

以下のPythonスクリプトで各オーディオデバイスのインデックスが確認できます。使用したい出力用デバイスのインデックスを確認し、`OUTPUT_DEVICE_INDEX`変数で指定してください。

```py
import pyaudio
 
p = pyaudio.PyAudio()
for i in range(p.get_device_count()): 
    print(p.get_device_info_by_index(i))
```

## Voskのモデルインストール手順

Vosk公式の[モデルダウンロードページ](https://alphacephei.com/vosk/models)から好きなモデルデータをダウンロード&解凍し、このディレクトリに`model`というディレクトリを作成しファイルを置きます。日本語の場合はvosk-model-small-ja-0.22を使用すればよいです。
