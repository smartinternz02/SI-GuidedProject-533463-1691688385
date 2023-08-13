FROM python:3.11
RUN mkdir -p /std_app
WORKDIR /std_app
COPY . /std_app
RUN chmod 644 DigiCertGlobalRootCA.crt
RUN python -m pip install -r /std_app/requirements.txt
EXPOSE 5000
CMD ["python", "/std_app/app.py"]