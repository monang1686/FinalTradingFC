"""Offline synthetic multi-source demo; never fetches or persists third-party data."""
import json
from datetime import datetime, timezone
from pathlib import Path
from card_catalog import build_catalog
from metadata_fusion import merge_catalogs
from experimental_scanner import demo, scan

def build_demo():
    now=datetime(2026,11,17,12,0,tzinfo=timezone.utc)
    a=build_catalog([
        {"ea_id":900000001,"name":"CARTA TEST A","rating":88,"position":"ST"},
        {"ea_id":900000002,"name":"CARTA TEST B","rating":84,"position":"CM"},
    ],provenance="fixture-demo-catalog-a",authorized=True)
    b=build_catalog([
        {"ea_id":900000001,"club":"CLUB TEST 1","rarity":"TEST SPECIAL","rating":88},
        {"ea_id":900000002,"club":"CLUB TEST 2","rating":86},
    ],provenance="fixture-demo-catalog-b",authorized=True)
    result=scan(demo(now),now=now,metadata_catalog=merge_catalogs([a,b]))
    result["demo_notice"]="Solo dati sintetici: cataloghi, prezzi e opportunita inventati."
    return result

if __name__=="__main__":
    print(json.dumps(build_demo(),ensure_ascii=False,indent=2))
