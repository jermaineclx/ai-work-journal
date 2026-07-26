# docker/

The `Dockerfile` and `docker-compose.yml` live at the repository root
(standard convention — Docker needs the build context there to see
`app/`, `requirements.txt` and `main.py` without extra `-f`/context
flags). This folder is reserved for any future auxiliary container
assets (e.g. a separate worker image, entrypoint scripts).
