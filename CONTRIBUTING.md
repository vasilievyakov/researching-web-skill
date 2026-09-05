# Contributing to Researching Web

Thanks for your interest in contributing! This skill is designed to be simple and focused.

## How to Contribute

### Reporting Issues

- Check existing issues first
- Include your Claude Code version
- Describe expected vs actual behavior
- Include example queries that cause the issue

### Suggesting Features

Open an issue with:
- Clear description of the feature
- Why it would be useful
- Example use case

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run `python3 -m unittest discover -s tests -v`; for workflow changes, also test with Claude Code using an explicitly selected live API budget when available. Clearly distinguish mocked checks from live acceptance.
5. Commit (`git commit -m 'Add amazing feature'`)
6. Push (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development Guidelines

### SKILL.md Changes

- Keep under 150 lines
- Trust Claude's intelligence — don't over-explain
- Add actionable instructions, not theory
- Test changes with real queries

### HTML Templates

- Support dark/light theme via CSS variables
- Keep templates responsive
- Include source attribution

### Code Style

- Clear, concise comments
- Descriptive variable names
- No unnecessary complexity

## Areas for Improvement

- [ ] More output formats (PDF, Markdown)
- [ ] Additional direct API providers with shared request accounting
- [ ] Multilingual support
- [ ] Custom confidence thresholds
- [x] Persistent caching and request budgets for repeated queries

## Questions?

Open an issue or start a discussion. Happy researching!
