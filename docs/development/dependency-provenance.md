# Dependency provenance and reproducible resolution

This record covers the dependency question reviewed for EDY SIEM 0.3.0 on
2026-08-17. It is evidence, not permission to execute an unreviewed package.

## Confirmed provenance

`httpx2==2.9.1` is an official PyPI release owned by the `pydantic`
organization and maintained by Pydantic Services Inc. PyPI links its source to
`pydantic/httpx2`; the release attestation identifies source commit
`c39c6e3e4272b9cb8d407125296f079b59d5de9f` at tag `v2.9.1`. The published
artifacts recorded by PyPI are:

| Artifact | SHA-256 |
| --- | --- |
| `httpx2-2.9.1-py3-none-any.whl` | `1820fe14a9ab1107bfeff39259987429450b070ec0ff38cc87eb0d8c97fdc71a` |
| `httpx2-2.9.1.tar.gz` | `1932a768737e3666291582833da748cc4e563c337cf96706fccc04fa6e58764a` |

Primary records: [PyPI release](https://pypi.org/project/httpx2/2.9.1/),
[PyPI release metadata](https://pypi.org/pypi/httpx2/2.9.1/json), and
[upstream source](https://github.com/pydantic/httpx2/tree/v2.9.1).

Starlette 1.3.1 officially declares `httpx2>=2.0.0` for its `full` extra and
documents `httpx2` as the dependency required for `TestClient`. This confirms
that the project name is intentional rather than a misspelling. See the
[Starlette 1.3.1 PyPI metadata](https://pypi.org/pypi/starlette/1.3.1/json).

No `httpx2` artifact was installed, imported, or executed during this review.

## Reproducible-resolution policy

The direct `==2.9.1` pin in `pyproject.toml` does **not** lock transitive
dependencies and is not, by itself, a reproducible environment. A hand-written
pin without hashes would not solve that problem.

Pip 26.2.1 provides the experimental PEP 751 `pip lock` command. Its own
documentation says that a generated lock is guaranteed only for the Python
version and platform where it was created. Therefore this repository does not
claim one unverified cross-platform lock. See the official
[`pip lock` documentation](https://pip.pypa.io/en/stable/cli/pip_lock/).

The approved follow-up procedure is:

1. Use a disposable, network-isolated review environment for each supported
   Python/platform pair.
2. Resolve the built EDY SIEM wheel with its `dev,api` extras using the pinned
   pip version and emit a platform-specific `pylock.toml`.
3. Review every direct and transitive artifact, hash, source, license and PyPI
   attestation before committing the lock.
4. Make CI install only from the reviewed lock and verify `pip check`; regenerate
   the lock only through the same documented review process.

A representative review command, intentionally **not run** in this change, is:

```bash
python -m pip lock "./dist/edy_siem-0.3.0-py3-none-any.whl[dev,api]" \
  --output pylock.python312-linux.toml
```

Lock generation may resolve and download distribution metadata or invoke a
build backend. Running it before the package and all transitive artifacts are
approved would violate the review boundary, so no lock file is fabricated here.
