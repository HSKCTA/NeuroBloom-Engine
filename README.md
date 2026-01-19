# NeuroBloom: Neuro-Hybrid Cognitive Engine

**A high-performance, distributed biometric monitoring system architected in C++ and Python.**

![C++](https://img.shields.io/badge/Core-C++17-blue.svg)
![ZeroMQ](https://img.shields.io/badge/IPC-ZeroMQ-red.svg)
![OpenSSL](https://img.shields.io/badge/Security-AES256-green.svg)
![Build](https://img.shields.io/badge/Build-CMake-orange.svg)

## Overview
NeuroBloom is a real-time system designed to monitor cognitive states (Focus, Stress, Cognitive Load) by fusing simulated EEG data with computer vision metrics. It demonstrates a **Low-Latency Distributed Architecture** using:

* **C++ Core (Producer):** Physics-based signal generation (1/f noise) and OpenCV Gaze Tracking.
* **ZeroMQ (Transport):** Sub-millisecond IPC replacing standard HTTP REST.
* **OpenSSL (Security):** Native AES-256-CBC encryption of biometric payloads.
* **Python (Consumer):** Sensor fusion and WebSocket broadcasting.

## Architecture

%%{init: {'theme': 'default', 'themeVariables': { 'fontSize': '16px', 'fontFamily': 'arial'}}}%%
flowchart TD
    %% Subgraph for the C++ Core
    subgraph CPP_Engine ["Layer 1: C++ Core Engine"]
        direction TB
        Input(("Webcam Input")) --> CV["Computer Vision<br/>Gaze & Face Track"]
        PinkNoise["Pink Noise Gen<br/>1/f Physics"] --> EEG["Simulated<br/>EEG Bands"]
        
        CV & EEG --> Serial["JSON Serializer"]
        Serial --> Encrypt["AES-256 Encryption<br/>(OpenSSL)"]
        Encrypt --> ZMQ_PUB["ZeroMQ<br/>PUB Socket"]
    end

    ZMQ_PUB -- "Encrypted Stream<br/>(Latency < 5ms)" --> ZMQ_SUB

    %% Subgraph for Python Middleware
    subgraph Python_Bridge ["Layer 2: Python Bridge"]
        direction TB
        ZMQ_SUB["ZeroMQ<br/>SUB Socket"] --> Decrypt["Decryption<br/>(Cryptography Lib)"]
        Decrypt --> Fusion["Sensor Fusion"]
        Fusion --> WSS(("WebSocket<br/>Server"))
    end

    WSS -- "JSON Events (60Hz)" --> React

    %% Subgraph for Frontend
    subgraph Frontend ["Layer 3: React Dashboard"]
        React["React Client"] --> State["State Manager"]
        State --> Viz["Chart.js Visualization"]
    end
    
    %% Clean, Solid Box Styles (High Contrast)
    classDef cpp fill:#fff0f0,stroke:#d32f2f,stroke-width:2px,color:black;
    classDef py fill:#fffff0,stroke:#fbc02d,stroke-width:2px,color:black;
    classDef ui fill:#f0f8ff,stroke:#0288d1,stroke-width:2px,color:black;
    
    class CV,PinkNoise,EEG,Serial,Encrypt,ZMQ_PUB cpp;
    class ZMQ_SUB,Decrypt,Fusion,WSS py;
    class React,State,Viz ui;
