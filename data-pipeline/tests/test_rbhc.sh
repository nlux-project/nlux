#!/bin/bash
# Validates Rijksmuseum Boerhaave collection records and source-level API entities.

set -euo pipefail

cd /Users/lux/data-pipeline

# ----------------------------------------
# Test: Standaard metre, Etienne Lenoir Parijs, 1795
# ----------------------------------------
# /Users/lux/data-pipeline/data/input/rbhc/2.json
# http://localhost:8088/view/object/0a7994ef-d7db-4a0f-98c7-ade4ca77d8c1
# http://localhost:8000/data/object/0a7994ef-d7db-4a0f-98c7-ade4ca77d8c1
/bin/bash /Users/jsoeterbroek/Development/nlux-project/nlux/data-pipeline/tests/test_rbhc-pipeline.sh 2

# ----------------------------------------
# Test: Jaarmarkt van Gondreville
# ----------------------------------------
# /Users/lux/data-pipeline/data/input/rbhc/246.json
# http://localhost:8088/view/object/0021ca83-4150-4f7b-ae1c-ffce174cded3
# http://localhost:8000/data/object/0021ca83-4150-4f7b-ae1c-ffce174cded3
/bin/bash /Users/jsoeterbroek/Development/nlux-project/nlux/data-pipeline/tests/test_rbhc-pipeline.sh 246

# ----------------------------------------
# Test API search and resolvable references
# ----------------------------------------
TEST_PRIREF="2" RBHC_REQUIRE_LIVE=1 \
    uv run python -m unittest "tests.test_rbhc_pipeline.RbhcPipelineIntegrationTest.test_api_record_has_resolvable_collection_and_owner"

TEST_PRIREF="2" RBHC_REQUIRE_LIVE=1 \
    uv run python -m unittest "tests.test_rbhc_pipeline.RbhcPipelineIntegrationTest.test_api_search_finds_collection_and_owner"

# ----------------------------------------
# Test Set: Rijksmuseum Boerhaave collection
# ----------------------------------------
# http://localhost:8088/view/set/d1096be6-e742-5ad7-ac17-1fe71ac0a49e
# http://localhost:8000/data/set/d1096be6-e742-5ad7-ac17-1fe71ac0a49e
# preferred name: Rijksmuseum Boerhaave collection, type: named collection
RBHC_REQUIRE_LIVE=1 \
    uv run python -m unittest "tests.test_rbhc_pipeline.RbhcPipelineIntegrationTest.test_api_rbhc_collection_record"

# ----------------------------------------
# Test Person: Lenoir, Etienne
# ----------------------------------------
# http://localhost:8088/view/person/858f1a1f-6039-53d3-80f0-c48bb68f5a61
# http://localhost:8000/data/person/858f1a1f-6039-53d3-80f0-c48bb68f5a61
# birth present, value = 1822
# death present, value = 1900
RBHC_REQUIRE_LIVE=1 \
    uv run python -m unittest "tests.test_rbhc_pipeline.RbhcPipelineIntegrationTest.test_api_lenoir_person_record"
