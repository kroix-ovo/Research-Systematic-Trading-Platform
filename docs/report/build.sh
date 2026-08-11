#!/usr/bin/env bash
# Build the verified research report PDF.
#   ./build.sh          assemble the PDF from existing results
#   ./build.sh --all    re-run verification and figures first (~8 min)
set -euo pipefail
export PATH="/opt/homebrew/bin:$PATH"
cd "$(dirname "$0")"

if [[ "${1:-}" == "--all" ]]; then
  echo "==> verification suite"
  python3 verify/run_all.py
  echo "==> figures"
  python3 figures/fig_math.py
  python3 figures/fig_systems.py
  python3 figures/fig_verify.py
fi

echo "==> LaTeX tables from verification results"
python3 gen_tables.py

echo "==> pandoc -> PDF"
pandoc report.md \
  --from=markdown+raw_tex+tex_math_dollars+pipe_tables+yaml_metadata_block \
  --to=pdf \
  --pdf-engine=tectonic \
  --include-in-header=preamble.tex \
  --resource-path=.:figures \
  --toc-depth=2 \
  --number-sections \
  -V documentclass=article \
  -V papersize=a4 \
  -V fontsize=10pt \
  -V geometry:"margin=2.1cm,top=2.4cm,bottom=2.2cm" \
  -V linkcolor=black \
  -V colorlinks=false \
  -o "Deterministic-Quant-Platform-Verified-Edition.pdf"

echo "==> done: $(ls -lh Deterministic-Quant-Platform-Verified-Edition.pdf | awk '{print $5}')"
