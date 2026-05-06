#!/bin/bash
# Validates WFM test records after each step — exits on first failure.

set -euo pipefail

cd /Users/lux/data-pipeline

# ----------------------------------------
# Foreest, Agatha van, Hoorn, Grote Oost 43
# ----------------------------------------
# /Users/lux/data-pipeline/data/input/wfm/82f55a96-de48-11e6-836d-d89d6717b464.json
# https://westfriesmuseum.com//detail/82f55a96-de48-11e6-836d-d89d6717b464/media/4d7b6891-63b4-fd44-151a-c45b7631decd?mode=detail
# http://localhost:8000/data/object/b5cb011d-daeb-4835-afe0-3925a5c87d20
# http://localhost:8088/view/object/b5cb011d-daeb-4835-afe0-3925a5c87d20
/bin/bash /Users/jsoeterbroek/Development/nlux-project/nlux/data-pipeline/tests/test_wfm-pipeline.sh 82f55a96-de48-11e6-836d-d89d6717b464


# ----------------------------------------
# Oude vrouw achter raamomlijsting windt garen
# ----------------------------------------
# /Users/lux/data-pipeline/data/input/wfm/1a327c86-de49-11e6-836d-d89d6717b464.json
# https://westfriesmuseum.com//detail/1a327c86-de49-11e6-836d-d89d6717b464/media/3f2fc63c-9d2d-1040-6465-5b6801f1d74b?mode=detail
# http://localhost:8000/view/object/8690fd38-789e-41b4-9229-f7cecedba9d9
# http://localhost:8088/view/object/8690fd38-789e-41b4-9229-f7cecedba9d9
/bin/bash /Users/jsoeterbroek/Development/nlux-project/nlux/data-pipeline/tests/test_wfm-pipeline.sh 1a327c86-de49-11e6-836d-d89d6717b464
