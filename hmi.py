#!flask/bin/python
# -*- coding: utf-8 -*-

import os
from flask import Flask, render_template, flash, request, redirect, url_for
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.exceptions import *

# App config
DEBUG = True
app = Flask(__name__,static_url_path='/templates')
app.config.from_object(__name__)
app.config['SECRET_KEY'] = os.urandom(24)


@app.route("/", methods=['GET'])
def index():
	return render_template('index.html')


@app.route("/", methods=['POST'])
def connect():
	address = request.form['address']
	port = int(request.form['port'])
	#print address, " ", port
	client = ModbusTcpClient(address, port)
	succeed = client.connect()
	if succeed:
		client.close()
		return redirect("/"+str(address)+":"+str(port))
	else:
		return render_template('index.html', error="Connection has failed. Please, check IP address and port.")

	
@app.route("/<address>:<port>")
def menu(address, port):
	port = int(port)
	client = ModbusTcpClient(address, port)
        succeed = client.connect()

	if not succeed:
		return redirect('/')
	else:
		client.close()
		return render_template('menu.html', address=address, port=port)


def operate(address, port, request, operation):

	# fields of the form
	start=request.form['address']
        value=request.form['value']
        unitId=request.form['unitId']

	# connection to the slave
	port = int(port)
	client = ModbusTcpClient(address, port)
	succeed = client.connect()

	html_template = operation+".html"

   	# no connection
        if not succeed:
		return render_template(html_template, address=address, port=port, form=request.form, error="Connection has failed. Please, check IP address and port on URL or go back to homepage.")

	# operation to launch
	if operation == 'read-discrete-inputs':
		result = client.read_discrete_inputs(address=int(start),count=int(value),unit=int(unitId))
	elif operation == 'read-coils':
		result = client.read_coils(address=int(start),count=int(value),unit=int(unitId))
	elif operation == 'read-holding-registers':
		result = client.read_holding_registers(address=int(start),count=int(value),unit=int(unitId))
	elif operation == 'read-input-registers':
		result = client.read_input_registers(address=int(start),count=int(value),unit=int(unitId))
	elif operation == 'write-coil':
		result = client.write_coil(int(start),int(value),unit=int(unitId))
	elif operation == 'write-holding-register':
		result = client.write_register(int(start),int(value),unit=int(unitId))

	client.close()

	# error in operation
	if result.isError():
		return render_template(html_template, address=address, port=port, form=request.form, error=result)
	
	# display results 	
	else:
		# op : read discrete values
		if operation in ["read-discrete-inputs", "read-coils"]:
			visual_result = []
			for b in result.bits:
				if b:
					visual_result.append('On')
				else:
					visual_result.append('Off')
			flash(str(visual_result))

		# op : read registers
		elif operation in ["read-holding-registers", "read-input-registers"]:
			flash(str(result.registers))
		
		# op : write values
		elif operation in ['write-coil','write-holding-register']:
			flash("Success!")
		
		return render_template(html_template, form=request.form, address=address, port=port)



def panel(address, port, operation, form):

	# only accept url-based queries if address and port are correctly functioning

	client = ModbusTcpClient(address, int(port))
	succeed = client.connect()
	#print(succeed)

	if not succeed:
		return redirect('/')
	else:	
		client.close()
		return render_template(operation+".html", form=form, address=address, port=port)


@app.route("/<address>:<port>/<operation>", methods=['GET','POST'])
def launch_operation(address, port, operation):

	supported_operations = ['read-discrete-inputs','read-coils','read-holding-registers','read-input-registers','write-coil','write-holding-register']

	if operation not in supported_operations:
		return redirect('/')

	if request.method == 'POST':
		return operate(address, port, request, operation)
	else:
		return panel(address, port, operation, request.form)


if __name__ == "__main__":
    app.run(host=0.0.0.0, port=5000)
