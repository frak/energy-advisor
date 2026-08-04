FROM python:3.12-slim

# --- supercronic: a cron built for containers -------------------------------
# Runs in the foreground as PID 1, logs to stdout, and passes the container's
# environment through to jobs (unlike system cron). Pinned + checksum-verified.
ARG SUPERCRONIC_VERSION=v0.2.48
ARG TARGETARCH
# SHA1 sums published on the supercronic release page for each arch.
ARG SUPERCRONIC_SHA1_amd64=016b7c9aebfc8d9fd9526e8ba33b191fc524485f
ARG SUPERCRONIC_SHA1_arm64=2ab9b3bdcf290f60b59700aad876b6e68f3a6b06

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends curl ca-certificates; \
    rm -rf /var/lib/apt/lists/*; \
    case "${TARGETARCH}" in \
        amd64) SHA1="${SUPERCRONIC_SHA1_amd64}" ;; \
        arm64) SHA1="${SUPERCRONIC_SHA1_arm64}" ;; \
        *) echo "unsupported arch: ${TARGETARCH}" >&2; exit 1 ;; \
    esac; \
    BIN="supercronic-linux-${TARGETARCH}"; \
    curl -fsSLO "https://github.com/aptible/supercronic/releases/download/${SUPERCRONIC_VERSION}/${BIN}"; \
    echo "${SHA1}  ${BIN}" | sha1sum -c -; \
    chmod +x "${BIN}"; \
    mv "${BIN}" /usr/local/bin/supercronic

# --- application ------------------------------------------------------------
WORKDIR /app

# Install deps first so the layer caches across code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# data/ holds forecasts.json, shared between the collector and the daily job.
# Mounted as a volume in compose so it survives rebuilds.
VOLUME ["/app/data"]

CMD ["supercronic", "/app/crontab"]
