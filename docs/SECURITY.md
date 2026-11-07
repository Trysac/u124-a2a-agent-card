# Security

## Threat Model & Constraints

1. **Denial of Service (DoS) via File & Input Size**:
   - Maximum input file size for CLI ingestion is bounded to 1 MB (`MAX_INPUT_BYTES = 1_048_576`).
   - URLs are bounded in length (max 4096 characters).
   - Error messages are truncated to 200 characters to prevent log injection or buffer bloating.
2. **Insecure Transports**:
   - In compliance with A2A specification v1.0.0, non-loopback URLs must use `https`. Plain `http` is strictly restricted to `localhost`, `127.0.0.1`, and `::1`.
3. **Logging & Information Disclosure**:
   - The library attaches a `NullHandler` to `logging.getLogger(__name__)` and never emits card payloads or secrets into logs.
