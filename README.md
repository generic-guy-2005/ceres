# ceres
Hobby project to automate notes and track activities in Obsidian

### App
Currently pushed the functionalities for routing, time, and database

- Routes to `dashboard.html` established
- Created the `sync_time()` function which returns date and time values. Also used to refresh the current date and time
- Created the `get_next()` function to automates markdown creation based on time and date
- Created the `load_data()` to load values and `save_all_data()` to save new values to `settings.json`

### Templates

- `dashboard.html`
The main screen of the project to monitor the overall activities. Current UI support the field for cash money, digital money, date, and time

- `add_cast.html`
A simple form to add persistent data for cash value manually

- `add_digital.html`
A simple form to add persistent data for digital or e-banking value manually

- `add_saving.html`
A simple form to set the current saving progress and target saving goal

- `edit_expense.html`
Form to edit the database value of existing expenses

- `report.html`
Contains the template to be stored to Obsidian and saved as markdown

- `upload_media.html`
Form to add new media into the database. Support both images and videos

### Bug

Due to symlink inconsistencies with Linux path, the app is currently run with `use_reloader=False`