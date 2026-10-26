# syntax=docker/dockerfile:1
#
# Single-container Frappe Helpdesk image, built for Railway.
#
# Railway gives a service exactly one public port, so nginx (on $PORT) fronts
# gunicorn + the socket.io node server, and supervisord keeps the RQ workers and
# the scheduler alive alongside them. MariaDB and Redis are expected to be
# separate Railway services (Redis can also run inside this container — see
# docker/railway/README.md).
#
# The repo cannot be built standalone (see CLAUDE.md): it has to sit at
# frappe-bench/apps/helpdesk, because desk/src/socket.ts imports
# ../../../../sites/common_site_config.json and desk/package.json links
# @framework/ui to ../../frappe/ui. This image builds that bench.

ARG PYTHON_VERSION=3.14

FROM python:${PYTHON_VERSION}-slim AS base

ARG NODE_MAJOR=24
# frappe develop == 16.x-dev, which is what pyproject.toml pins.
ARG FRAPPE_BRANCH=develop
# Empty means "repository default branch", which is what CI uses.
ARG TELEPHONY_BRANCH=""

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore \
    BENCH_DIR=/home/frappe/frappe-bench \
    NODE_OPTIONS=--max-old-space-size=4096

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        cron \
        curl \
        wget \
        git \
        gosu \
        nginx \
        supervisor \
        redis-server \
        gettext-base \
        pkg-config \
        python3-dev \
        libmariadb-dev \
        mariadb-client \
        redis-tools \
        libssl-dev \
        libffi-dev \
        libjpeg-dev \
        zlib1g-dev \
        libcups2-dev \
        fontconfig \
        libfontconfig1 \
        libxrender1 \
        libxext6 \
        libx11-6 \
        xfonts-75dpi \
        xfonts-base \
        xz-utils \
        procps \
        rsync; \
    rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Node (CI builds this app with Node 24) — installed from the official tarball
# so we do not depend on a distro repo carrying the right major version.
# ---------------------------------------------------------------------------
RUN set -eux; \
    case "$(dpkg --print-architecture)" in \
        amd64) node_arch=x64 ;; \
        arm64) node_arch=arm64 ;; \
        *) echo "unsupported architecture: $(dpkg --print-architecture)" >&2; exit 1 ;; \
    esac; \
    base_url="https://nodejs.org/dist/latest-v${NODE_MAJOR}.x"; \
    tarball="$(curl -fsSL "${base_url}/" | grep -oE "node-v${NODE_MAJOR}\.[0-9]+\.[0-9]+-linux-${node_arch}\.tar\.xz" | head -n1)"; \
    test -n "${tarball}"; \
    curl -fsSL "${base_url}/${tarball}" -o /tmp/node.tar.xz; \
    tar -xJf /tmp/node.tar.xz -C /usr/local --strip-components=1 --no-same-owner \
        --exclude CHANGELOG.md --exclude LICENSE --exclude README.md; \
    rm /tmp/node.tar.xz; \
    npm install -g --force yarn@1; \
    node --version; \
    yarn --version

# ---------------------------------------------------------------------------
# wkhtmltopdf (PDF rendering). Frappe's patched generic build, same as CI.
# ---------------------------------------------------------------------------
RUN set -eux; \
    if [ "$(dpkg --print-architecture)" = "amd64" ]; then \
        wget -qO /tmp/wkhtmltox.tar.xz \
            https://github.com/frappe/wkhtmltopdf/raw/master/wkhtmltox-0.12.3_linux-generic-amd64.tar.xz; \
        tar -xf /tmp/wkhtmltox.tar.xz -C /tmp; \
        mv /tmp/wkhtmltox/bin/wkhtmltopdf /usr/local/bin/wkhtmltopdf; \
        chmod +x /usr/local/bin/wkhtmltopdf; \
        rm -rf /tmp/wkhtmltox /tmp/wkhtmltox.tar.xz; \
    else \
        echo "skipping wkhtmltopdf on $(dpkg --print-architecture)"; \
    fi

RUN pip install --no-cache-dir frappe-bench

RUN useradd --create-home --shell /bin/bash frappe

# ---------------------------------------------------------------------------
# Bench + frappe
# ---------------------------------------------------------------------------
USER frappe
WORKDIR /home/frappe

RUN git clone --depth 1 --branch "${FRAPPE_BRANCH}" https://github.com/frappe/frappe /home/frappe/frappe

# --no-backups: otherwise bench init calls `crontab -l` as the frappe user to
# install its backup cron job, which fails with "Permission denied" in the
# Railway build sandbox and aborts the build.
RUN bench init \
        --skip-redis-config-generation \
        --skip-assets \
        --no-backups \
        --frappe-path /home/frappe/frappe \
        --python "$(command -v python)" \
        frappe-bench \
    && rm -rf /home/frappe/frappe

WORKDIR /home/frappe/frappe-bench

RUN yarn --cwd apps/frappe install --frozen-lockfile || yarn --cwd apps/frappe install

# helpdesk declares required_apps = ["telephony"] in hooks.py
RUN set -eux; \
    if [ -n "${TELEPHONY_BRANCH}" ]; then \
        bench get-app --skip-assets --branch "${TELEPHONY_BRANCH}" https://github.com/frappe/telephony; \
    else \
        bench get-app --skip-assets https://github.com/frappe/telephony; \
    fi

# ---------------------------------------------------------------------------
# This app. `bench get-app` clones, so give it a git repo to clone from
# (.git is excluded from the build context to keep the image small).
# ---------------------------------------------------------------------------
COPY --chown=frappe:frappe . /home/frappe/src/helpdesk

RUN set -eux; \
    cd /home/frappe/src/helpdesk; \
    if [ ! -d .git ]; then \
        git init -q -b develop; \
        git add -A; \
        git -c user.email=build@localhost -c user.name=build commit -qm "container build"; \
    fi

RUN bench get-app --skip-assets /home/frappe/src/helpdesk && rm -rf /home/frappe/src

# ---------------------------------------------------------------------------
# Frontend assets. The desk SPA is built explicitly (vite writes into
# helpdesk/public/desk and helpdesk/www/helpdesk/index.html per vite.config.js),
# then `bench build` produces frappe's own bundles and the sites/assets symlinks.
# ---------------------------------------------------------------------------
RUN yarn --cwd apps/helpdesk install --frozen-lockfile || yarn --cwd apps/helpdesk install

RUN yarn --cwd apps/helpdesk/desk build

RUN bench build --app frappe --production || bench build --app frappe

# Belt and braces: make sure every app is reachable under /assets even if
# bench's symlink pass skipped one.
RUN set -eux; \
    cd /home/frappe/frappe-bench/sites; \
    mkdir -p assets; \
    for app in frappe telephony helpdesk; do \
        if [ -d "../apps/${app}/${app}/public" ]; then \
            ln -sfn "../../apps/${app}/${app}/public" "assets/${app}"; \
        fi; \
    done

# Clean the node_modules that were only needed to build the SPA.
RUN rm -rf apps/helpdesk/node_modules apps/helpdesk/desk/node_modules \
    && yarn cache clean || true

# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------
USER root

# Railway mounts its volume over sites/, which would hide the built assets and
# apps.txt. Keep a pristine copy the entrypoint re-seeds from on every boot.
RUN mkdir -p /opt/frappe \
    && cp -a /home/frappe/frappe-bench/sites /opt/frappe/sites-template \
    && chown -R frappe:frappe /opt/frappe

COPY docker/railway/entrypoint.sh /usr/local/bin/helpdesk-entrypoint
COPY docker/railway/nginx.conf.template /opt/frappe/nginx.conf.template
COPY docker/railway/supervisord.conf /opt/frappe/supervisord.conf

RUN chmod +x /usr/local/bin/helpdesk-entrypoint \
    && mkdir -p /var/log/supervisor /var/lib/nginx \
    && chown -R frappe:frappe /var/lib/nginx

ENV PORT=8080
EXPOSE 8080

ENTRYPOINT ["/usr/local/bin/helpdesk-entrypoint"]
CMD ["supervisord"]