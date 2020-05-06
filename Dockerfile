FROM missingno/island-env:v1

ADD . /app
WORKDIR /app

ENTRYPOINT ["sh", "./server-entrypoint.sh"]
