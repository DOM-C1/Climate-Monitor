FROM python:latest

WORKDIR /dashboard

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY Home.py .

COPY .streamlit/config.toml ./.streamlit/config.toml

COPY pages/1_About_this_site.py ./pages/1_About_this_site.py
COPY pages/2_Explore.py ./pages/2_Explore.py
COPY pages/3_Alerts_across_the_UK.py ./pages/3_Alerts_across_the_UK.py
COPY pages/4_Sign_Up.py ./pages/4_Sign_Up.py

ENTRYPOINT ["streamlit","run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]%
