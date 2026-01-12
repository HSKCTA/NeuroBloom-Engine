# NeuroBloom API Specification

This document outlines the API connection details and data structures for the NeuroBloom frontend.

## Connection Details

*   **Protocol**: WebSocket
*   **URL**: `ws://localhost:8000/ws` (Local) or `ws://10.100.174.136:8000/ws` (LAN)
*   **Behavior**: The server pushes JSON updates approximately every 30-50ms (30 FPS).
*   **Auto-Shutdown**: Disconnecting the WebSocket (closing the tab) will automatically terminate the backend vision sensors.

## How to Connect

### Scenario A: Same WiFi / Network
If you are on the same network as the backend, use the host's IP address:
```typescript
const ws = new WebSocket('ws://10.100.174.136:8000/ws');
```
*Note: Ensure the host machine (10.100.174.136) allows incoming connections on port 8000.*

### Scenario B: Remote (Different Networks)
If you are working remotely, the host must expose the server using a tool like **ngrok**.
1.  Host runs: `ngrok http 8000`
2.  Host shares the generated URL (e.g., `https://xyz.ngrok-free.app`)
3.  Frontend connects via WSS:
    ```typescript
    const ws = new WebSocket('wss://xyz.ngrok-free.app/ws');
    ```

## Data Structure

The backend sends a JSON object containing sensor fusion data (EEG + Vision).

### TypeScript Interfaces

Copy these interfaces into your TypeScript project to type the incoming data.

```typescript
export interface NeuroData {
  /** Unix timestamp in milliseconds */
  timestamp: number;
  
  /** Simulated EEG Power Bands */
  eeg: {
    /** Theta Band Power (Associated with drowsiness/distraction) */
    theta: number;
    /** Beta Band Power (Associated with active focus) */
    beta: number;
  };
  
  /** Computer Vision Metrics */
  vision: {
    /** Head Yaw (Horizontal rotation) in pixels from center */
    yaw: number;
    /** Gaze Score (0.0 - 1.0, lower is more direct eye contact) */
    gaze: number;
    /** Attention Score (1.0 = Focused, 0.0 = Distracted) */
    attention: number;
  };
  
  /** 
   * Diagnostic State (Injected by Python Bridge) 
   * Note: This field is added by the Python server, not the C++ core.
   */
  diagnosis: "DISTRACTED" | "FOCUSED" | "WAITING...";
}
```

### Example JSON Payload

```json
{
  "timestamp": 1704862555123,
  "eeg": {
    "theta": 28450.50,
    "beta": 6120.25
  },
  "vision": {
    "yaw": 45.2,
    "gaze": 0.8,
    "attention": 0.0
  },
  "diagnosis": "DISTRACTED"
}
```

## Implementation Notes

1.  **State Management**: The data comes in high frequency. Avoid re-rendering the entire UI on every packet if possible, or use a throttle.
2.  **Charts**: For the EEG chart, you can plot `eeg.beta` vs `eeg.theta`.
3.  **Visuals**: 
    *   `vision.yaw` can be used to animate a head avatar or indicator.
    *   `diagnosis` should drive the main status color (Red for DISTRACTED, Green for FOCUSED).

## Dysgraphia Analysis API

The frontend can send an image of handwriting to the backend for analysis.

### Request (Frontend -> Backend)

Send a text message over the WebSocket with the following format:

```text
SCAN_HANDWRITING:<base64_encoded_image_string>
```

*   **Prefix**: `SCAN_HANDWRITING:`
*   **Payload**: The base64 string of the image (without the `data:image/png;base64,` header if possible, though the backend might handle it, best to strip it).

### Response (Backend -> Frontend)

The backend will respond with a JSON object:

```json
{
  "type": "DYSGRAPHIA_RESULT",
  "score": 0.15,
  "diagnosis": "NORMAL"
}
```

*   **type**: Always `DYSGRAPHIA_RESULT`.
*   **score**: A number between 0.0 and 1.0+.
    *   `< 0.25`: Normal
    *   `0.25 - 0.40`: Mild Irregularity
    *   `> 0.40`: High Risk
*   **diagnosis**: One of `NORMAL`, `MILD IRREGULARITY`, `HIGH RISK`, or `ERROR`.

### TypeScript Interface

```typescript
export interface DysgraphiaResult {
  type: "DYSGRAPHIA_RESULT";
  score: number;
  diagnosis: "NORMAL" | "MILD IRREGULARITY" | "HIGH RISK" | "ERROR";
}
```
