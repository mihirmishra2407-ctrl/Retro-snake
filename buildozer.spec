[app]

# Application identity
title = Retro Snake
package.name = retrosnake
package.domain = com.mihir.retrosnake
version = 1.0.0

# Python/Pygame entrypoint
source.dir = .
source.main = main.py
source.include_exts = py,png,jpg,jpeg,wav,ogg,ttf,txt
source.exclude_exts = spec
source.exclude_dirs = .git,.github,bin,.buildozer,__pycache__

# Pygame CE is built by the local python-for-android recipe included in this repo.
requirements = python3,pygame-ce
p4a.local_recipes = ./recipes
p4a.branch = develop

# Android package settings
orientation = landscape
fullscreen = 1
android.api = 35
android.minapi = 23
android.arch = arm64-v8a
android.accept_sdk_license = True
android.debug_artifact = apk

# App icon and loading image
icon.filename = %(source.dir)s/assets/retro_snake_icon.png
presplash.filename = %(source.dir)s/assets/retro_snake_icon.png

# Keep the display awake while playing.
android.wakelock = True

# Build metadata
android.copy_libs = 1

[buildozer]
log_level = 2
warn_on_root = 1
