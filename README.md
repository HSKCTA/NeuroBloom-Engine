# Autism Spectrum Disabilities - Neuro-Hybrid System

This project is a neuro-hybrid system designed to assist in the diagnosis and monitoring of Autism Spectrum Disorders (ASD), ADHD, and Dyscalculia. It combines simulated EEG data generation with computer vision analysis to provide a comprehensive assessment tool.

## Features

-   **Neuro-Hybrid Generator (C++)**:
    -   Simulates 8-band EEG data (Delta, Theta, Alpha, Beta, Gamma).
    -   Performs real-time face and eye tracking using OpenCV.
    -   Calculates attention metrics: Focus Ratio, Hyperactivity Index, and Blink Rate.
    -   Encrypts data using AES-256 and transmits it via ZeroMQ.

-   **Bridge Server (Python)**:
    -   Receives encrypted data from the C++ generator.
    -   Decrypts and processes the data.
    -   Calculates cognitive metrics: Theta/Beta Ratio (ADHD), Cognitive Load, and Stress Index.
    -   Provides a WebSocket API for real-time data streaming.
    -   Includes a Dysgraphia analysis module using handwriting heuristics.

-   **Frontend Dashboard (React)**:
    -   Real-time visualization of EEG bands and attention metrics.
    -   Live video feed overlay with tracking indicators.
    -   Dysgraphia assessment interface.
    -   Responsive and modern UI built with Vite and TailwindCSS.

## Architecture

1.  **C++ Backend**: Generates data and handles computer vision. Publishes to ZeroMQ.
2.  **Python Middleware**: Subscribes to ZeroMQ, processes logic, and hosts a WebSocket server (FastAPI).
3.  **React Frontend**: Connects to the WebSocket server to display data and interact with the system.

## Prerequisites

-   **C++**: `g++`, `pkg-config`, `libzmq3-dev`, `libopencv-dev`, `libssl-dev`
-   **Python**: Python 3.8+
-   **Node.js**: Node.js 18+ and `npm`

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/HSKCTA/Autism-Spectrum-Disabilities.git
    cd Autism-Spectrum-Disabilities
    ```

2.  **Install Python Dependencies:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Install Frontend Dependencies:**
    ```bash
    cd frontend
    npm install
    cd ..
    ```

4.  **Compile C++ Generator:**
    ```bash
    g++ neuro_hybrid.cpp -o neuro_hybrid -lzmq `pkg-config --cflags --libs opencv4` -lssl -lcrypto
    ```

## Usage

1.  **Run the System:**
    Use the provided script to start all components:
    ```bash
    chmod +x run_all.sh
    ./run_all.sh
    ```

2.  **Access the Dashboard:**
    Open your browser and navigate to `http://localhost:5173`.

## License
[MIT](LICENSE)
