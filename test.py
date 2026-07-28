from gtts import gTTS

tts = gTTS(text="Hello everyone", lang="en")

tts.save("output.mp3")

