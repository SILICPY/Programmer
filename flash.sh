#!/usr/bin/env bash

set -euo pipefail

(&>/dev/null platformio --version) || { echo "Error: platformio core is not installed."; exit 1; }

cd pio
pio run -t upload
