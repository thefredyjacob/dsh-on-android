---
name: dsh-on-android
description: Install, repair, or reproduce DeepSeek Harness (DSH) on an Android phone in Termux. Covers the Android-specific native-loader, flock, hardlink, SELinux/DNS, localhost Web UI, sign-in, and sandbox workarounds.
---

# DSH on Android

Run the real DSH host on the phone. No APK, no PC, no Electron port. Termux runs Node; Chrome opens the DSH Web UI at `127.0.0.1:3080`.

> **Root is required for device control.** DSH itself runs unrooted, but `su`, `settings`, `svc`, `input`, `uiautomator`, `screencap`, and app management need Magisk root granted to Termux. Termux:API commands such as battery, toast, and notifications work without root.

## Status

Tested with:

| Part | Version |
|---|---|
| DSH | `0.2.2-rc.1` |
| Node | `25.3.0` (Termux; DSH requires `>=24.9`) |
| Android | 12, arm64 |
| Phone | Nubia NX669J / REDMAGIC 6S Pro |
| Termux | F-Droid build, Termux:API installed |
| Root | Magisk 30.7 — **required for device control**, optional for the DSH Web UI |

This is a community workaround, not an official Android build. DSH is in developer preview and updates can break the patches.

## What works

- DSH Web UI in mobile Chrome.
- Sessions, workspace, model login, API key, plugins, skills.
- Bash tool, file tools, approvals.
- Device control through Termux:API and `su -c`.
- UIAutomator, `input`, `screencap` for Android UI automation.

## What does not work out of the box

Android is not Linux desktop. Four DSH assumptions fail:

| Failure | Cause | Fix |
|---|---|---|
| `No usable native binding found for node-addon-require-builtin-android-arm64` | No Android binary in the optional package | JS fallback + launch Node with `--expose-internals` |
| `flock is not supported on android-arm64` | No Android `node-addon-system` binary | No-op advisory lock; one host process only |
| `EACCES: permission denied, link` in `dsh-fs-local` | Android blocks hardlinks under `/data/data` | Guarded `rename` fallback |
| `EACCES: permission denied, link` in `dsh-session-persistence-jsonl` | Same hardlink limitation | `rename` fallback after existence check |

A fifth trap is SELinux: a process started with `su 10147 -c ...` lands in `u:r:magisk:s0` and DNS stops resolving. Start sshd and DSH from the Termux app, not from a root shell.

Image attachments are not covered by the core patches. `dsh-attachment-local` also uses hardlinks, so image upload may still fail on Android. Text, sessions, workspaces, and the Bash tool are the tested path.

## Install as a DSH skill

```sh
mkdir -p "$HOME/.dsh/skills"
git clone https://github.com/thefredyjacob/dsh-on-android.git \
  "$HOME/.dsh/skills/dsh-on-android"
```

Restart DSH or refresh the skill catalog. The skill name is `dsh-on-android`.

## Prerequisites

- Android 12 or newer, arm64.
- Termux from F-Droid, not the obsolete Play Store build.
- Optional: Termux:API for battery, camera, SMS, location, notifications, torch.
- **Required for device control:** Magisk root, with Termux allowed in Magisk → Superuser.
- Network access for npm and DeepSeek login.

## Quick install

```sh
pkg install -y git
git clone https://github.com/thefredyjacob/dsh-on-android.git
cd dsh-on-android
bash scripts/install.sh
```

The installer installs Node, installs DSH, applies the four patches, and creates `~/bin/dsh-android`.

If the repo is not published yet, copy this directory to the phone and run `bash scripts/install.sh` there.

## Manual install

```sh
pkg update -y
pkg install -y nodejs git python

npm install -g --ignore-scripts --no-audit --no-fund @deepseek-ai/dsh@0.2.2-rc.1

python scripts/patch.py

cp scripts/dsh-android "$HOME/bin/dsh-android"
chmod 700 "$HOME/bin/dsh-android"
```

`--ignore-scripts` is required. DSH pulls `koffi`, which is only used on Windows but still tries to build during install. Skipping lifecycle scripts avoids the failed Windows build. The Linux path never imports `koffi`.

## Start DSH

```sh
mkdir -p "$HOME/dsh"
cd "$HOME/dsh"
nohup "$HOME/bin/dsh-android" --profile web --no-open --port 3080 --host 127.0.0.1 \
  > "$HOME/dsh-web.log" 2>&1 &
grep -o 'http://127.0.0.1:3080/?token=[A-Za-z0-9_-]*' "$HOME/dsh-web.log" | tail -1
```

Open that URL in Chrome on the phone. The token is exchanged for a cookie and the URL redirects to the app.

Do not run `dsh` directly. The wrapper adds `--expose-internals`, which the loader fallback needs.

## First run

1. Open the token URL.
2. Accept the preview notice.
3. Sign in with a DeepSeek account, or add an API key.
4. Pick a workspace. `~/dsh` works. If the UI reports “Unable to create default workspace”, create the directory and restart DSH from it.
5. Send `uname -a`.

## How the patches work

### 1. Native loader

DSH’s Cordis loader uses `node-addon-require-builtin` to reach Node internals. The package has no `android-arm64` binary.

The installer replaces `lib/index.js` with a small JS fallback and keeps the original as `index.js.bak`. With `--expose-internals`, Node resolves `internal/*` through normal `require`.

### 2. flock

`@deepseek-ai/node-addon-system/lib/flock.js` rejects any platform that is not Linux or macOS. Android is rejected.

The installer adds an early return for `process.platform === "android"`. This disables the advisory session-file lock. Run one DSH host per Termux install, not several.

### 3. fs-local hardlink

`dsh-fs-local` publishes a new file with `link(temp, target)` so an existing file is never overwritten. Android returns `EACCES` for hardlinks under `/data/data`.

The installer falls back to `rename` after `lstat` confirms the target is absent. The race window is tiny and acceptable for a single-user phone.

### 4. Session-file hardlink

`dsh-session-persistence-jsonl` uses the same hardlink pattern when it materializes `session.v4.jsonl.zstd`.

The installer adds `rename` to the imports and uses `rename(tmp, finalPath)` on Android. The package already checks that the target does not exist before this step.

## Android control

**Root is required for device control.** The DSH Web UI runs unrooted, and simple Termux:API commands work unrooted. Android control through `su`, `settings`, `svc`, `input`, `uiautomator`, `screencap`, and app management needs Magisk root granted to Termux.

```sh
# No root
termux-battery-status
termux-wifi-connectioninfo
termux-toast "hello"
termux-notification --title DSH --content done
termux-camera-photo -c 0 /sdcard/Download/photo.jpg

# Root
su -c id
su -c 'svc wifi enable'
su -c 'settings put system screen_brightness 128'
su -c 'input tap 540 1200'
su -c 'uiautomator dump /data/local/tmp/ui.xml'
su -c 'screencap -p /data/local/tmp/screen.png'
```

Put these rules in the workspace `AGENTS.md` so the agent knows the phone layout and safety rules. See `examples/AGENTS.md`.

## Sandbox and approvals

Android has no Landlock backend for DSH’s `workspace-write` sandbox. Every Bash call therefore asks for `danger-full-access`.

Options:

- **Allow once**: safest per command.
- **Full access** via the shield icon near the composer: no prompts, full shell.

Full access means the agent can run any command the Termux UID can run, including `su`. Treat it as real root access.

## SELinux and DNS

Check the process context:

```sh
cat /proc/self/attr/current
```

Expected:

```text
u:r:untrusted_app_27:s0:...
```

Bad:

```text
u:r:magisk:s0
```

A process started by `su 10147 -c ...` from ADB gets the Magisk context. It can reach IP addresses but DNS through Android netd fails with:

```text
curl: (6) Could not resolve host: api.deepseek.com
```

Start sshd and DSH from the Termux app or Termux:Boot. Do not start them by `su`-ing to the Termux UID from ADB.

## Verify

```sh
curl -sS -I https://api.deepseek.com
su -c id
```

Expected: HTTP response, not `Could not resolve host`; `uid=0(root)` if Magisk allows Termux.

Inside DSH:

```text
Run uname -a and id.
Run termux-battery-status.
Run su -c id.
Take a screenshot and save it to /sdcard/Download/dsh-test.png.
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `No usable native binding` | Run the wrapper, not `dsh`; rerun `patch.py` |
| `flock is not supported` | Rerun `patch.py`; restart DSH |
| `EACCES ... link` | Rerun `patch.py`; restart DSH |
| `curl: (6) Could not resolve host` | Restart sshd/DSH from Termux app context |
| `koffi` build failure during npm install | Use `--ignore-scripts` |
| `Unable to create default workspace` | `mkdir -p ~/dsh`; restart from that directory |
| Bash asks for full access | Expected; Android has no sandbox backend |
| `su: Permission denied` | Magisk → Superuser → Termux → Allow |
| Blank page after token URL | Check `~/dsh-web.log`; confirm port 3080 |

## Update

After `npm update -g @deepseek-ai/dsh`, rerun:

```sh
python scripts/patch.py
```

The patcher backs up each file once as `*.bak` and refuses to double-patch.

## Uninstall

```sh
pkill -f 'dsh/lib/bin.js --profile web'
npm uninstall -g @deepseek-ai/dsh
rm -f "$HOME/bin/dsh-android"
# Optional: remove state
rm -rf "$HOME/.dsh"
```

## Security

- DSH listens on `127.0.0.1` only. Do not bind `0.0.0.0`.
- The token URL grants local access. Do not paste it into chats or screenshots.
- SSH on `0.0.0.0:8022` exposes the phone to the LAN. Prefer key-only auth and a trusted network.
- Root + full access is equivalent to giving the model a root shell. Keep approvals on unless you accept that.
- The patches weaken atomic-create guarantees. Do not run multiple DSH hosts against the same state directory.

## Publish

```sh
git init
git add .
git commit -m "Add DSH on Android Termux skill"
gh repo create dsh-on-android --public --source=. --push
```

Suggested topics: `deepseek-harness`, `dsh`, `dsh-skill`, `termux`, `android`, `arm64`.

## Files

```text
SKILL.md                    this file
README.md                   repo landing page
LICENSE                     MIT
scripts/install.sh          install Node, DSH, patches, launcher
scripts/patch.py            idempotent Android patches
scripts/dsh-android         Node wrapper with --expose-internals
examples/AGENTS.md          phone control rules for DSH workspaces
```
