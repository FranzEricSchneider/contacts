Manage a list of contacts

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
Note - the `/usr/bin/python3` part is so the system startup file will run. If you don't want to use that, you can just `pip` install in whatever environment you're using.

3. Install the repo
```
pip install -e .
```

4. Make systemd startup file at `~/.config/systemd/user/check-contacts.service`, replacing the `<username>` with your own. If you want to run in a miniconda environment, use `#!/home/<username>/miniconda3/bin/python3` instead of `/usr/bin/python3`.

```
[Unit]
Description=Check overdue contacts and show Zenity popup
After=graphical-session.target
Wants=graphical-session.target

[Service]
Environment=CONTACTS=/home/<username>/.contacts.yaml
ExecStart=/usr/bin/python3 -m contacts.check_contacts
Restart=no

[Install]
WantedBy=graphical-session.target

```

5. Enable it
```bash
systemctl --user daemon-reload
systemctl --user enable check-contacts
```

6. To test it immediately
```bash
systemctl --user start check-contacts
```


## Environmental Requirements

Needs a CONTACTS environmental variable with the path to the contacts file. This can be done, for example, by adding this to `.bash_aliases`:
```bash
export CONTACTS=$HOME/.contacts.yaml
```

## Use

You can ingest new content
```bash
./ingest.py updates.txt
```

If the updates are of the format
```
name
key: content
key: content

name
key:content
```

And you can print the contacts:
```bash
./print.py -h  # for multiple flag options
```

## Testing

The project uses pytest for testing. To run the tests:
```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=.

# Run tests verbosely
pytest -v
```

All test files are located in the `tests/` directory.

## Design Requirements
* Ingest and understand a yaml file which stores for each contact name, address, frequency, and a series of timestamped updates
* * Optional: characteristics, tags, urls
* Have timed contact reminders as well as random reminders
* Have search functionality for names and locations
* Have easy to use full ingestion and update ingestion
* Have auto-run functionality on startup

### Stretch goals
* Have an auditory option where it will read bios
* Option to open urls
