'''
from flask import Flask

#from grouping import app
app = Flask(__name__)
import grouping.views

if __name__ == "__main__":
    app.run(port=5000, debug=True,host='0.0.0.0')
'''
