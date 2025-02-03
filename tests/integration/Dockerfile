# Dockerfile
FROM python:3.10

# Install necessary packages
RUN apt-get update && apt-get install -y \
    openssh-client \
    openssh-server \
    openmpi-bin \
    openmpi-common \
    libopenmpi-dev \
    sudo \
    libyaml-dev \
    python3-dev \
    pip


RUN mkdir /var/run/sshd && \
    mkdir -p /root/.ssh && \
    chmod 700 /root/.ssh

# Generate SSH keys and set permissions
RUN ssh-keygen -t rsa -b 4096 -f /root/.ssh/id_rsa -N ""


# Copy SSH configuration
COPY tests/integration/ssh_config /root/.ssh/config
RUN chmod 600 /root/.ssh/config
# Expose SSH port
EXPOSE 22

RUN useradd -m -s /bin/bash myuser
RUN echo "myuser:mypassword" | chpasswd
RUN echo 'myuser ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/myuser
RUN chmod 0440 /etc/sudoers.d/myuser

USER myuser

RUN mkdir -p ~/.ssh
RUN ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
RUN echo "Host *" > ~/.ssh/config
RUN echo "  StrictHostKeyChecking no" >> ~/.ssh/config
RUN chmod 600 ~/.ssh/config
RUN cat ~/.ssh/id_rsa.pub > ~/.ssh/authorized_keys

RUN echo export PATH=$PATH:~/.local/bin >> ~/.profile
RUN echo export PATH=$PATH:~/.local/bin >> ~/.bashrc
RUN export PATH=$PATH:~/.local/bin

WORKDIR /home/myuser/app
COPY . /home/myuser/app
RUN sudo chown -R myuser:myuser /home/myuser/app
RUN PATH=$PATH:~/.local/bin pip install --upgrade pip
RUN PATH=$PATH:~/.local/bin pip install -e .
RUN PATH=$PATH:~/.local/bin pip install mpi4py
ENV ODOP_PATH=/tmp/odop/


# Start SSH service
CMD ["sudo", "/usr/sbin/sshd", "-D"]