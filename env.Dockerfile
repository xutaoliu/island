FROM python:3.6

COPY ./requirements.txt /tmp/requirements.txt
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r /tmp/requirements.txt
