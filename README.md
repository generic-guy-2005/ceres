# ceres
Hobby project to automate notes and track activities in Obsidian

### App
Currently pushed the functionalities for routing, time, and database

- Routes to `dashboard.html` established
- Created the `sync_time()` function which returns date and time values. Also used to refresh the current date and time

### Templates

- `dashboard.html`
The main screen of the project to monitor the overall activities. Current UI support the field for cash money, digital money, date, and time

- `add_cast.html`
A simple form to add persistent data for cash value manually

- `add_digital.html`
A simple form to add persistent data for digital or e-banking value manually

- `add_saving.html`
A simple form to set the current saving progress and target saving goal

### Bug

Due to symlink inconsistencies with Linux path, the app is currently run with `use_reloader=False`