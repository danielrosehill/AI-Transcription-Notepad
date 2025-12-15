# Voice Notepad Features

Comprehensive feature documentation for Voice Notepad.

## Table of Contents

- [Core Features](#core-features)
- [Audio Processing](#audio-processing)
- [AI Transcription](#ai-transcription)
- [User Interface](#user-interface)
- [Cost Tracking](#cost-tracking)
- [Database & History](#database--history)
- [Hotkeys & Shortcuts](#hotkeys--shortcuts)
- [Settings & Configuration](#settings--configuration)

---

## Core Features

### Voice Recording
- **Real-time recording** with visual feedback
- **Automatic sample rate negotiation** with audio devices
- **Microphone disconnection handling** during recording
- **Append mode**: Record multiple clips and combine before transcription
- **Audio feedback**: Optional beep notifications for record start/stop

### File Transcription
- **Direct file upload**: Transcribe existing audio files
- **Supported formats**: MP3, WAV, OGG, M4A, FLAC
- **Multiple file selection**: Process multiple files in sequence
- **Same cleanup options**: File transcriptions use the same AI cleanup as live recordings

### Microphone Testing
- **Pre-recording test**: Test your microphone before recording
- **Visual level meter**: Real-time audio level display
- **Device verification**: Ensure your mic is working properly
- **Dedicated tab**: Separate Mic Test tab for quick checks

---

## Audio Processing

### Voice Activity Detection (VAD)
- **Silence removal**: Automatically strips silence before API upload
- **Silero VAD model**: Lightweight ONNX model (~1.4MB)
- **Cost reduction**: Smaller files = lower API costs
- **Faster uploads**: Less data to transfer
- **Optional**: Can be disabled in Settings → Behavior

**Technical Parameters:**
- Sample rate: 16kHz
- Window size: 512 samples (~32ms)
- Speech probability threshold: 0.5
- Minimum speech segment: 250ms
- Speech padding: 30ms

### Automatic Gain Control (AGC)
- **Level normalization**: Consistent audio levels for better transcription
- **Smart boosting**: Only boosts quiet audio, never attenuates loud audio
- **Target peak**: -3 dBFS (leaves headroom for good signal)
- **Minimum threshold**: -40 dBFS (avoids amplifying noise)
- **Maximum gain**: +20 dB (prevents over-amplification)

### Audio Compression
- **Downsampling**: 16kHz mono (matches Gemini's internal format)
- **WAV format**: For API upload
- **Opus archival**: Optional storage in highly compressed Opus format (~24kbps)
- **Storage efficiency**: ~180KB per minute of recording

### Audio Archival
- **Optional feature**: Enable in Settings → Behavior
- **Opus codec**: Speech-optimized compression
- **Storage location**: `~/.config/voice-notepad-v3/audio-archive/`
- **Linked to history**: Archived files are linked in transcript database
- **Small file sizes**: ~24kbps bitrate, very efficient

---

## AI Transcription

### Multimodal Approach
Voice Notepad uses **audio-capable multimodal models** that transcribe AND clean up in a single pass—no separate ASR step required.

**Why this matters:**
- The AI "hears" your tone, pauses, and emphasis
- Verbal editing works ("scratch that", "new paragraph")
- One API call instead of two
- Lower cost than separate ASR + LLM

### Supported AI Providers

#### OpenRouter (Recommended)
**Single API key for multiple models** with accurate per-key cost tracking.

| Model | Best For |
|-------|----------|
| **Gemini 2.5 Flash** | Fast, cost-effective, excellent quality |
| **Gemini 2.5 Flash Lite** | Ultra-low cost, quick notes |
| **Gemini 2.0 Flash** | Previous generation, still capable |
| **GPT-4o Audio Preview** | Premium quality, highest cost |
| **Voxtral Small** | Multilingual support |

#### Google AI (Direct)
Direct access to Gemini models.

| Model | Best For |
|-------|----------|
| **Gemini Flash Latest** | Auto-updates to newest Flash model |
| **Gemini 2.5 Flash** | Current generation |
| **Gemini 2.5 Flash Lite** | Lightweight, low cost |
| **Gemini 2.5 Pro** | Highest quality, expensive |

#### OpenAI
OpenAI's audio-capable models.

| Model | Best For |
|-------|----------|
| **GPT-4o Audio Preview** | Full GPT-4o with audio |
| **GPT-4o Mini Audio Preview** | Faster, cheaper variant |

#### Mistral AI
Mistral's Voxtral audio models.

| Model | Best For |
|-------|----------|
| **Voxtral Small Latest** | 24B parameters, multilingual |
| **Voxtral Mini Latest** | Smaller, faster variant |

### Cleanup Prompt Customization

Fully customizable via **Settings → Prompt**. Options include:

**Text Cleanup:**
1. Remove filler words (um, uh, like, etc.)
2. Remove verbal tics and hedging phrases (you know, I mean, etc.)
3. Remove standalone acknowledgments (Okay, Right, etc.)
4. Add proper punctuation and sentences
5. Add natural paragraph spacing

**Advanced Options:**
6. Follow verbal instructions in recording ("don't include this", "change this")
7. Add subheadings for lengthy transcriptions (optional)
8. Use markdown formatting like bold and lists (optional)
9. Remove unintentional dialogue (optional)
   - Only removes dialogue the AI can confidently detect as accidental
   - E.g., someone else speaking to you during recording

**Format Presets:**
- Standard transcription (default)
- Email draft
- To-do list
- Meeting notes
- Blog post
- Documentation

**Formality Levels:**
- Casual
- Neutral (default)
- Professional

**Verbosity Reduction:**
- None (keep everything)
- Moderate (default)
- Aggressive (maximum conciseness)

---

## User Interface

### Tabbed Interface
The app uses a modern tabbed interface with the following tabs:

#### 1. Record Tab
- Main recording interface
- Real-time status display
- Markdown editor with live preview
- Quick access to recording controls

#### 2. File Transcription Tab
- Upload audio files for transcription
- Multiple file selection
- Same cleanup options as live recording
- Progress tracking for file uploads

#### 3. History Tab
- Browse all past transcriptions
- **Full-text search** (FTS5) for fast queries
- Click to preview, double-click to load
- View metadata (duration, cost, model used)
- Delete individual transcriptions
- **Delete All History** button with warning dialog

#### 4. Cost Tab
- **OpenRouter balance**: Live credit balance (when using OpenRouter)
- **API key usage**: Daily, weekly, monthly spend for your specific key
- **Model breakdown**: Usage by model from OpenRouter activity API
- **Local statistics**: Transcription count, words, characters

#### 5. Analysis Tab
- **Summary stats**: Last 7 days of activity
- **Model performance**: Avg inference time, chars/sec
- **Storage usage**: Database size, archived audio size
- Performance comparison across models

#### 6. Models Tab
- Browse available models by provider
- Tier indicators (Free, Moderated Free, Paid)
- Model descriptions and capabilities
- Quick reference for model selection

#### 7. Mic Test Tab
- Test microphone before recording
- Visual audio level meter
- Real-time feedback
- Device verification

#### 8. About Tab
- App information and version
- Keyboard shortcuts reference
- Links to documentation
- License information

### Markdown Editor
- **Live preview**: See formatted text as you type
- **Source/preview toggle**: Switch between markdown source and rendered view
- **Copy button**: One-click copy to clipboard
- **Save button**: Export to file
- **Clear button**: Reset editor

---

## Cost Tracking

### OpenRouter (Recommended)
OpenRouter provides the most accurate cost tracking:

- **Key-specific usage**: Uses `/api/v1/key` endpoint for your specific API key (not account-wide)
- **Account balance**: Displayed in status bar and Cost tab via `/api/v1/credits`
- **Activity breakdown**: Model usage via `/api/v1/activity` endpoint (last 30 days)
- **Real costs**: Actual billed amounts, not estimates

### Status Bar Display
When using OpenRouter:
- **Today's spend**: `Today: $X.XXXX (N)`
  - N = number of transcriptions today
- **Account balance**: `Bal: $X.XX`
  - Remaining OpenRouter credit

### Cost Tab Features
- **Live balance**: OpenRouter credit balance (cached 60 seconds)
- **Time periods**: Hourly, daily, weekly, monthly spend
- **Model breakdown**: See which models cost the most
- **Local stats**: Transcription count, words, characters from database

### Per-Transcription Tracking
The database stores:
- Input/output token counts
- Estimated cost (actual for OpenRouter)
- Audio duration (original and after VAD)
- Inference time in milliseconds
- Text length and word count
- Prompt text length

**Note:** Only OpenRouter provides accurate key-specific cost data. Other providers show token-based estimates.

---

## Database & History

### SQLite Database
All transcriptions are stored locally in `~/.config/voice-notepad-v3/transcriptions.db`.

**Stored metadata:**
- Timestamp
- Provider and model used
- Transcript text
- Audio duration (original and after VAD)
- Inference time in milliseconds
- Token usage and cost
- Optional archived audio file path

### Full-Text Search (FTS5)
- **Fast searching**: SQLite FTS5 for instant search on large databases
- **Automatic indexing**: Enabled automatically on new and existing databases
- **Seamless fallback**: Uses LIKE queries if FTS is unavailable
- **Search as you type**: Results update in real-time

### Database Maintenance

#### Settings → Database Tab
New dedicated tab showing:
- **Total transcription count**
- **Database size**: Total size on disk
- **Archived audio size**: Total audio archive storage
- **FTS status**: Whether Full-Text Search is enabled
- **Optimize Database (VACUUM)** button to reclaim disk space
- **Refresh Statistics** button

#### VACUUM Operation
- **Reclaim space**: Removes unused disk space after deletions
- **Manual trigger**: Settings → Database tab
- **Automatic**: Runs after "Delete All History"
- **Safe operation**: Non-destructive database optimization

#### Delete All History
- **Red button** in History tab header
- **Comprehensive warning**: Shows what will be deleted
- **Automatic VACUUM**: Reclaims disk space after deletion
- **Success notification**: Shows deletion count

---

## Hotkeys & Shortcuts

### Global Hotkeys
System-wide keyboard shortcuts that work even when the app is minimized or unfocused.

**Configure in:** Settings → Hotkeys tab

#### Hotkey Modes

**1. Tap to Toggle Mode**
- **One key** toggles recording on/off
- **Separate key** stops and transcribes
- Best for quick note-taking

**2. Separate Start/Stop Mode**
- **Different keys** for Start, Stop (discard), and Stop & Transcribe
- More control over recording workflow
- Good for intentional recordings

**3. Push-to-Talk (PTT) Mode**
- **Hold a key** to record
- **Release to stop**
- Configurable action on release (transcribe or discard)
- Best for quick voice notes

#### Available Actions
- **Toggle Recording**: Start or stop recording
- **Start Recording**: Begin a new recording
- **Stop & Discard**: Stop and discard current recording
- **Stop & Transcribe**: Stop and send to AI
- **Push-to-Talk Key**: Hold to record, release to stop

#### Recommended Keys
**F14-F20** (macro keys) are suggested to avoid conflicts with other applications. These keys are available on keyboards with programmable macro keys.

**Supported Keys:**
- F1-F20 (function keys)
- Modifier combinations (Ctrl+, Alt+, Shift+, Super+)
- Media keys (on supported keyboards)

**Note:** On Wayland, global hotkeys work via XWayland compatibility layer.

### Application Shortcuts
Built-in keyboard shortcuts within the app:

- **Ctrl+R**: Start/stop recording
- **Ctrl+Return**: Stop recording and transcribe
- **Ctrl+C**: Copy transcript to clipboard
- **Ctrl+S**: Save transcript to file
- **Ctrl+L**: Clear editor
- **Ctrl+,**: Open settings (Linux/Windows)
- **Cmd+,**: Open settings (macOS)

---

## Settings & Configuration

### Configuration Storage
Settings are stored in `~/.config/voice-notepad-v3/config.json`.

### Settings Tabs

#### 1. General Tab
- **Provider selection**: Choose AI provider (OpenRouter, Gemini, OpenAI, Mistral)
- **Model selection**: Choose specific model within provider
- **API keys**: Enter API keys for each provider
- **Audio device**: Select microphone input

#### 2. Prompt Tab
- **Cleanup options**: Checkboxes for prompt components
- **Format preset**: Email, todo, meeting notes, etc.
- **Formality level**: Casual, neutral, professional
- **Verbosity reduction**: None, moderate, aggressive
- **Email signoff**: Optional signature for email format

#### 3. Behavior Tab
- **Enable VAD**: Toggle Voice Activity Detection
- **Archive audio**: Save recordings in Opus format
- **Audio feedback**: Enable beep notifications
- **Auto-copy to clipboard**: Automatically copy transcripts (planned)

#### 4. Hotkeys Tab
- **Hotkey mode**: Choose Tap to Toggle, Separate, or Push-to-Talk
- **Key assignments**: Set keys for each action
- **Suggested keys**: F14-F20 recommendations
- **Key capture**: Click field and press desired key

#### 5. Database Tab
- **Statistics**: View database and audio archive size
- **FTS status**: Check if Full-Text Search is enabled
- **VACUUM**: Optimize database to reclaim space
- **Refresh**: Update statistics

### Environment Variables
Alternative to storing API keys in settings:

```bash
OPENROUTER_API_KEY=your_key  # Recommended
GEMINI_API_KEY=your_key
OPENAI_API_KEY=your_key
MISTRAL_API_KEY=your_key
```

---

## Platform Support

### Linux
- **AppImage**: Universal, run on any distro
- **.deb**: Debian/Ubuntu packages
- **Tarball**: Portable archive
- **Wayland support**: Full compatibility with Wayland compositors
- **XWayland**: Global hotkeys work via XWayland layer

### Windows
- **Installer (.exe)**: Recommended, creates Start Menu shortcut
- **Portable (.zip)**: Extract and run anywhere
- **SmartScreen**: May show warning (open-source software without code signing)

### System Requirements
- **Python 3.9+**: Bundled in all packages
- **ffmpeg**: For audio processing
- **portaudio**: For microphone access
- **64-bit OS**: x86_64/amd64 architecture

---

## Related Documentation

- **[README.md](README.md)**: Quick start and installation
- **[CLAUDE.md](CLAUDE.md)**: Developer documentation
- **[CHANGELOG.md](CHANGELOG.md)**: Version history
- **[User Manual (PDF)](docs/manuals/Voice-Notepad-User-Manual-v1.pdf)**: Complete guide

## Related Resources

- [Audio-Multimodal-AI-Resources](https://github.com/danielrosehill/Audio-Multimodal-AI-Resources): Curated list of audio-capable AI models
- [Audio-Understanding-Test-Prompts](https://github.com/danielrosehill/Audio-Understanding-Test-Prompts): Test prompts for evaluating audio understanding
