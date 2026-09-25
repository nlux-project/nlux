#!/bin/bash
# Validates WFM test records after each step — exits on first failure.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run the repo's tests with the repo's requirements; point PIPELINE_DIR at the
# deployed data location (harvest input, caches, export output).
cd "$SCRIPT_DIR/.."
export PIPELINE_DIR="${LUX_BASEPATH:-/Users/lux/data-pipeline}"
PYTHON_VERSION="${PYTHON_VERSION:-3.12}"
TEST_PY="uv run --python $PYTHON_VERSION --with-requirements requirements.txt python"

# ----------------------------------------
# Test: Foreest, Agatha van, Hoorn, Grote Oost 43
# ----------------------------------------
# /Users/lux/data-pipeline/data/input/wfm/82f55a96-de48-11e6-836d-d89d6717b464.json
# https://westfriesmuseum.com//detail/82f55a96-de48-11e6-836d-d89d6717b464/media/4d7b6891-63b4-fd44-151a-c45b7631decd?mode=detail
# http://localhost:8000/data/object/b5cb011d-daeb-4835-afe0-3925a5c87d20
# http://localhost:8088/view/object/b5cb011d-daeb-4835-afe0-3925a5c87d20
/bin/bash "$SCRIPT_DIR/test_wfm-pipeline.sh" 82f55a96-de48-11e6-836d-d89d6717b464


# ----------------------------------------
# Test: Oude vrouw achter raamomlijsting windt garen
# ----------------------------------------
# /Users/lux/data-pipeline/data/input/wfm/1a327c86-de49-11e6-836d-d89d6717b464.json
# https://westfriesmuseum.com//detail/1a327c86-de49-11e6-836d-d89d6717b464/media/3f2fc63c-9d2d-1040-6465-5b6801f1d74b?mode=detail
# http://localhost:8000/view/object/8690fd38-789e-41b4-9229-f7cecedba9d9
# http://localhost:8088/view/object/8690fd38-789e-41b4-9229-f7cecedba9d9
/bin/bash "$SCRIPT_DIR/test_wfm-pipeline.sh" 1a327c86-de49-11e6-836d-d89d6717b464


# ----------------------------------------
# Test Set: Westfries Museum collection
# ----------------------------------------
# http://localhost:8088/view/set/1084a0b1-9d14-5e2e-a373-c425c7746cd1
# http://localhost:8000/view/set/1084a0b1-9d14-5e2e-a373-c425c7746cd1
# preferred name: Westfries Museum collection, type : named collection
TEST_PRIREF="82f55a96-de48-11e6-836d-d89d6717b464" WFM_REQUIRE_LIVE=1 \
    $TEST_PY -m unittest "tests.test_wfm_pipeline.WfmPipelineIntegrationTest.test_api_wfm_collection_record"

# ----------------------------------------
# Test Person: Ouwater, Isaak 1747-1792
# ----------------------------------------
# http://localhost:8088/view/person/4209b862-359b-5e69-89fa-a65f4dfc764c
# http://localhost:8000/view/person/4209b862-359b-5e69-89fa-a65f4dfc764c
# biography present
# birth present, value = 12/31/1747
# death present, value = 12/31/1792
# wikipedia summary present
TEST_PRIREF="82f55a96-de48-11e6-836d-d89d6717b464" WFM_REQUIRE_LIVE=1 \
    $TEST_PY -m unittest "tests.test_wfm_pipeline.WfmPipelineIntegrationTest.test_api_ouwater_person_record"
