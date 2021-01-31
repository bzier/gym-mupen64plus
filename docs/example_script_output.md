## Example output
Here is an example of the output to expect from the `example.py` sample script. See the [README](../README.md) for details.

```
[2021-01-30 22:24:24,030] Making new env: Mario-Kart-Luigi-Raceway-v0
validate sub
('ControllerHTTPServer started on port ', 8082)
Initially on DISPLAY :0
Starting xvfb with command: ['Xvfb', ':0', '-screen', '0', '640x480x24', '-fbdir', '/dev/shm']

Using DISPLAY :0
Changed to DISPLAY :0
Starting emulator with comand: ['vglrun', '-d', ':0', 'mupen64plus', '--nospeedlimit', '--nosaveoptions', '--resolution', '640x480', '--gfx', 'mupen64plus-video-glide64.so', '--audio', 'dummy', '--input', '/usr/local/lib/mupen64plus/mupen64plus-input-bot.so', '/src/gym-mupen64plus/gym_mupen64plus/ROMs/marioKart.n64']
Calling mss.mss() with DISPLAY :0
 __  __                         __   _  _   ____  _             
|  \/  |_   _ _ __   ___ _ __  / /_ | || | |  _ \| |_   _ ___ 
| |\/| | | | | '_ \ / _ \ '_ \| '_ \| || |_| |_) | | | | / __|  
| |  | | |_| | |_) |  __/ | | | (_) |__   _|  __/| | |_| \__ \  
|_|  |_|\__,_| .__/ \___|_| |_|\___/   |_| |_|   |_|\__,_|___/  
             |_|         http://code.google.com/p/mupen64plus/  
Mupen64Plus Console User-Interface Version 2.5.0

UI-Console: attached to core library 'Mupen64Plus Core' version 2.5.0
UI-Console:             Includes support for Dynamic Recompiler.
UI-Console:             Includes support for MIPS r4300 Debugger.
Core: Couldn't open configuration file '/root/.config/mupen64plus/mupen64plus.cfg'.  Using defaults.
Core Warning: No version number in 'Core' config section. Setting defaults.
Core Warning: No version number in 'CoreEvents' config section. Setting defaults.
UI-Console Warning: No version number in 'UI-Console' config section. Setting defaults.
Core: Goodname: Mario Kart 64 (U) [!]
Core: Name: MARIOKART64         
Core: MD5: 3A67D9986F54EB282924FCA4CD5F6DFF
Core: CRC: 3E5055B6 2E92DA52
Core: Imagetype: .v64 (byteswapped)
Core: Rom size: 12582912 bytes (or 12 Mb or 96 Megabits)
Core: Version: 1446
Core: Manufacturer: Nintendo
Core: Country: USA
UI-Console Status: Cheat codes disabled.
UI-Console: using Video plugin: 'Glide64 Video Plugin' v2.0.0
UI-Console: using Audio plugin: <dummy>
Input: Mupen64Plus Bot Input Plugin version 0.0.1 startup.
UI-Console: using Input plugin: 'Mupen64Plus Bot Input Plugin' v0.0.1
UI-Console: using RSP plugin: 'Hacktarux/Azimer High-Level Emulation RSP Plugin' v2.5.0
Video: SSE detected.

Input: InitiateControllers
Input: Reading Input-Bot-Control0
Input Warning: Missing 'plugged' parameter. Set to 1
Input Warning: Missing 'host' parameter. Setting to localhost
Input Warning: missing 'port' parameter. Set to 8082
Input: Reading Input-Bot-Control1
Input Warning: Missing 'plugged' parameter. Set to 0
Input: Reading Input-Bot-Control2
Input Warning: Missing 'plugged' parameter. Set to 0
Input: Reading Input-Bot-Control3
Input Warning: Missing 'plugged' parameter. Set to 0
Input: Mupen64Plus Bot Input Plugin version 0.0.1 initialized.
Core Warning: No audio plugin attached.  There will be no sound output.
Video: opening /usr/share/games/mupen64plus/Glide64.ini

Video: opening /usr/share/games/mupen64plus/Glide64.ini

Video: fb_clear 0 fb_smart 0

Video: extensions 'CHROMARANGE TEXCHROMA TEXMIRROR PALETTE6666 FOGCOORD EVOODOO TEXTUREBUFFER TEXFMT'

Video: fb_hires

Core: Setting video mode: 640x480
Video: Congratulations, you have 8 auxiliary buffers, we'll use them wisely !

Video: packed pixels extension used

Video: NPOT extension used

Video: use_fbo 0

Video:  --> bias factor 32768

Video: num_tmu 2

Video: tbuf_size 2Mb

Core: Starting R4300 emulator: Dynamic Recompiler
Core: R4300: starting 64-bit dynamic recompiler at: 0x7fd8627726e0
Video: opening /usr/share/games/mupen64plus/Glide64.ini

Video: ucode = 1

Changed back to DISPLAY :0
Player row: 0
Player col: 0
Map series: 0
Map choice: 0
Reset called!
NOOP waiting for green light
GO! ...drive straight as fast as possible...
Doughnuts!!
Step 0
Step 100
Step 200
Step 300
...
```
