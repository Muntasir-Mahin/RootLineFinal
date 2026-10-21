#!/usr/bin/env bash
# Linux/macOS source build. Requires Python 3.12+, git, curl, a C++ compiler,
# make, and ffmpeg. Keep native tools and downloaded models out of Git.
set -euo pipefail
rootline_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$rootline_root"
case "${1:-}" in
  ''|--tools-only) ;;
  *) echo 'Usage: bash scripts/setup_voice.sh [--tools-only]' >&2; exit 2 ;;
esac
command -v ffmpeg >/dev/null || { echo 'Install ffmpeg first (brew install ffmpeg on macOS; apt install ffmpeg on Debian/Ubuntu).' >&2; exit 1; }
rootline_tools=${ROOTLINE_VOICE_TOOLS:-"$rootline_root/work/voice-runtime"}
mkdir -p "$rootline_tools" local_models work
if [[ ! -x "$rootline_tools/whisper.cpp/build/bin/whisper-cli" ]]; then
  python3 -m venv "$rootline_tools/venv"
  "$rootline_tools/venv/bin/python" -m pip install 'cmake==4.4.4'
  if [[ ! -d "$rootline_tools/whisper.cpp" ]]; then
    git clone --depth 1 --branch v1.8.2 https://github.com/ggml-org/whisper.cpp.git "$rootline_tools/whisper.cpp"
  fi
  [[ $(git -C "$rootline_tools/whisper.cpp" rev-parse HEAD) == 4979e04f5dcaccb36057e059bbaed8a2f5288315 ]] || { echo 'Unexpected whisper.cpp version; inspect your tools directory.' >&2; exit 1; }
  "$rootline_tools/venv/bin/cmake" -S "$rootline_tools/whisper.cpp" -B "$rootline_tools/whisper.cpp/build" -DCMAKE_BUILD_TYPE=Release -DGGML_NATIVE=OFF -DGGML_CUDA=OFF -DWHISPER_BUILD_TESTS=OFF -DWHISPER_BUILD_SERVER=OFF
  "$rootline_tools/venv/bin/cmake" --build "$rootline_tools/whisper.cpp/build" --target whisper-cli -j 2
fi
"$rootline_tools/whisper.cpp/build/bin/whisper-cli" --help >/dev/null 2>&1
# Only paths, never credential values, are written here.
{
  printf 'export WHISPER_CLI=%q\n' "$rootline_tools/whisper.cpp/build/bin/whisper-cli"
  printf 'export WHISPER_MODEL_PATH=%q\n' "$rootline_root/local_models/ggml-small.bin"
} > work/voice.env
if [[ "${1:-}" == --tools-only ]]; then
  echo 'Native voice tools ready. Speech model was not downloaded (--tools-only).'
  exit 0
fi
rootline_model="$rootline_root/local_models/ggml-small.bin"
verify_model() {
  # Official whisper.cpp v1.8.2 models/README.md lists this SHA-1 for small.
  python3 - "$1" <<'PY'
import hashlib
import sys
from pathlib import Path
path = Path(sys.argv[1])
if not path.is_file():
    raise SystemExit(1)
with path.open('rb') as model:
    digest = hashlib.file_digest(model, 'sha1').hexdigest()
raise SystemExit(0 if digest == '55356645c2b361a969dfd0ef2c5a50d530afd8d5' else 1)
PY
}
if ! verify_model "$rootline_model"; then
  rootline_download=$(mktemp "$rootline_root/local_models/small-download.XXXXXX")
  trap 'rm -f -- "$rootline_download"' EXIT
  curl --fail --location --retry 2 --output "$rootline_download" 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin'
  verify_model "$rootline_download" || { echo 'Speech model checksum did not match; existing model was preserved.' >&2; exit 1; }
  mv -- "$rootline_download" "$rootline_model"
  trap - EXIT
fi
. work/voice.env
.venv/bin/python manage.py check_voice
echo 'Restart Django after sourcing work/voice.env, then select Check connection on Ask RootLine.'
