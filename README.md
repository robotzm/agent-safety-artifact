# Agent Safety Benchmark

**Anonymous authors**

A project scaffold for an agent safety benchmark. Research content, implementation,
datasets, and experimental results will be added by the authors. This repository
does not yet contain a benchmark release or evaluated results.

## Project website

Open the [anonymous project website](https://anonymous.4open.science/w/agent-safety-benchmark-880C/) for the overview and available materials.
Browse the [anonymous repository](https://anonymous.4open.science/r/agent-safety-benchmark-880C/) for all files.
The website uses local assets and relative links so it can be served from a GitHub
Pages project path or another static hosting path.

## Repository layout

| Location | Intended contents |
| --- | --- |
| [docs/](docs/index.html) | Static project website and downloadable materials |
| [src/](src/README.md) | Benchmark implementation and evaluation code |
| [data/](data/README.md) | Dataset documentation and release instructions |
| [configs/](configs/README.md) | Reproducible evaluation configurations |
| [results/](results/README.md) | Verified experimental results and reporting artifacts |
| [scripts/check_links.py](scripts/check_links.py) | Local website link and asset validation |

## Preview the website

From the repository root, run:

```sh
python3 -m http.server 8000 --directory docs
```

Then open `http://localhost:8000` in your browser. No package installation or build
step is required.

## Check website links

From the repository root, run:

```sh
python3 scripts/check_links.py
```

The checker validates local HTML links, fragment targets, and CSS asset URLs. It
also rejects empty links and obvious placeholder external URLs. External HTTP
availability must be checked separately after publication.

## Adding research content

Replace the clearly marked website placeholders with the manuscript's actual
abstract, benchmark design, verified results, and release materials. Keep links
pointing to existing files or sections. Add a paper download only once the
anonymized PDF is available.

## Release status and license

This is a structure-only release. A license will be added with the substantive
release; no open-source license is selected by this scaffold.
