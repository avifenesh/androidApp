Kid Animals — Android App

Overview
- Simple fullscreen animal gallery for kids with a vertical thumbnail strip.
- Kid-lock safety using Android screen pinning / lock task mode.
- Images load from `app/src/main/assets/animals/`.
- Includes a script to fetch Creative Commons animal images from Wikimedia Commons.

Project Layout
- `app/src/main/java/com/example/kidanimals/MainActivity.kt`: Main UI, gallery, kid-lock overlay.
- `app/src/main/res/layout/*`: Layouts for main screen, thumbnails, pager, and exit overlay.
- `app/src/main/assets/animals/`: Drop animal images here (JPG/PNG).
- `tools/scrape_wikimedia_animals.py`: Image scraper (requires network + requests).

Kid-Lock Safety
- The app attempts `startLockTask()` on resume to enter lock task / screen pinning.
- To exit inside the app: long‑press the lock icon, then swipe the handle up.
- The app calls `stopLockTask()` when permitted; otherwise it shows how to unpin via system gesture.

Recommended Setup (Screen Pinning)
1) On the kid device, enable Settings → Security → App pinning (or Screen pinning).
2) Set a device PIN/Pattern so unpinning requires adult authentication.
3) Launch the app. It will be pinned; the kid can’t leave accidentally.
4) Adult exit: long‑press the lock icon → swipe up → follow system prompt to unpin if shown.

Optional Kiosk Mode (Device Owner)
- As device owner, the app can fully control lock task and exit without gestures.
- Requires ADB and a fresh (factory reset) device or dedicated profile.
- Example (advanced):
  - `adb shell dpm set-device-owner com.example.kidanimals/.DevAdminReceiver` (Not configured in this repo by default.)
- For most families, screen pinning with a PIN is sufficient and simpler.

Adding Images Manually
- Place JPG/PNG files into `app/src/main/assets/animals/`.
- Filenames should be simple ASCII if possible.
- Images are downsampled in-memory for performance.

Scraping Animal Images (Wikimedia Commons)
- Requirements: Python 3 + `pip install requests`.
- Example:
  - `python tools/scrape_wikimedia_animals.py --category "Category:Animal portraits" --limit 60 --out app/src/main/assets/animals`
- Licensing: Images on Commons have various CC licenses. This script saves `animals_metadata.csv` next to the assets — review and keep attributions per license.

Build & Run
- Open the project in Android Studio (Giraffe+), use JDK 17.
- Build and run on an Android 7.0+ device (API 24+ recommended API 29+).
- First run: enable app pinning in device settings (see above).

Notes
- The app hides back navigation and uses pinning to avoid home/recents. Parents can still exit via the in-app flow.
- If you want more categories (farm animals, sea animals, birds), run the scraper for each and copy images into the assets folder.

