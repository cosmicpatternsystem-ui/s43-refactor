# ASO-X Global API Contract v1.0
## Endpoints
- GET  /v1/health          -> Live system heartbeat status
- GET  /v1/audit/latest    -> Latest verified integrity entry
- POST /v1/safety/verify   -> Verify external transaction against SafetyGate
- GET  /v1/intel/status    -> Optimized intelligence metrics

## Security
- Auth: Bearer JWT
- Encryption: TLS 1.3
