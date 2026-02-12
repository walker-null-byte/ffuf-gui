# FFUF-GUI

A modern, open-source web GUI wrapper for the [ffuf](https://github.com/ffuf/ffuf) command-line tool.

![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Features

-   **Modern Dark Interface**: Clean, professional design.
-   **Full FFUF Support**: Configure URL, Methods, Headers, Matchers, Filters, and more.
-   **Live Interaction**: Real-time output streaming and command preview.
-   **Safe Execution**: Input validation and secure subprocess handling.
-   **Responsive**: Works on desktop and mobile browsers.

## Installation

### Prerequisites

-   [ffuf](https://github.com/ffuf/ffuf) must be installed and in your system PATH.
-   Python 3.7+

### From Source

1.  Clone the repository:
    ```bash
    git clone https://github.com/example/ffuf-gui.git
    cd ffuf-gui
    ```

2.  Install dependencies:
    ```bash
    pip install .
    ```

3.  Run the application:
    ```bash
    ffuf-gui
    ```
    Open your browser to `http://127.0.0.1:5000`.

### Arch Linux (AUR)

```bash
yay -S ffuf-gui
```

## Usage

1.  **Target**: Enter the target URL. Use the `FUZZ` keyword where you want payload injection (e.g., `http://example.com/FUZZ`).
2.  **Wordlists**: Add one or more wordlists. Default keyword is `FUZZ`.
3.  **Config**: Set matchers (e.g., `200,301`) and filters to refine results.
4.  **Run**: Click the "Run" button. Results will stream in real-time.

## Development

1.  Install dev dependencies:
    ```bash
    pip install -e .
    ```

2.  Run Flask in debug mode:
    ```bash
    python -m ffuf_gui.app
    ```

## License

MIT
