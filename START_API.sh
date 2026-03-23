#!/bin/bash
# Stoppe alte API-Instanzen
echo "Stoppe alte API-Instanzen..."
pkill -f "uvicorn app.main:app" 2>/dev/null || true

# Force kill Port 9000
lsof -ti :9000 | xargs -r kill -9 2>/dev/null || true
sleep 2

# Starte neue API
echo "Starte Krankenkassen API..."
echo ""
echo "API läuft auf:"
echo "  http://localhost:9000"
echo ""
echo "Teste mit:"
echo '  curl "http://localhost:9000/find-billing-center?krankenkasse=Techniker"'
echo ""
echo "Oder öffne im Browser:"
echo "  http://localhost:9000/docs"
echo ""
echo "Drücke Ctrl+C zum Beenden"
echo ""

cd /home/alex/kk_info
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload
