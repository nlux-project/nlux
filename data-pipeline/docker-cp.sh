#!/bin/bash
docker cp data/output/latest/export_fhm_0.jsonl nlux-api-1:/tmp/export_fhm_0.jsonl
docker cp data/output/latest/export_nha-c1477_0.jsonl nlux-api-1:/tmp/export_nha-c1477_0.jsonl 
docker cp data/output/latest/export_nha-c480_0.jsonl nlux-api-1:/tmp/export_nha-c480_0.jsonl
docker cp data/output/latest/export_nha-c587_0.jsonl nlux-api-1:/tmp/export_nha-c587_0.jsonl
docker cp data/output/latest/export_nha-c1477_0.jsonl nlux-api-1:/tmp/export_nha-c1477_0.jsonl
docker cp data/output/latest/export_nha-c480_0.jsonl nlux-api-1:/tmp/export_nha-c480_0.jsonl
docker cp data/output/latest/export_rbhc_0.jsonl nlux-api-1:/tmp/export_rbhc_0.jsonl
docker cp data/output/latest/export_rma_0.jsonl nlux-api-1:/tmp/export_rma_0.jsonl
docker cp data/output/latest/export_teylers_0.jsonl nlux-api-1:/tmp/export_teylers_0.jsonl
docker cp data/output/latest/export_wfm_0.jsonl nlux-api-1:/tmp/export_wfm_0.jsonl
echo "Loading data..."
docker exec nlux-api-1 python3 scripts/load_data.py /tmp/
