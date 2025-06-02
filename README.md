# contacts
Manage a list of contacts

## Environmental Requirements
* Needs a CONTACTS environmental variable with the path to the contacts file

This can be done, for example, by adding this to `.bash_aliases`
```
export CONTACTS=$HOME/.contacts.yaml
```

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
