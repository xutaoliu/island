# Island Server

## Dev

### Build Env (When dependencies or [requirements.txt](requirements.txt) were changed)

- `docker build -t missingno/island-env -f env.Dockerfile .`

### Build Image

- `docker build -t missingno/island .`

### Generate Migrations

- `cd dev`
- `docker-compose -f docker-compose-migrations.yml up`
- CTRL-C when done.
- Copy all directories from `migrations/` to project root and overwrite all files.

### Rebuild Image

- `docker build -t missingno/island .`

## Run

- `cd dev`
- `docker-compose up`
