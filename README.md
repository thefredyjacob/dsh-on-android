# DSH on Android

Run [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) natively on an Android phone through Termux. No APK, no PC, no Electron port.

This is a community workaround for DSH `0.2.2-rc.1` on Android/arm64. It is not an official Android build.

> **Root is required for device control.** DSH itself runs unrooted, but `su`, `settings`, `svc`, `input`, `uiautomator`, `screencap`, and app management need Magisk root granted to Termux. Simple Termux:API commands work without root.

## Why this exists

DSH is a Node.js agent harness. Android can run Node, but four desktop assumptions break:

1. No `android-arm64` native loader binding.
2. No Android `flock` addon.
3. Android blocks hardlinks under `/data/data`.
4. A root-started process gets the Magisk SELinux context, which breaks DNS.

This skill packages the fixes and the exact setup steps.

## Quick start

Install as a DSH skill and run the installer:

```sh
pkg install -y git
mkdir -p "$HOME/.dsh/skills"
git clone https://github.com/thefredyjacob/dsh-on-android.git \
  "$HOME/.dsh/skills/dsh-on-android"
bash "$HOME/.dsh/skills/dsh-on-android/scripts/install.sh"
```

Then:

```sh
cd "$HOME/dsh"
nohup "$HOME/bin/dsh-android" --profile web --no-open --port 3080 --host 127.0.0.1 \
  > "$HOME/dsh-web.log" 2>&1 &
grep -o 'http://127.0.0.1:3080/?token=[A-Za-z0-9_-]*' "$HOME/dsh-web.log" | tail -1
```

Open that URL in Chrome on the phone, sign in to DeepSeek, send `uname -a`.

## Tested

| Part | Version |
|---|---|
| DSH | `0.2.2-rc.1` |
| Node | `25.3.0` |
| Android | 12, arm64 |
| Termux | F-Droid |
| Root | Magisk 30.7 — **required for device control** |

## What you get

- Full DSH Web UI, sessions, workspaces, plugins, skills.
- Bash and file tools.
- Termux:API device control for battery, camera, SMS, location, notifications, torch.
- **Root-required device control:** settings, radios, UIAutomator, screenshots, app management.
- Approval prompts for shell commands because Android has no Landlock sandbox.

## Security

- DSH binds `127.0.0.1` only.
- The token URL grants local access. Do not share it.
- Full access mode gives the model a real shell, including `su`.
- The patches weaken atomic-create and locking guarantees. Run one host only.

Read [SKILL.md](SKILL.md) for the full procedure, patch internals, and troubleshooting.

## License

MIT
