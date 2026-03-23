#!/bin/bash
# Test script for the FastAPI application

echo "=== Testing Krankenkassen Info API ==="
echo ""

echo "1. Root endpoint:"
curl -s http://localhost:8000/ | python3 -m json.tool
echo ""

echo "2. Health check:"
curl -s http://localhost:8000/health | python3 -m json.tool
echo ""

echo "3. Get first 5 carriers:"
curl -s "http://localhost:8000/carriers?limit=5" | python3 -m json.tool | head -40
echo ""

echo "4. Search for 'DAK':"
curl -s "http://localhost:8000/carriers/search/?name=DAK" | python3 -m json.tool | head -30
echo ""

echo "5. Get acceptance centers:"
curl -s "http://localhost:8000/acceptance-centers" | python3 -m json.tool | head -30
echo ""

echo "6. Get carriers for acceptance center 105830016:"
curl -s "http://localhost:8000/acceptance-centers/105830016" | python3 -m json.tool | head -30
echo ""
