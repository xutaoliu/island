FROM missingno/island-env:v1

ADD . /app
WORKDIR /app

ENTRYPOINT ["./server-entrypoint.sh"]
