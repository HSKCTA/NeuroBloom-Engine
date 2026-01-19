#!/bin/bash

# Kill any existing processes
pkill -f neuro_hybrid
pkill -f server.py
pkill -f "npm run dev"

# Build C++ Generator
echo "Building NeuroBloom C++ Generator..."
mkdir -p core/build
cd core/build
cmake ..
make
cd ../..

# Start C++ Generator
echo "Starting NeuroBloom C++ Generator..."
./core/build/neuro_hybrid > neuro.log 2>&1 &
PID_CPP=$!
echo "C++ Generator started with PID $PID_CPP"

# Start Python Bridge
echo "Starting Python Bridge..."
cd bridge
# Check if venv exists, if not create it (optional, but good practice)
if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

uvicorn server:app --host 0.0.0.0 --port 8000 --ws websockets > ../bridge.log 2>&1 &
PID_PY=$!
echo "Python Bridge started with PID $PID_PY"
cd ..

# Start Frontend
echo "Starting Frontend..."
cd web
npm install # Ensure dependencies are installed
npm run dev > ../frontend.log 2>&1 &
PID_FRONT=$!
echo "Frontend started with PID $PID_FRONT"
cd ..

echo "All components started."
echo "Dashboard should be available at http://localhost:5173"
echo "Press Ctrl+C to stop all components."

trap "kill $PID_CPP $PID_PY $PID_FRONT; exit" INT
wait
