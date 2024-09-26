# Getting Started

The op-analytics repo is the one stop shop for the Data Team at OP Labs.


## Virtual Environment

Our project is managed using [uv](https://docs.astral.sh/uv/). 
Follow the instructions on the uv docs to install uv on your platform.


Once you have uv installed you can create your development virtualenv by running:
```
$ uv sync
```


## Directory Structure

```{danger}
We are currently in the process of migrating to our new directory structure for the project.
There are a lot of directories in the top-level at the moment that we hope to reorganize
over time.
```

### `src/`

The project is structured as a [uv Workspace](https://docs.astral.sh/uv/concepts/workspaces/).
This means there is one top-level ``src/`` directory and multiple individual workspace member
packages under ``packages/``.

Any python implementation that we leverage for data work will be implemeted as part of a package.
At the top-level we only define a command-line interface, which is the default way by which we
interact with our functionality.


###  `dbt/`

The ``dbt/`` directory contains a `dbt <https://www.getdbt.com/>`_ project. This is still work in progress, but we
hope all our data warehouse tables will be modeld with dbt.

The dbt autogenrated docs are written out to ``docs/dbt``.


### `sphinx/`

We use `sphinx <https://www.sphinx-doc.org/en/master/>`_ to write documentation for our project. The ``sphinx``
directory contains or sphinx setup.

The build output from sphinx is written to ``docs/``. Our github-pages configuration is set up to serve a static site
from the ``docs/`` directory.


## CLI


As mentioned above, the top-level ``src/`` python module for this project defines the ``opdata`` command-line interface.
This CLI is used to expose the many utilities that are defined as part of our project member packages.

Some of this utilities are internal. For example to help us autogenerate code or documentation, or to provide a simple
way to execute some logic during CI/CD.

We also have utilities that have external use cases. For example fetching onchain data from RPC nodes.

You can see the CLI help message by running:
```
$ uv run opdata --help
```

Or get help about a specific subcommand:
```
$ uv run opdata rpc --help
```