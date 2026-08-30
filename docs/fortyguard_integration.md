# FortyGuard Integration Architecture

## Overview
AeroMind ClimateGuard integrates directly with the FortyGuard Temperature Intelligence API to feed live, hyper-local temperature data into the system's deterministic Risk Engine.

## Architecture
The system uses the `TemperatureProvider` abstraction located in `services/temperature/provider.py` to ensure that data ingestion logic remains decoupled from specific vendors.
- **FortyGuardProvider**: The primary implementation that communicates with the FortyGuard API using `httpx`.
- **LocalDemoProvider**: A robust fallback mechanism that generates deterministic telemetry data when the API is unreachable, misconfigured, or when the system is running in offline mode.

## Data Flow
1. `FortyGuard Client` fetches raw JSON from the FortyGuard API.
2. `Response Validation` normalizes the JSON into a `TemperatureObservation` Pydantic model.
3. The `Ingestion Pipeline` receives the observation and extracts metrics (e.g., `ambient_temp`).
4. The `Risk Engine` assesses the updated metrics against baseline tolerances and historical rate-of-change data.
5. The `WebSocket Hub` broadcasts the unified `temperature.updated` and `risk.updated` events.
6. The `React Dashboard` consumes the event to update the UI, showing live telemetry and explicitly flagging the data source (LIVE (FG) or DEMO DATA).

## Security
- **Authentication**: API keys are securely loaded from environment variables (`FORTYGUARD_API_KEY`) using `pydantic-settings`.
- **Exposure**: Keys are never hardcoded, logged to the console, or exposed in API responses (including `/health` or `/test-connection`).

## Handling Failures
The integration utilizes the tenacity library for robust error handling:
- **Rate Limiting**: `HTTP 429` responses trigger exponential backoff.
- **Timeouts**: Slow responses retry automatically up to 3 times before falling back to the `LocalDemoProvider`.
- **Authentication Errors**: Invalid keys immediately mark the provider status as `AUTHENTICATION_ERROR` and halt further automated polling to prevent account lockouts.
