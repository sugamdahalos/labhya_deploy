FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install openssh-server and utilities
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       openssh-server sudo ca-certificates passwd \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir /var/run/sshd

# Create a non-root user 'ubuntu' with a default password that the agent
# will normally override. This is convenient for local dev/testing.
RUN useradd -m -s /bin/bash ubuntu \
    && echo "ubuntu:ubuntu" | chpasswd \
    && usermod -aG sudo ubuntu

# Enable password authentication (agent sets a stronger random password at runtime)
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config || true \
    && sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config || true \
    && sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config || true

EXPOSE 22

# Keep container running with sshd in foreground
CMD ["/usr/sbin/sshd","-D"]
