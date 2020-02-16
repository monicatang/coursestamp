FROM gcr.io/google-appengine/python

# Create a virtualenv for dependencies. This isolates these packages from
# system-level packages.
# Use -p python3 or -p python3.7 to select python version. Default is version 2.
RUN virtualenv /env -p python3

# Setting these environment variables are the same as running
# source /env/bin/activate.
ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH

RUN apt-get update && apt-get install -y \
        vim \
        curl \
        wget \
        git \
        make \
        netcat \
        python \
        python2.7-dev \
        g++ \
        bzip2 \
        binutils
###############################################################################
RUN apt-get install -y portaudio19-dev libopenblas-base libopenblas-dev pkg-config git-core cmake python-dev liblapack-dev libatlas-base-dev libblitz0-dev libboost-all-dev libhdf5-serial-dev libqt4-dev libsvm-dev libvlfeat-dev  python-nose python-setuptools python-imaging build-essential libmatio-dev python-sphinx python-matplotlib python-scipy
# additional dependencies
RUN apt-get install -y \
        libasound2 \
        libasound-dev \
        libssl-dev

RUN pip install pyaudio

# Copy the application's requirements.txt and run pip to install all
# dependencies into the virtualenv.
ADD requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt
# RUN pipwin install pyaudio


# Add the application source code.
ADD . /app

# Run a WSGI server to serve the application. gunicorn must be declared as
# a dependency in requirements.txt.
CMD gunicorn -b :$PORT main:app