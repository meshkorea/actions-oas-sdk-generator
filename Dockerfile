FROM openjdk:8-jdk-slim

# hadolint ignore=DL3009
RUN apt-get update -qq && apt-get install -qq --no-install-recommends \
  curl \
  gnupg2

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN curl -sL https://deb.nodesource.com/setup_12.x | bash -
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
RUN apt-get update -qq && apt-get install -qq --no-install-recommends \
  nodejs yarn wget unzip python3-pip\
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN mkdir /opt/gradle && \
  wget -q "https://downloads.gradle.org/distributions/gradle-5.6.2-bin.zip" -O "gradle-5.6.2-bin.zip" && \
  unzip -q -d /opt/gradle gradle-5.6.2-bin.zip && \
  mkdir /openapi-generator && \
  wget -q https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/4.1.3/openapi-generator-cli-4.1.3.jar \
  -O /openapi-generator/openapi-generator-cli.jar && \
  ln -s /opt/gradle/gradle-5.6.2/bin/gradle /usr/bin/gradle && \
  pip3 install --upgrade setuptools && \
  pip3 install PyYAML 

# COPY gradle /openapi-generator/gradle
COPY entrypoint.py /entrypoint.py

RUN chmod +x /entrypoint.py

ENTRYPOINT ["/entrypoint.py"]

