#!/bin/bash
# Validates WFM test records after each step — exits on first failure.

set -euo pipefail

cd /Users/lux/data-pipeline

/bin/bash /Users/jsoeterbroek/Development/nlux-project/nlux/data-pipeline/tests/test_fhm.sh
/bin/bash /Users/jsoeterbroek/Development/nlux-project/nlux/data-pipeline/tests/test_hvh.sh
/bin/bash /Users/jsoeterbroek/Development/nlux-project/nlux/data-pipeline/tests/test_rbhc.sh
/bin/bash /Users/jsoeterbroek/Development/nlux-project/nlux/data-pipeline/tests/test_teylers.sh
/bin/bash /Users/jsoeterbroek/Development/nlux-project/nlux/data-pipeline/tests/test_wfm.sh
