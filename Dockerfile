FROM missingno/island-env

ADD . /app
WORKDIR /app

RUN chmod u+x server-entrypoint.sh
RUN chmod u+x migrations-entrypoint.sh

ENTRYPOINT ["./server-entrypoint.sh"]
