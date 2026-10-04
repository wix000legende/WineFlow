# 🍷 WineFlow

**WineFlow** is a modern, lightweight, and stable wrapper and prefix manager for Wine on Linux. It solves the biggest pain point of running Windows applications on Linux: isolated prefixes, automated dependency management (`.NET`, `VC++`, `DirectX`), and seamless desktop integration without headaches.

---

## 🚀 Features

- **Isolated Prefixes:** Keep every Windows application in its own sandbox environment to prevent crashes from affecting your entire system.
- **Smart Dependency Installer:** Automatically fetch and install common redistributables (Visual C++, .NET, DirectX) required by apps and games.
- **CLI & Automation:** Simple command-line interface to create prefixes, run `.exe` installers, and manage configurations effortlessly.
- **Desktop Integration:** Automatically generate clean Linux `.desktop` shortcuts for your Windows apps.

---

## 📦 Project Structure

```text
wineflow/
├── core/          # Core engine for Wine prefix & process management
├── cli/           # Command-line interface
├── utils/         # Helper functions & dependency handlers
└── main.py        # Entry point
```

---

## 🛠️ Getting Started

1. Ensure `wine` is installed on your system.
2. Run the tool:
   ```bash
   python3 main.py --help
   ```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
