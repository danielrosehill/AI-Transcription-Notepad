# Troubleshooting

## Audio Issues

**No microphone detected:** Check that your microphone is connected and recognized by running `pactl list sources short`. Ensure PipeWire or PulseAudio is running with `pactl info`. For USB microphones, verify device permissions with `ls -la /dev/snd/`.

**Recording not working:** Verify the correct input device is selected as the system default. Test the microphone in another application. Restart PipeWire with `systemctl --user restart pipewire`.

**Poor audio quality:** Position the microphone closer, reduce background noise, and check microphone gain in system settings.

## API Issues

**API key not working:** Verify the key is correct in Settings → API Keys. Check that the key has required permissions. Verify OpenRouter credits are available. Try setting the key via environment variable: `export OPENROUTER_API_KEY=your_key`.

**Transcription fails:** Check your internet connection, verify the API key is valid and has credits, try a different model (Gemini 3 Flash vs Pro), and check terminal output for error details. For large recordings, enable VAD to reduce file size.

**Rate limiting:** Wait a few minutes before trying again. OpenRouter has generous rate limits for most usage patterns.

## Installation Issues

**PyAudio installation fails:** Install PortAudio development headers with `sudo apt install portaudio19-dev`.

**Missing ffmpeg:** Install with `sudo apt install ffmpeg`.

**Qt platform plugin error:** Install the missing library with `sudo apt install libxcb-cursor0`.

## Global Hotkeys

**Hotkeys not working:** Check configuration in Settings → Hotkeys. On Wayland, ensure the user is in the `input` group for evdev access. Some keys may be captured by the desktop environment. Use F13-F24 (macro keys) to avoid conflicts.

## Text Injection (Auto-Paste)

**Text not pasting after transcription:** Text injection requires `ydotool` with a properly configured daemon. See the [Text Injection Setup Guide](text-injection.md) for detailed instructions.

**"ydotoold backend unavailable" warning:** The ydotool daemon is not running or is running as root instead of your user. Kill any existing daemon and restart as your user:
```bash
sudo pkill ydotoold
sudo rm -f /tmp/.ydotool_socket
ydotoold &
```

**Socket permission issues:** Check that `/tmp/.ydotool_socket` is owned by your user, not root:
```bash
ls -la /tmp/.ydotool_socket
```

For complete setup instructions, see [Text Injection Setup](text-injection.md).

## Database Issues

**History not showing:** Check that the Mongita database directory exists at `~/.config/voice-notepad-v3/mongita/` and verify write permissions on the config directory.

**Cost data missing:** Verify the OpenRouter API key has access to usage endpoints. Check that files exist in `~/.config/voice-notepad-v3/usage/`.

## Getting Help

Check [GitHub Issues](https://github.com/danielrosehill/AI-Transcription-Notepad/issues) for similar problems. When opening a new issue, include steps to reproduce, error messages from terminal, system information, and the model being used.
