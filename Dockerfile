FROM python:3.12.5-alpine3.20

# add mono repo and mono
RUN apk add --no-cache mono --repository http://dl-cdn.alpinelinux.org/alpine/edge/testing

# Install dependencies
RUN apk add --no-cache --upgrade \
    ffmpeg mediainfo python3 git py3-pip python3-dev python3-tkinter g++ cargo mktorrent rust \
    && apk add --no-cache mono --repository http://dl-cdn.alpinelinux.org/alpine/edge/testing

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Set the timezone
ENV TZ=Europe/Kiev
RUN ln -sf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# create virtual environment
RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"

# change workdir
WORKDIR /UTOPIA-Upload-Assistant

# install reqs
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy everything
COPY . .

# Define volumes
VOLUME /UTOPIA-Upload-Assistant/data
VOLUME /UTOPIA-Upload-Assistant/tmp

# Set file ownership
RUN chown -R appuser:appgroup /UTOPIA-Upload-Assistant

# Switch to the non-root user
USER appuser

CMD ["sh"]