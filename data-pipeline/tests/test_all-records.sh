#!/bin/bash
# Validates WFM test records after each step — exits on first failure.

set -euo pipefail

cd /Users/lux/data-pipeline

/bin/bash /Users/jsoeterbroek/Development/nlux-project/nlux/data-pipeline/tests/test_wfm-record.sh
