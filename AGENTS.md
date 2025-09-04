# Repository Guidelines

## Project Structure & Module Organization
- Root Gradle (Kotlin DSL): `build.gradle.kts`, `settings.gradle.kts` (AGP 8.2.2, Kotlin 1.9.22).
- App module: `app/`
  - Source: `app/src/main/java/com/example/kidanimals/`
  - Resources: `app/src/main/res/`
  - Manifest: `app/src/main/AndroidManifest.xml`
  - Assets (images): `app/src/main/assets/animals/`
  - Gradle config: `app/build.gradle.kts`
- Tools: `tools/` (e.g., `scrape_wikimedia_animals.py`).

## Build, Test, and Development Commands
- `./gradlew assembleDebug`: Build a debug APK.
- `./gradlew installDebug`: Build and install on a connected device/emulator.
- `./gradlew clean`: Remove build outputs.
- `./gradlew lint`: Run Android/Kotlin lint checks.
- Local run: open in Android Studio (JDK 17), target API 34, min API 24.

## Coding Style & Naming Conventions
- Kotlin: 4‑space indent, trailing commas discouraged, prefer `val` over `var`.
- Classes/objects: `PascalCase` (e.g., `MainActivity`). Functions/vars: `lowerCamelCase`.
- Resources: snake_case (e.g., `activity_main.xml`, `rounded_bg.xml`, `@id/full_image`).
- Packages: `com.example.kidanimals.*`. Keep UI code in `MainActivity.kt`; add new UI in dedicated files.
- Formatting: use Android Studio default Kotlin style; verify with `./gradlew lint` before PRs.

## Testing Guidelines
- Unit tests: place in `app/src/test/` (JUnit4). Example file: `MainActivityTest.kt`.
- Instrumentation tests: `app/src/androidTest/` (Espresso). Run with `./gradlew connectedAndroidTest`.
- Name tests descriptively (e.g., `loadsImages_fromAssets()`); aim for fast, deterministic tests.

## Commit & Pull Request Guidelines
- Commits: imperative, present tense, concise subject (<72 chars) with context in body.
  - Example: `Add ViewPager2 gallery and thumbnail strip`.
- PRs: include summary, screenshots for UI changes, steps to test, and any linked issues.
- Keep diffs focused; update README or comments when behavior changes.

## Security & Configuration Tips
- Assets licensing: images may be Creative Commons; keep attributions from `animals_metadata.csv`.
- Kid‑lock: app uses screen pinning; document device setup in PRs if behavior changes.
- Tools: `tools/scrape_wikimedia_animals.py` needs `requests` and network; do not vendor large binaries.

## Architecture Overview
- Single‑activity app with RecyclerView thumbnails and ViewPager2 fullscreen pager.
- Images streamed from `assets/animals/` and downsampled for memory safety.

