#!/data/data/com.termux/files/usr/bin/bash
set -e

cd "$HOME/s43_refactor"

ts="$(date +%Y%m%d_%H%M%S)"
snapdir="$HOME/s43_refactor/snapshots"
outdir="/sdcard/Download"

mkdir -p "$snapdir"
mkdir -p "$outdir"

if [ ! -f "s43.py" ]; then
  echo "ERROR: s43.py not found"
  exit 1
fi

cp -p "s43.py" "$snapdir/s43_${ts}.py"

if [ -f "s43_instrumented.py" ]; then
  cp -p "s43_instrumented.py" "$snapdir/s43_instrumented_${ts}.py"
fi

tar -czf "$snapdir/s43_snapshot_${ts}.tar.gz" s43.py s43_instrumented.py 2>/dev/null || tar -czf "$snapdir/s43_snapshot_${ts}.tar.gz" s43.py

sha256sum "$snapdir/s43_${ts}.py" > "$snapdir/s43_${ts}.sha256"

cp -f "$snapdir/s43_${ts}.py" "$outdir/s43_LATEST.py"
cp -f "$snapdir/s43_${ts}.sha256" "$outdir/s43_LATEST.sha256"
cp -f "$snapdir/s43_snapshot_${ts}.tar.gz" "$outdir/s43_LATEST.tar.gz"

cp -f "$snapdir/s43_${ts}.py" "$outdir/s43_${ts}.py"
cp -f "$snapdir/s43_${ts}.sha256" "$outdir/s43_${ts}.sha256"
cp -f "$snapdir/s43_snapshot_${ts}.tar.gz" "$outdir/s43_snapshot_${ts}.tar.gz"

if [ -f "$snapdir/s43_instrumented_${ts}.py" ]; then
  cp -f "$snapdir/s43_instrumented_${ts}.py" "$outdir/s43_instrumented_LATEST.py"
  cp -f "$snapdir/s43_instrumented_${ts}.py" "$outdir/s43_instrumented_${ts}.py"
fi

echo "CHECKPOINT_OK $ts"
echo "PHONE_SOURCE $HOME/s43_refactor/s43.py"
echo "PHONE_SNAPSHOT $snapdir/s43_${ts}.py"
echo "EXPORT_LATEST $outdir/s43_LATEST.py"
echo "EXPORT_ARCHIVE $outdir/s43_LATEST.tar.gz"
echo "SHA256 $(cat "$snapdir/s43_${ts}.sha256")"
