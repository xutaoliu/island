# Island Server

## Build yourself

- `docker build -t missingno/island-env:<version> -f env.Dockerfile .`
- Change the first line of [Dockerfile](Dockerfile) to `FROM missingno/island-env:<version>`
- `docker build -t missingno/island:<version> .`

## Run

- `cd env`
- `docker-compose up`
