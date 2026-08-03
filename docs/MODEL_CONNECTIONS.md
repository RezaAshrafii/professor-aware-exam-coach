# Model connections

## Scope

The desktop app supports exactly two reusable connection slots. The UI is provider-neutral: it stores a label, protocol, base URL, selected model and active state.

## Protocols

### Gemini

- Model discovery: `GET {base_url}/models`
- Generation: `POST {base_url}/models/{model}:generateContent`
- Only models advertising `generateContent` are shown.

### OpenAI-compatible

- Model discovery: `GET {base_url}/models`
- Generation first tries `POST {base_url}/chat/completions`.
- If the endpoint/model rejects that API shape with 400/404/405/422, runtime tries `POST {base_url}/responses` once.

## Secrets

Metadata is stored in SQLite. API keys are stored separately in `data/model_secrets.json`, which is excluded from Git and never returned by product endpoints.

This is suitable for a local single-user application. It is not intended as a multi-user secret vault.

## No hardcoded model catalog

Model names are never maintained in source code. The catalog is fetched from the configured endpoint, cached locally, searched client-side and rendered eight results at a time.
