# Frontend Developer Guide

This guide explains how to set up and run the NeuroBloom frontend.

## Prerequisites

*   **Node.js**: Version 18 or higher.
*   **npm**: Included with Node.js.

## Setup

1.  Navigate to the `frontend` directory:
    ```bash
    cd frontend
    ```

2.  Install dependencies:
    ```bash
    npm install
    ```

## Running the Frontend

To start the development server:

```bash
npm run dev
```

The application will be available at [http://localhost:5173](http://localhost:5173).

## Connecting to Backend

The frontend expects a WebSocket connection to the backend.

*   **Local Backend**: If the backend is running locally on your machine (port 8000), the frontend should connect automatically to `ws://localhost:8000/ws`.
*   **Remote Backend**: If the backend is on another machine (e.g., `10.100.174.136`), update the WebSocket URL in your code (likely in `Dashboard.jsx` or a config file) to match the backend IP.

## Project Structure

*   `src/components/Dashboard.jsx`: Main dashboard component.
*   `src/App.jsx`: Root component.
*   `vite.config.js`: Vite configuration.

## Common Issues

*   **Connection Failed**: Ensure the backend is running and the IP/Port is correct. Check the browser console for WebSocket errors.
*   **Module Errors**: If you see import errors, ensure you are running via `npm run dev` and not trying to open `index.html` directly.
