from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

##### ROUTES ######
@app.route('/')
def home():
  """Home Page - Dashboard"""
  return render_template('dashboard.html')

@app.route('/login', methods=['GET','POST'])
def login():
  """Route for users to be able to log into their account"""
  def login():
    if request.method == 'POST':
      return redirect(url_for('home'))
    return render_template('login.html')

if __name__ == '__main__':
  app.run(debug=True)
  

