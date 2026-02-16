# File Transcription (Beta)

File Transcription lets you transcribe audio files from disk, rather than recording through your microphone.

## How to Access

File Transcription is available from the menu bar: **Beta → File Transcription...**

This opens a dedicated window for selecting and transcribing audio files.

## Usage

1. Open **Beta → File Transcription** from the menu bar
2. Browse for an audio file on your system
3. Click **Transcribe** to process the file
4. The transcribed and cleaned-up text appears in the output area

The same cleanup prompt, format presets, and model settings from the main app are applied to file transcriptions.

## Supported Formats

Any audio format supported by FFmpeg can be transcribed, including:
- WAV, MP3, FLAC, OGG, M4A, AAC, WMA, OPUS, WEBM

## Notes

- File transcription is a **Beta** feature and may have limitations with very long files
- The audio pipeline (AGC, VAD, compression) is applied to file audio the same way as microphone recordings
- Transcription results are saved to the history database with `source: "file"` for easy identification
- Large files may take longer to upload and process
