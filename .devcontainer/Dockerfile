FROM mcr.microsoft.com/devcontainers/python:1-3.11-bookworm

# The upstream image can retain a Yarn APT source whose signing key is not
# available during a Codespaces feature build. ActionCharter does not use Yarn,
# so remove only that source before Dev Container features run apt-get update.
RUN find /etc/apt/sources.list.d -type f -exec \
        sed -i '\|https://dl.yarnpkg.com/debian|d' {} + \
    && find /etc/apt/sources.list.d -type f -empty -delete
