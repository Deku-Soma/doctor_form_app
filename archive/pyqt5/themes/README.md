# `themes/` — Visual Assets & Stylesheet

Contains the application's visual identity: the QSS theme, company logo, and doctor/clinic stamps used in PDF generation.

## Files

| File | Purpose |
|------|---------|
| `modern.qss` | Global dark theme stylesheet (Qt Stylesheet format). Applied in `MainApp.load_stylesheet()`. |
| `Logo.png` | HealthCorp360 company logo. Used in `HeaderSection` (home page background) and embedded in PDFs as a base64 data URI. |
| `Dr.R.Malebye stamp.png` | Doctor's stamp image embedded in PDFs as `stamp1_data_uri`. |
| `helthcorp stamp.png` | Clinic stamp image embedded in PDFs as `stamp2_data_uri`. |

## Theme Color Palette

The `modern.qss` defines a consistent dark theme:

| Token | Hex | Usage |
|-------|-----|-------|
| Background | `#2b2b2b` | Main window, containers |
| Surface | `#3d3d3d` | Input fields, cards, tables |
| Border | `#555555` | Input borders, grid lines |
| Accent (Teal) | `#1abc9c` | Buttons, focus rings, headers |
| Accent Hover | `#16a085` | Button hover states |
| Text Primary | `#ffffff` | All text |
| Text Secondary | `#aaaaaa` | Placeholders, disabled text |

## How Assets Are Loaded

- **QSS:** Loaded via `get_resource_path("themes/modern.qss")` — works both in dev and PyInstaller builds.
- **Logo/Stamps in PDFs:** Loaded in `template_generator.py`, base64-encoded, and injected as `data:image/png;base64,...` data URIs into Jinja2 templates. This ensures PDFs render correctly without external file dependencies.
