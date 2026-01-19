# Build and Run Instructions

This document provides step-by-step instructions to build and run the Neuro-Hybrid System, including the C++ Core, Python Bridge, and React Frontend.

## Prerequisites

Ensure you have the following installed on your system:

-   **C++ Build Tools**:
    -   `cmake`
    -   `g++`
    -   `make`
    -   `pkg-config`
    -   Libraries: `libzmq3-dev`, `libopencv-dev`, `libssl-dev`
-   **Python**: Python 3.8+ and `venv` module.
-   **Node.js**: Node.js v18+ and `npm`.

## Build Instructions

### 1. Core (C++ Generator)

The C++ core handles data generation and computer vision.

```bash
mkdir -p core/build
cd core/build
cmake ..
make
cd ../..
```

### 2. Bridge (Python Middleware)

The Python bridge acts as middleware between the C++ core and the frontend.

```bash
cd bridge
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..
```

### 3. Web (Frontend Dashboard)

The frontend is a React application built with Vite.

```bash
cd web
npm install
cd ..
```

## Run Instructions

You can run all components simultaneously using the provided script, or run them individually.

### Option A: Run All (Recommended)

```bash
chmod +x run_all.sh
./run_all.sh
```

### Option B: Run Individually

**1. Start C++ Core**
```bash
./core/build/neuro_hybrid
```

**2. Start Python Bridge**
```bash
cd bridge
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8000 --ws websockets
```

**3. Start Frontend**
```bash
cd web
npm run dev
```

## Accessing the Dashboard

Once running, the dashboard is available at: [http://localhost:5173](http://localhost:5173)
