# Audio Agent Setup & Usage

This project includes complete audio conversation functionality:
- **Speech-to-Text**: Captures speech from your microphone and transcribes it using Deepgram
- **LangGraph Processing**: Feeds transcribed text to your LangGraph agent  
- **Text-to-Speech**: Converts agent responses back to speech using Deepgram TTS
- **Audio Playback**: Plays the synthesized speech through your speakers

## 🚀 Quick Setup

### 1. Install Dependencies

You'll need to install these packages:

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install portaudio19-dev python3-pyaudio alsa-utils

# Install Python dependencies
pip install -r requirements.txt
```

**Required packages:**
- `deepgram-sdk` - For speech-to-text transcription
- `pyaudio` - For microphone audio capture
- `langchain-openai` - Already installed
- `langgraph` - Already installed

### 2. Get Deepgram API Key

1. Sign up at [Deepgram Console](https://console.deepgram.com/)
2. Get your API key
3. Set it as an environment variable:

```bash
export DEEPGRAM_API_KEY="your_api_key_here"
```

Or add to your `~/.bashrc` or `~/.zshrc`:
```bash
echo 'export DEEPGRAM_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

## 🎤 Usage

### Option 1: Audio Agent (Recommended)
```bash
python audio_agent.py
```

This will:
1. Record audio from your microphone (default 5 seconds)
2. Transcribe the audio using Deepgram STT
3. Send the transcribed text to your LangGraph agent
4. Convert the agent's response to speech using Deepgram TTS
5. Play the spoken response through your speakers

### Option 2: Test Basic Agent
```bash
python main.py
```

This tests your LangGraph agent with a simple text message.

## 🛠️ Automatic Setup

For easier setup, run:
```bash
python setup_audio.py
```

This will:
- Install system dependencies
- Install Python packages
- Check your Deepgram API key
- Test audio recording
- List available microphones

## 🎯 How It Works

1. **Audio Capture**: Uses PyAudio to record from your microphone
2. **Speech-to-Text**: Deepgram converts speech to text using Nova-2 model
3. **Agent Processing**: LangGraph agent processes the transcribed text
4. **Text-to-Speech**: Deepgram converts agent response to speech using Aura model
5. **Audio Playback**: PyAudio plays the synthesized speech

**Complete Voice-to-Voice Flow**: You speak → Agent hears → Agent thinks → Agent speaks back!

## 🔧 Customization

### Commands
When running `audio_agent.py`, you can:
- Press Enter for voice conversation with TTS enabled
- Type "text" to disable TTS (text-only responses)
- Type "speech" to re-enable TTS (voice responses)
- Type a number (e.g., "10") to set recording duration
- Type "quit" to exit

### Audio Settings
In `audio_agent.py`, you can modify:
```python
self.rate = 16000        # Sample rate
self.channels = 1        # Mono audio
self.record_seconds = 5  # Default duration
```

### Transcription Options
Modify the Deepgram STT options:
```python
options = PrerecordedOptions(
    model="nova-2",      # Use Nova-2 model
    smart_format=True,   # Auto-punctuation
    language="en"        # English language
)
```

### Text-to-Speech Options
Modify the Deepgram TTS options in the `text_to_speech` method:
```python
options = SpeakOptions(
    model="aura-asteria-en",  # High-quality voice model
    encoding="linear16",       # Audio format
    sample_rate=24000         # Supported sample rate for linear16
)
```

**Supported Sample Rates for linear16 encoding:**
- 8000 Hz - Telephone quality
- 16000 Hz - Standard quality
- 24000 Hz - High quality (recommended)
- 32000 Hz - Very high quality
- 48000 Hz - Studio quality

**Available TTS Models:**
- `aura-asteria-en` - Female, warm and conversational
- `aura-luna-en` - Female, smooth and pleasant  
- `aura-stella-en` - Female, friendly and approachable
- `aura-athena-en` - Female, confident and articulate
- `aura-hera-en` - Female, sophisticated and polished
- `aura-orion-en` - Male, deep and authoritative
- `aura-arcas-en` - Male, natural and engaging
- `aura-perseus-en` - Male, assertive and clear
- `aura-angus-en` - Male, gruff and strong
- `aura-orpheus-en` - Male, confident and smooth
- `aura-helios-en` - Male, upbeat and energetic
- `aura-zeus-en` - Male, powerful and commanding



## 🎙️ Microphone Troubleshooting

### List Available Microphones
```bash
python -c "
import pyaudio
audio = pyaudio.PyAudio()
for i in range(audio.get_device_count()):
    info = audio.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f'{i}: {info[\"name\"]}')
audio.terminate()
"
```

### Test Audio Recording
```bash
# Test system audio
arecord -d 5 -f cd test.wav && aplay test.wav
```

## 📝 Example Session

```
$ python audio_agent.py
🎤 Audio Agent initialized!
Features:
- Speech-to-Text: Converts your voice to text
- LangGraph Agent: Processes your request intelligently
- Text-to-Speech: Converts agent responses to speech

Commands:
- Press Enter to start recording with TTS
- Type 'text' to disable TTS (text-only mode)
- Type 'speech' to enable TTS (default)
- Type 'quit' to exit
- Type a number to set recording duration (seconds)

[🔊 TTS ON] Press Enter to record (or command): 
Recording audio for 5 seconds...
Speak now!
Recording finished!
Transcribing audio...
Transcribed text: What's the weather like in New York?
Processing with LangGraph agent...
It is sunny in New York.
Converting text to speech...
Text-to-speech conversion completed!
Playing audio...
Audio playback completed!
```

## 🐛 Common Issues

1. **ModuleNotFoundError: pyaudio**
   - Install: `sudo apt-get install python3-pyaudio portaudio19-dev`

2. **DEEPGRAM_API_KEY not set**
   - Set environment variable with your Deepgram API key

3. **No audio input**
   - Check microphone permissions
   - Verify microphone is working: `arecord -d 5 test.wav`

4. **Audio device busy**
   - Close other audio applications
   - Check available devices with setup script

5. **Transcription failed**
   - Check Deepgram API key and credits
   - Verify internet connection
   - Check Deepgram service status
   - Ensure audio quality is good

6. **TTS sample rate error**
   - Use supported sample rates: 8000, 16000, 24000, 32000, or 48000 Hz
   - Default is 24000 Hz for good quality

7. **Deepgram SDK deprecation warnings**
   - Update to latest deepgram-sdk version: `pip install --upgrade deepgram-sdk`
   - Code has been updated to use current API methods

## 🧪 Troubleshooting Tools

### Manual Audio Tests
```bash
# Test microphone
arecord -d 5 -f cd test.wav && aplay test.wav

# Check audio devices
arecord -l  # List recording devices
```


