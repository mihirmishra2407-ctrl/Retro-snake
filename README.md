# Retro Snake — Android GitHub Build Package

This repository contains the actual current Retro Snake Python/Pygame source plus the Android packaging files required for a GitHub Actions Buildozer build.

## Included

- `main.py` — current Retro Snake game source
- `assets/retro_snake_icon.png` — Retro Snake app icon
- `buildozer.spec` — Android package configuration
- `recipes/pygame-ce/` — local pygame-ce Android recipe
- `.github/workflows/build-apk.yml` — GitHub Actions APK build workflow

## Build

1. Create an empty GitHub repository named `Retro-Snake`.
2. Upload the contents of this folder, including `.github/workflows/build-apk.yml`.
3. Commit to the `main` branch.
4. Open **Actions** in GitHub.
5. Open **Build Retro Snake APK**.
6. Wait for the workflow to finish successfully.
7. Open the completed run and download the **Retro-Snake-APK** artifact.
8. Extract the artifact ZIP to obtain the `.apk` file.

The workflow can also be started manually from **Actions → Build Retro Snake APK → Run workflow**.

## Important

This package is a real build repository, not a placeholder ZIP. The game source is copied from the latest Retro Snake source available when this package was generated.

The current game source is still the desktop-oriented version of Retro Snake. Its terminal QCL uses Python `input()` and its directional gameplay uses keyboard events. Those Android interaction pieces need to be adapted before claiming the final mobile UX with the planned BUTTONS/SWAP touch controls and graphical CL/QCL controls.
