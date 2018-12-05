# blockchain
A simple Blockchain in Python.

## Environment

1. Python 3.6
2. Install Postman
3. Install pipenv, flask, requests, pickledb

## How to run this code

In this case, we will use two ports on one computer to simulate two nodes/users.

1. Run the servers:
	* `$ pipenv run python blockchain.py`
	* `$ pipenv run python blockchain.py -p 5001`
	
2. Start the Postman and add the following HTTP requests:
```
$ localhost:5000/chain
$ localhost:5001/chain
$ localhost:5000/transactions/new
$ localhost:5001/transactions/new
$ localhost:5000/mine
$ localhost:5001/mine
$ localhost:5000/restart
$ localhost:5001/restart
$ localhost:5000/nodes/register
$ localhost:5001/nodes/register
$ localhost:5000/nodes/resolve
$ localhost:5001/nodes/resolve
$ localhost:5000/pool
$ localhost:5001/pool
$ localhost:5000/getblocks
$ localhost:5001/getblocks
```