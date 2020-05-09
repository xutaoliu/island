FROM missingno/island-env:v2

ADD . /app
WORKDIR /app

ENTRYPOINT ["./server-entrypoint.sh"]
