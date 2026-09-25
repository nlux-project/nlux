#!/bin/bash
# Runs every per-source validation suite — exits on the first failure.
# Note: the per-source suites expect a running environment
# (API container, pipeline services and $LUX_BASEPATH data).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

/bin/bash "$SCRIPT_DIR/test_fhm.sh"
/bin/bash "$SCRIPT_DIR/test_hvh.sh"
/bin/bash "$SCRIPT_DIR/test_nha.sh"
/bin/bash "$SCRIPT_DIR/test_rbhc.sh"
/bin/bash "$SCRIPT_DIR/test_teylers.sh"
/bin/bash "$SCRIPT_DIR/test_wfm.sh"