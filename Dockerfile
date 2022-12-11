FROM python:3.7.13-slim-bullseye as base

WORKDIR /usr/src/app

COPY ["setup.py", "README.rst", "./"]
COPY ["xlsx2sqlite/", "./xlsx2sqlite/"]

RUN python -m venv /usr/src/app/venv

ENV PATH="/usr/src/app/venv/bin:$PATH"

RUN pip install --no-cache-dir . \
    && pip install -I 'nuitka>0.7,<0.8'


FROM python:3.7.13-slim-bullseye as build

RUN apt-get update -y \
    && apt-get install --no-install-recommends -y \
        locales \
        build-essential \
        ccache \
        patchelf \
        clang \
        libfuse-dev \
        upx \
    && rm -rf /var/cache/apt/archives \
    && rm -rf /var/lib/apt/lists/* \
	&& localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8 

ENV LANG en_US.utf8

WORKDIR /usr/src/app

COPY --from=base /usr/src/app/venv ./venv
COPY --from=base /usr/src/app/xlsx2sqlite ./xlsx2sqlite

ENV PATH="/usr/src/app/venv/bin:$PATH"
ENV PYTHONPATH="/usr/src/app/xlsx2sqlite:$PYTHONPATH"

RUN python -m nuitka \
        --standalone \
        --nofollow-import-to=pytest \
        --python-flag=nosite,-O \
        --plugin-enable=anti-bloat,implicit-imports,data-files,pylint-warnings \
        --clang \
        --warn-implicit-exceptions \
        --warn-unusual-code \
        --prefer-source-code \
        xlsx2sqlite/xlsx2sqlite.py \
    && cd xlsx2sqlite.dist/ \
    && ldd xlsx2sqlite | grep "=> /" | awk '{print $3}' | xargs -I '{}' cp --no-clobber -v '{}' . \
    && ldd xlsx2sqlite | grep "/lib64/ld-linux-x86-64" | awk '{print $1}' | xargs -I '{}' cp --parents -v '{}' . \
    && cp --no-clobber -v /lib/x86_64-linux-gnu/libgcc_s.so.1 . \
    && mkdir -p ./lib/x86_64-linux-gnu/ \
    && cp --no-clobber -v /lib/x86_64-linux-gnu/libresolv* ./lib/x86_64-linux-gnu \
    && cp --no-clobber -v /lib/x86_64-linux-gnu/libnss_dns* ./lib/x86_64-linux-gnu \
    && upx -9 xlsx2sqlite


FROM python:3.7.13-slim-bullseye

ARG USER_ID
ARG GROUP_ID

RUN getent group ${GROUP_ID} || addgroup --gid $GROUP_ID app \
    && adduser --disabled-password --gecos '' --uid $USER_ID --gid $GROUP_ID app

COPY --chown=${USER_ID}:${GROUP_ID} --from=build /usr/src/app/xlsx2sqlite.dist/ /opt/xlsx2sqlite

USER app

ENTRYPOINT [ "/opt/xlsx2sqlite/xlsx2sqlite" ]
