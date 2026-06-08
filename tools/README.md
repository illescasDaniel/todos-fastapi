# Optional PlantUML JAR

If the `plantuml` CLI is not installed, download a release JAR here:

```bash
curl -fsSL -o tools/plantuml.jar \
  "https://github.com/plantuml/plantuml/releases/download/v1.2024.8/plantuml-1.2024.8.jar"
```

Then run `./scripts/render_diagrams.sh` from the project root.

The JAR is gitignored; SVG outputs under `docs/images/` are committed.
