#!/bin/bash
# Validates NHA C587 records after each step -- exits on first failure.

set -euo pipefail

cd /Users/lux/data-pipeline

TEST_NHA_C587_ID="${1:-F7DDF7EEFB8E11DF9E4D523BC2E286E2}"

echo "==> Testing NHA C587 ..."
echo "==> Testing mapper and fetcher configuration ..."
TEST_NHA_C587_ID="$TEST_NHA_C587_ID" NHA_C587_REQUIRE_LIVE=1 \
    uv run python -m unittest "tests.test_nha_pipeline.NhaC587PipelineIntegrationTest.test_fetcher_builds_filtered_memorix_requests"
TEST_NHA_C587_ID="$TEST_NHA_C587_ID" NHA_C587_REQUIRE_LIVE=1 \
    uv run python -m unittest "tests.test_nha_pipeline.NhaC587PipelineIntegrationTest.test_mapper_transforms_record"

/bin/bash /Users/jsoeterbroek/Development/nlux-project/nlux/data-pipeline/tests/test_nha-pipeline.sh "$TEST_NHA_C587_ID"
