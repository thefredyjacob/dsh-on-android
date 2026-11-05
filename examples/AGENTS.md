# Android host

This DSH instance runs inside Termux on the phone itself. Android 12+, arm64.
Magisk root is required for device control: settings, radios, UI injection,
app management, screenshots, and `su`. DSH itself runs unrooted.

## Environment

- Termux prefix: `/data/data/com.termux/files/usr`
- Home: `/data/data/com.termux/files/home`
- If a command is missing: `export PATH=$PREFIX/bin:$PATH`
- Shared storage: `/sdcard` (run `termux-setup-storage` once if needed).

## Control order

1. Termux:API for hardware and user-facing features.
2. Root shell `su -c '...'` for protected settings, radios, UI injection, app management.
3. UIAutomator and `input` for UI automation.
4. No on-device `adb`; do not assume it exists.

If `su -c id` returns `Permission denied`, ask the user to grant Termux root in
Magisk -> Superuser.

## Device / battery / network

```sh
termux-battery-status
termux-wifi-connectioninfo
termux-telephony-deviceinfo
termux-audio-info
getprop ro.product.model
```

## Screen and UI

```sh
su -c 'screencap -p /data/local/tmp/screen.png'
su -c 'uiautomator dump /data/local/tmp/ui.xml'
su -c 'cat /data/local/tmp/ui.xml'
su -c 'input tap 540 1200'
su -c 'input swipe 540 1800 540 600 300'
su -c 'input text "hello"'
su -c 'input keyevent KEYCODE_HOME'
su -c 'input keyevent KEYCODE_BACK'
```

Copy screenshots somewhere readable:

```sh
su -c 'cp /data/local/tmp/screen.png /sdcard/Download/screen.png'
```

## Apps

```sh
pm list packages
monkey -p com.android.settings 1
su -c 'am force-stop com.example.app'
su -c 'pm uninstall --user 0 com.example.app'
```

## Settings / radios

```sh
su -c 'svc wifi enable'
su -c 'svc wifi disable'
su -c 'svc data enable'
su -c 'svc bluetooth enable'
su -c 'cmd connectivity airplane-mode enable'
su -c 'settings put system screen_brightness 128'
su -c 'settings get system screen_brightness'
```

## Termux:API

```sh
termux-toast "hello"
termux-notification --title DSH --content "task done"
termux-clipboard-get
termux-clipboard-set "text"
termux-volume
termux-brightness 128
termux-torch on
termux-camera-photo -c 0 /sdcard/Download/photo.jpg
termux-location -p network
termux-sms-list -l 5
termux-contact-list
termux-media-player play /sdcard/Download/audio.mp3
termux-tts-speak "hello"
```

## Safety

- Ask before destructive actions: uninstall, clear app data, factory reset, reboot, flashing, deleting files outside the workspace.
- Never `rm -rf` `/`, `/sdcard`, `/data`, or the Termux prefix.
- Do not expose the DSH port to the LAN.
- Read the UI tree before tapping coordinates.
- Keep a short audit trail of root commands in the reply.
