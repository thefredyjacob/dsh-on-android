#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
export PATH="$PREFIX/bin:$PATH"

echo "== Termux packages =="
pkg update -y
pkg install -y nodejs git python

echo "== Node =="
node -v

echo "== DSH 0.2.2-rc.1 =="
npm install -g --ignore-scripts --no-audit --no-fund @deepseek-ai/dsh@0.2.2-rc.1

echo "== Android patches =="
python "$HERE/patch.py"

echo "== launcher =="
mkdir -p "$HOME/bin" "$HOME/dsh"
cp "$HERE/dsh-android" "$HOME/bin/dsh-android"
chmod 700 "$HOME/bin/dsh-android"
if [ ! -f "$HOME/dsh/AGENTS.md" ] && [ -f "$HERE/../examples/AGENTS.md" ]; then
  cp "$HERE/../examples/AGENTS.md" "$HOME/dsh/AGENTS.md"
fi

cat <<'EOF'

Installed.

Start:
  cd "$HOME/dsh"
  nohup "$HOME/bin/dsh-android" --profile web --no-open --port 3080 --host 127.0.0.1 > "$HOME/dsh-web.log" 2>&1 &
  grep -o 'http://127.0.0.1:3080/?token=[A-Za-z0-9_-]*' "$HOME/dsh-web.log" | tail -1

Open that URL in Chrome on the phone.

Root is required for device control. Grant Termux root in Magisk, then
verify with `su -c id`. DSH itself runs unrooted.
EOF
