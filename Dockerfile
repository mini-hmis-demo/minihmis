FROM python:3.12-alpine

LABEL org.opencontainers.image.title="MiniHMIS (demo)" \
      org.opencontainers.image.description="DEMO ONLY - fake health information system for a security pre-disclosure demo"

WORKDIR /srv/minihmis
COPY VERSION ./
COPY app ./app

RUN adduser -D -H minihmis
USER minihmis

ENV PORT=8080
EXPOSE 8080
CMD ["python", "app/minihmis.py"]
