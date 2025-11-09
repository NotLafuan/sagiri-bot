sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv ffmpeg
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m spacy download en_core_web_sm
