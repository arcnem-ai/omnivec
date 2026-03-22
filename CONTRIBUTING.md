# Contributing

Thanks for contributing to `omnivec`.

## Before opening a PR

- Keep the API behavior and defaults stable unless the change intentionally updates v1 UX.
- Keep indexing and clustering deterministic outside CrewAI.
- Keep route handlers thin. Put reusable logic in service modules.
- Update `README.md` for user-visible changes. Update `README.ja.md` too when practical.
- Prefer the standard library and existing dependencies before adding new ones.
- If a change touches the `texvec` or `picvec` integration, update docs and test coverage together.

## Development

```sh
uv sync
uv run pytest
uv run omnivec
```

## Testing

- Prefer deterministic unit and API tests.
- Do not make the default suite depend on OpenAI, ONNX Runtime downloads, model downloads, or external services.
- Use fake runners and temp directories instead of writing into a real persistent data directory.
- Keep smoke tests separate from the default test suite.

## Pull Requests

- Keep changes focused and explain the user-facing impact.
- Add or update tests when behavior changes.
- Update docs and examples when endpoints, env vars, storage, deployment, or workflows change.
- Call out any new binary, model, runtime, or deployment assumptions.

## AI Coding Agents

If you use an AI coding agent, read [AGENTS.md](AGENTS.md) before making changes.

## License

By submitting a contribution, you agree that your work will be licensed under the MIT License.
