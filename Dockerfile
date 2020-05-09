FROM missingno/island-env

ADD . /app
WORKDIR /app

ENTRYPOINT ["./server-entrypoint.sh"]
