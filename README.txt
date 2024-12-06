# LLaMA Text Generation Backend

This project provides a backend for running a text generation model using GPT-2. 
It consists of a Python server using Flask and a Node.js server using Express.js. 
The Python server handles the text generation, while the Node.js server forwards requests from the front-end to the Python server.


### 1. Clone the Repository

git clone <repository-url>
cd llama-backend


### 2. Create Python Virtual Environment

ensure pip is installed

python -m venv venv
pip install transformers
pip install flask

python app.py
node server.js

### 3. (In PitchBotFE) 

npm run dev



