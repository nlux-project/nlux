#!/bin/bash
# Validates NHA C587 records after each step -- exits on first failure.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run the repo's tests with the repo's requirements; point PIPELINE_DIR at the
# deployed data location (harvest input, caches, export output).
cd "$SCRIPT_DIR/.."
export PIPELINE_DIR="${LUX_BASEPATH:-/Users/lux/data-pipeline}"
PYTHON_VERSION="${PYTHON_VERSION:-3.12}"
TEST_PY="uv run --python $PYTHON_VERSION --with-requirements requirements.txt python"

TEST_NHA_C587_ID1="${1:-F7DDF7EEFB8E11DF9E4D523BC2E286E2}"
TEST_NHA_C587_ID2="${1:-F7A6959CFB8E11DF9E4D523BC2E286E2}"

echo "==> Testing NHA C587 ..."
echo "==> Testing mapper and fetcher configuration ..."
TEST_NHA_C587_ID="$TEST_NHA_C587_ID1" NHA_C587_REQUIRE_LIVE=1 \
    $TEST_PY -m unittest "tests.test_nha_pipeline.NhaC587PipelineIntegrationTest.test_fetcher_builds_filtered_memorix_requests"
TEST_NHA_C587_ID="$TEST_NHA_C587_ID1" NHA_C587_REQUIRE_LIVE=1 \
    $TEST_PY -m unittest "tests.test_nha_pipeline.NhaC587PipelineIntegrationTest.test_mapper_transforms_record"
TEST_NHA_C480_ID="65B76D9AFB8F11DF9E4D523BC2E286E2" NHA_C480_REQUIRE_LIVE=1 \
    $TEST_PY -m unittest "tests.test_nha_pipeline.NhaC480PipelineIntegrationTest.test_fetcher_builds_filtered_memorix_requests"
TEST_NHA_C480_ID="65B76D9AFB8F11DF9E4D523BC2E286E2" NHA_C480_REQUIRE_LIVE=1 \
    $TEST_PY -m unittest "tests.test_nha_pipeline.NhaC480PipelineIntegrationTest.test_mapper_transforms_record"
TEST_NHA_C1477_ID="65B76D9AFB8F11DF9E4D523BC2E286E2" NHA_C1477_REQUIRE_LIVE=1 \
    $TEST_PY -m unittest "tests.test_nha_pipeline.NhaC1477PipelineIntegrationTest.test_fetcher_builds_filtered_memorix_requests"
TEST_NHA_C1477_ID="65B76D9AFB8F11DF9E4D523BC2E286E2" NHA_C1477_REQUIRE_LIVE=1 \
    $TEST_PY -m unittest "tests.test_nha_pipeline.NhaC1477PipelineIntegrationTest.test_mapper_transforms_record_with_c1477_collection_label"

/bin/bash "$SCRIPT_DIR/test_nha-pipeline.sh" "$TEST_NHA_C587_ID1"
/bin/bash "$SCRIPT_DIR/test_nha-pipeline.sh" "$TEST_NHA_C587_ID2"

# ----------------------------------------
# Test Person: Maarten van Heemskerk
# ----------------------------------------
# The C587 portrait object should also produce a searchable Person result.
NHA_C587_REQUIRE_LIVE=1 \
    $TEST_PY -m unittest "tests.test_nha_pipeline.NhaC587PipelineIntegrationTest.test_api_mvanheemskerk_person_record"
