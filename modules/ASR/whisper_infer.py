from transformers import pipeline
import numpy as np


class Transcriber:
    def __init__(self):
        self.transcriber = pipeline(
            "automatic-speech-recognition", model="models/whisper-tiny-finetune"
        )

    def transcribe(self, stream, new_chunk):
        sr, y = new_chunk
        y = y.astype(np.float32)
        y /= np.max(np.abs(y))

        if stream is not None:
            stream = np.concatenate([stream, y])
        else:
            stream = y
        return stream, self.transcriber({"sampling_rate": sr, "raw": stream})["text"]
