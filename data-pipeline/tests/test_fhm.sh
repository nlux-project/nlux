#!/bin/bash
# Validates FHM test records after each step — exits on first failure.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run the repo's tests with the repo's requirements; point PIPELINE_DIR at the
# deployed data location (harvest input, caches, export output).
cd "$SCRIPT_DIR/.."
export PIPELINE_DIR="${LUX_BASEPATH:-/Users/lux/data-pipeline}"
PYTHON_VERSION="${PYTHON_VERSION:-3.12}"
TEST_PY="uv run --python $PYTHON_VERSION --with-requirements requirements.txt python"

# ----------------------------------------
# Test: De poort van het hofje van Bakenes
# ----------------------------------------
# /Users/lux/data-pipeline/data/input/fhm/13646.json
# http://localhost:8088/view/object/f3f14350-0e94-46de-a596-b373cb1d958d
# http://localhost:8000/view/object/f3f14350-0e94-46de-a596-b373cb1d958d
/bin/bash "$SCRIPT_DIR/test_fhm-pipeline.sh" 13646


# ----------------------------------------
# Test: Portret van een onbekende vrouw met een boek
# ----------------------------------------
# /Users/lux/data-pipeline/data/input/fhm/14492.json
# http://localhost:8088/view/object/e94da0da-ba10-4bb0-9fd7-7bce01007a73
# http://localhost:8000/view/object/e94da0da-ba10-4bb0-9fd7-7bce01007a73
/bin/bash "$SCRIPT_DIR/test_fhm-pipeline.sh" 14492

# ----------------------------------------
# Test API search and resolvable references
# ----------------------------------------
FHM_REQUIRE_LIVE=1 \
    $TEST_PY -m unittest "tests.test_fhm_pipeline.FhmPipelineIntegrationTest.test_api_record_has_resolvable_collection_and_owner"

FHM_REQUIRE_LIVE=1 \
    $TEST_PY -m unittest "tests.test_fhm_pipeline.FhmPipelineIntegrationTest.test_api_search_finds_collection_and_owner"

# ----------------------------------------
# Test Set: Frans Hals Museum collection
# ----------------------------------------
# http://localhost:8088/view/set/4f324cd4-f0f2-552d-b0fd-681fda62d099
# http://localhost:8000/data/set/4f324cd4-f0f2-552d-b0fd-681fda62d099
# preferred name: Frans Hals Museum collection, type: named collection
FHM_REQUIRE_LIVE=1 \
    $TEST_PY -m unittest "tests.test_fhm_pipeline.FhmPipelineIntegrationTest.test_api_fhm_collection_record"

# ----------------------------------------
# Test Person: Wybrand Hendriks
# ----------------------------------------
# http://localhost:8088/view/person/5b6e8be2-3caf-5210-87e6-a5d53e10882d
# http://localhost:8000/data/person/5b6e8be2-3caf-5210-87e6-a5d53e10882d
# biography present
# birth present, value = 1744
# death present, value = 1831
# wikipedia summary present
FHM_REQUIRE_LIVE=1 \
    $TEST_PY -m unittest "tests.test_fhm_pipeline.FhmPipelineIntegrationTest.test_api_whendriks_person_record"
