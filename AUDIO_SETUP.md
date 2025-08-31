# Audio Agent Setup & Usage

This project includes audio input functionality:
- **Speech-to-Text**: Captures speech from your microphone and transcribes it using Deepgram
- **LangGraph Processing**: Feeds transcribed text to your LangGraph agent
- **Text Response**: Agent responds with text output (TTS removed for simplicity)

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
2. Transcribe the audio using Deepgram
3. Send the transcribed text to your LangGraph agent
4. Display the agent's response

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
4. **Text Response**: Agent displays response as text

**Voice-to-Text Flow**: You speak → Agent hears → Agent thinks → Agent responds with text!

## 🔧 Customization

### Recording Duration
When running `audio_agent.py`, you can:
- Press Enter for default 5-second recording
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
Modify the Deepgram options:
```python
options = PrerecordedOptions(
    model="nova-2",      # Use Nova-2 model
    smart_format=True,   # Auto-punctuation
    language="en"        # English language
)
```



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
- LangGraph Agent: Processes your request and responds with text

Commands:
- Press Enter to start recording
- Type 'quit' to exit
- Type a number to set recording duration (seconds)

Press Enter to record (or 'quit' to exit): 
Recording audio for 5 seconds...
Speak now!
Recording finished!
Transcribing audio...
Transcribed text: What's the weather like in New York?
Processing with LangGraph agent...
It is sunny in New York.
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

## 🧪 Troubleshooting Tools

### Manual Audio Tests
```bash
# Test microphone
arecord -d 5 -f cd test.wav && aplay test.wav

# Check audio devices
arecord -l  # List recording devices
```


