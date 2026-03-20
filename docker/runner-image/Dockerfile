FROM ubuntu:22.04

ARG RUNNER_VERSION=2.329.0

RUN apt-get update && apt-get install -y \
    curl \
    jq \
    git \
    ca-certificates \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for the runner
RUN useradd -m runner && \
    echo "runner ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

WORKDIR /actions-runner

RUN curl -fsSL -o actions-runner.tar.gz \
    "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz" && \
    tar xzf actions-runner.tar.gz && \
    rm actions-runner.tar.gz && \
    ./bin/installdependencies.sh

# Fix ownership so the non-root user can run the agent
RUN chown -R runner:runner /actions-runner

COPY start.sh .
RUN chmod +x start.sh

USER runner

ENTRYPOINT ["./start.sh"]
