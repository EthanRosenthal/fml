from flask import render_template, request

from fml.app import app
from fml.optimizer import run_pipeline


@app.route('/', methods=['GET', 'POST'])
def index():
    calculate = request.form.get('calculate', False)
    if calculate:
        solution_msg = run_pipeline().split('\n')
    else:
        solution_msg = ''
    return render_template('index.html',
                           solution_msg=solution_msg)
