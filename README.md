# Wedding Agent

AI-powered Singapore wedding agents.

## Setup

```bash
uv sync --all-extras
cp .env.example .env
```

## Development

```bash
# Format and lint
make format
make check

# Run tests
uv run pytest
```

## Configuration

Set in `.env`:
- `GOOGLE_API_KEY` - Your Google API key (required)
- `GEMINI_MODEL` - Model to use (default: `gemini-2.5-flash`)
- `LANGFUSE_ENABLED` - Enable observability (default: `false`)

## License

WTFPL - See [LICENSE](LICENSE) for details.
