#!/bin/bash
# Validates Rijksmuseum Amsterdam test records after each step.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run the repo's tests with the repo's requirements; point PIPELINE_DIR at the
# deployed data location (harvest input, caches, export output).
cd "$SCRIPT_DIR/.."
export PIPELINE_DIR="${LUX_BASEPATH:-/Users/lux/data-pipeline}"
PYTHON_VERSION="${PYTHON_VERSION:-3.12}"
TEST_PY="uv run --python $PYTHON_VERSION --with-requirements requirements.txt python"

# ----------------------------------------
# Test Object: De Nachtwacht / The Night Watch
# ----------------------------------------
# Rijksmuseum object number: SK-C-5
# Rijksmuseum Linked Art id: https://id.rijksmuseum.nl/200107928
# Public page: https://www.rijksmuseum.nl/nl/collectie/SK-C-5
/bin/bash "$SCRIPT_DIR/test_rma-pipeline.sh" 200107928

# ----------------------------------------
# Test API search and resolvable references
# ----------------------------------------
TEST_RMA_ID="200107928" RMA_REQUIRE_LIVE=1 \
    $TEST_PY -m unittest "tests.test_rma_pipeline.RmaPipelineIntegrationTest.test_api_record"

TEST_RMA_ID="200107928" RMA_REQUIRE_LIVE=1 \
    $TEST_PY -m unittest "tests.test_rma_pipeline.RmaPipelineIntegrationTest.test_api_search_finds_night_watch"

# ----------------------------------------
# Test Set: Rijksmuseum Amsterdam
# ----------------------------------------
TEST_RMA_ID="200107928" RMA_REQUIRE_LIVE=1 \
    $TEST_PY -m unittest "tests.test_rma_pipeline.RmaPipelineIntegrationTest.test_api_rma_collection_record"
