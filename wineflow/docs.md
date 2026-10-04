# WineFlow Documentation & Developer Guide

## 🌟 Architecture Overview

WineFlow leverages system Wine binaries while providing a powerful abstraction layer to solve typical Wine issues:
- **Prefix Isolation:** Every app runs in its own dedicated directory under `~/.wineflow/`. No more broken global prefixes when an app crashes.
- **Automated Winetricks Bridge:** Seamlessly inject missing runtimes (`vcrun2019`, `dotnet`, `dxvk`) via built-in wrappers.
- **Native Desktop Integration:** Generates standard XDG `.desktop` entries so Windows applications feel like native Linux apps.

---

## 💻 CLI Usage Examples

### 1. Initialize a custom isolated environment
```bash
python3 wineflow/main.py init --prefix my-game-env
```

### 2. Install a missing runtime dependency (requires winetricks)
```bash
python3 wineflow/main.py dep --prefix my-game-env --name vcrun2019
```

### 3. Run a Windows executable (.exe)
```bash
python3 wineflow/main.py run --prefix my-game-env --exe /path/to/installer.exe
```

### 4. Create a desktop shortcut for easy launching
```bash
python3 wineflow/main.py shortcut --prefix my-game-env --name "My Windows App" --exe /path/to/app.exe
```
