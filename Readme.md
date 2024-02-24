1.<!-- Install Nginx: -->
sudo apt-get update
sudo apt-get install nginx

2.Create Enivironment For project 
    python3 -m venv env

3.install All requirements from requerements.txt file
    pip install -r requirements.txt

4.setup mongo

5.<!-- Start Flask Application Instances: -->
gunicorn -b 0.0.0.0:5000 your_app:app
gunicorn -b 0.0.0.0:5001 your_app:app
