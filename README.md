# MiniHMIS (demo)

> **This is a demo.** MiniHMIS is a deliberately tiny, fake "health management
> information system". It exists only to demonstrate a security pre-disclosure
> workflow. It holds no real data, contains no code from any real HMIS, and
> must never be used for anything real.

## What it does

- A login page (`/login`)
- One protected page (`/dashboard`)
- A version endpoint (`/api/version`)

It is a single Python file with no dependencies beyond the standard library.

## Run it

With Docker:

```bash
docker build -t minihmis:dev .
docker run --rm -p 8080:8080 minihmis:dev
```

Or directly:

```bash
python3 app/minihmis.py
```

Then open <http://localhost:8080> and sign in with `admin` / `demo-password`.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `PORT` | `8080` | Port to listen on |
| `MINIHMIS_ADMIN_USER` | `admin` | Demo account username |
| `MINIHMIS_ADMIN_PASSWORD` | `demo-password` | Demo account password |
| `MINIHMIS_SITE_NAME` | `MiniHMIS Demo Instance` | Name shown in the page header |

## Tests

```bash
python3 -m unittest discover -s tests
```

## Releases

| Version | Status |
| --- | --- |
| 1.0 | Unsupported |

## Security

See [SECURITY.md](SECURITY.md). This is a demo project; any advisory published
here is part of a demonstration and does not describe a real product.
