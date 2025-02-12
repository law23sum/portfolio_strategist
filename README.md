# The Portfolio Strategist

Financia is a financial software (fintech) company that services online users with intuitive, user-friendly financial tools to create, monitor, and advise on budgets, portfolios, and investments, all to promote a simplified, interactive, and reliable approach to easily manage your assets.

## Installation - Docker

The easiest way to get up and running is with [Docker](https://www.docker.com/).

Just [install Docker](https://www.docker.com/get-started) and
[Docker Compose](https://docs.docker.com/compose/install/)
and then run:

```
make init
```

This will spin up a database, web worker, celery worker, and Redis broker and run your migrations.

You can then go to [localhost:8000](http://localhost:8000/) to view the app.

*Note: if you get an error, make sure you have a `.env` file, or create one based on `.env.example`.*

### Using the Makefile

You can run `make` to see other helper functions, and you can view the source
of the file in case you need to run any specific commands.

For example, you can run management commands in containers using the same method
used in the `Makefile`. E.g.

```
docker compose exec web uv run manage.py createsuperuser
```

## Installation - Native

You can also install/run the app directly on your OS using the instructions below.

You can setup a virtual environment and install dependencies in a single command with:

```bash
uv sync
```

This will create your virtual environment in the `.venv` directory of your project root.

## Set up database

*If you are using Docker you can skip these steps.*

Create a database named `portfolio_strategist`.

```
createdb portfolio_strategist
```

Create database migrations:

```
uv run manage.py makemigrations
```

Create database tables:

```
uv run manage.py migrate
```

## Running server

**Docker:**

```bash
make start
```

**Native:**

```bash
uv run manage.py runserver
```

## Building front-end

To build JavaScript and CSS files, first install npm packages:

**Docker:**

```bash
make npm-install
```

**Native:**

```bash
npm install
```

Then build (and watch for changes locally):

**Docker:**

```bash
make npm-watch
```

**Native:**

```bash
npm run dev-watch
```

## Running Celery

Celery can be used to run background tasks.
If you use Docker it will start automatically.

You can run it using:

```bash
celery -A portfolio_strategist worker -l INFO --pool=solo
```

Or with celery beat (for scheduled tasks):

```bash
celery -A portfolio_strategist worker -l INFO -B --pool=solo
```

Note: Using the `solo` pool is recommended for development but not for production.

## Updating translations

**Docker:**

```bash
make translations
```

**Native:**

```bash
uv run manage.py makemessages --all --ignore node_modules --ignore .venv
uv run manage.py makemessages -d djangojs --all --ignore node_modules --ignore .venv
uv run manage.py compilemessages --ignore .venv
```

## Google Authentication Setup

To setup Google Authentication, follow the [instructions here](https://docs.allauth.org/en/latest/socialaccount/providers/google.html).

## Installing Git commit hooks

To install the Git commit hooks run the following:

```shell
$ uv run pre-commit install --install-hooks
```

Once these are installed they will be run on every commit.

For more information see the [docs](https://docs.saaspegasus.com/code-structure.html#code-formatting).

## Running Tests

To run tests:

**Docker:**

```bash
make test
```

**Native:**

```bash
uv run manage.py test
```

Or to test a specific app/module:

**Docker:**

```bash
make test ARGS='apps.utils.tests.test_slugs --keepdb'
```

**Native:**

```bash
uv run manage.py test apps.utils.tests.test_slugs
```

On Linux-based systems you can watch for changes using the following:

**Docker:**

```bash
find . -name '*.py' | entr docker compose exec web uv run manage.py test apps.utils.tests.test_slugs
```

**Native:**

```bash
find . -name '*.py' | entr uv run manage.py test apps.utils.tests.test_slugs
```
