FROM python:3.8

ENV PYTHONUNBUFFERED=1

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
  && apt-get -y install --no-install-recommends git-all \
  && useradd -ms /bin/bash mapbiomas1 \
  && useradd -ms /bin/bash mapbiomas2 \ 
  && useradd -ms /bin/bash mapbiomas3 \
  && useradd -ms /bin/bash mapbiomas4 \
  && useradd -ms /bin/bash mapbiomas5 \
  && useradd -ms /bin/bash mapbiomas6 \
  && useradd -ms /bin/bash mapbiomas7 \
  && useradd -ms /bin/bash mapbiomas8 \
  && useradd -ms /bin/bash mapbiomas9 \
  && useradd -ms /bin/bash mapbiomas10 

WORKDIR /tmp/mapbiomas

COPY . .

RUN pip install --disable-pip-version-check --no-cache-dir -r requirements.txt

WORKDIR /mapbiomas

RUN rm -rf /tmp/mapbiomas