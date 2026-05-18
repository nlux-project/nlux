#!/bin/bash
# Validates Rijksmuseum Amsterdam test records after each step.

set -euo pipefail

cd /Users/lux/data-pipeline

# ----------------------------------------
# Test Object: De Nachtwacht / The Night Watch
# ----------------------------------------
# Rijksmuseum object number: SK-C-5
# Rijksmuseum Linked Art id: https://id.rijksmuseum.nl/200107928
# Public page: https://www.rijksmuseum.nl/nl/collectie/SK-C-5
/bin/bash /Users/jsoeterbroek/Development/nlux-project/nlux/data-pipeline/tests/test_rma-pipeline.sh 200107928

# ----------------------------------------
# Test API search and resolvable references
# ----------------------------------------
TEST_RMA_ID="200107928" RMA_REQUIRE_LIVE=1 \
    uv run python -m unittest "tests.test_rma_pipeline.RmaPipelineIntegrationTest.test_api_record"

TEST_RMA_ID="200107928" RMA_REQUIRE_LIVE=1 \
    uv run python -m unittest "tests.test_rma_pipeline.RmaPipelineIntegrationTest.test_api_search_finds_night_watch"

# ----------------------------------------
# Test Set: Rijksmuseum Amsterdam
# ----------------------------------------
TEST_RMA_ID="200107928" RMA_REQUIRE_LIVE=1 \
    uv run python -m unittest "tests.test_rma_pipeline.RmaPipelineIntegrationTest.test_api_rma_collection_record"
