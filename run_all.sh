#!/bin/bash

# Kill any existing processes
pkill -f neuro_hybrid
pkill -f bridge_server.py

# Start C++ Generator
echo "Starting NeuroBloom C++ Generator..."
./neuro_hybrid > neuro.log 2>&1 &
PID_CPP=$!
echo "C++ Generator started with PID $PID_CPP"

# Start Python Bridge
echo "Starting Python Bridge..."
source venv/bin/activate
uvicorn bridge_server:app --host 0.0.0.0 --port 8000 --ws websockets > bridge.log 2>&1 &
PID_PY=$!
echo "Python Bridge started with PID $PID_PY"

# Start Frontend
echo "Starting Frontend..."
cd frontend
npm run dev > frontend.log 2>&1 &
PID_FRONT=$!
echo "Frontend started with PID $PID_FRONT"

echo "All components started."
echo "Dashboard should be available at http://localhost:5173"
echo "Press Ctrl+C to stop all components."

trap "kill $PID_CPP $PID_PY $PID_FRONT; exit" INT
wait
