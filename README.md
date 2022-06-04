# VOICEVOX STT-TTS

[Google Cloud Speech-to-Text API](https://cloud.google.com/speech-to-text)と[VOICEVOX](https://voicevox.hiroshiba.jp/)の[非公式WebAPI](https://voicevox.su-shiki.com/su-shikiapis/)を使用して、音声入力->テキスト->音声読み上げを行うツールです。
Windows 11、Python 3.9.6で仮想オーディオデバイスを使用した環境で動作を確認しています。

## 出力用仮想オーディオデバイスの設定

以下のPythonスクリプトで各オーディオデバイスのインデックスが確認できます。使用したい出力用デバイスのインデックスを確認し、`OUTPUT_DEVICE_INDEX`変数で指定してください。

```py
import pyaudio
 
p = pyaudio.PyAudio()
for i in range(p.get_device_count()): 
    print(p.get_device_info_by_index(i))
```
