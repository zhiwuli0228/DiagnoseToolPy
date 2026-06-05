## ADDED Requirements

### Requirement: Backend responses larger than 1000 bytes MUST be gzipped

The FastAPI application MUST compress response bodies larger than
1000 bytes using `Content-Encoding: gzip` for any client that sends
`Accept-Encoding: gzip`.

#### Scenario: Large response is compressed

- **WHEN** a response body exceeds 1000 bytes and the client sends
  `Accept-Encoding: gzip`
- **THEN** the response MUST include `Content-Encoding: gzip` and the
  decompressed body MUST match the uncompressed payload.

#### Scenario: Small response is not compressed

- **WHEN** a response body is 1000 bytes or smaller
- **THEN** the response MUST NOT include `Content-Encoding: gzip`.

#### Scenario: Streaming responses remain streamable

- **WHEN** a route returns a `StreamingResponse`
- **THEN** the body MUST still be delivered as a stream (chunked
  transfer-encoding preserved).
