FROM python:3.10-slim

# [Optional] If your pip requirements rarely change, uncomment this section to add them to the image.
# COPY requirements.txt /tmp/pip-tmp/
# RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
#    && rm -rf /tmp/pip-tmp

# [Optional] Uncomment this section to install additional OS packages.
# RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
#     && apt-get -y install --no-install-recommends <your-package-list-here>

# [Optional] Uncomment this line to install global node packages.
# RUN su vscode -c "source /usr/local/share/nvm/nvm.sh && npm install -g <your-package-here>" 2>&1

ENV PYTHONUNBUFFERED=1 \
  # prevents python creating .pyc files which reduces docker image size
  PYTHONDONTWRITEBYTECODE=1 \
  \
  # pip
  # don't use cache
  PIP_NO_CACHE_DIR=off \
  # don't check version when installing
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  # increases default timeout
  PIP_DEFAULT_TIMEOUT=100 \
  \
  # poetry
  # set poetry version
  POETRY_VERSION=1.1.13 \
  # prevents poetry from creating virtualenvs because we already are in a docker container
  POETRY_VIRTUALENVS_CREATE=false \
  # make poetry install to this location
  POETRY_HOME="/opt/poetry" \
  # do not ask any interactive question
  POETRY_NO_INTERACTION=1

# prepend poetry to path
ENV PATH="$POETRY_HOME/bin:$PATH"

RUN apt-get update -y \
  && apt-get install --no-install-recommends -y \
  # deps for installing poetry
  curl \
  # deps for building python deps
  build-essential \
  # install git
  git

# install poetry - respects $POETRY_VERSION & $POETRY_HOME
RUN curl -sSL https://install.python-poetry.org | python -