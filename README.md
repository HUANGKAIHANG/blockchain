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
/transactions/new and /nodes/register are POST requests and the rest are GET requests. HTTP-POST requests need to be filled in with JSON format arguments.

for /transactions/new
{
	"sender": "127.0.0.1:5000",
	"recipient": "127.0.0.1:5001",
	"amount": 50
}

for /nodes/register
{
	"nodes":["http://127.0.0.1:5001"]
}

3. Detailed step example

USE localhost:5000/nodes/register with data in JSON
{
	"nodes":["http://127.0.0.1:5001"]
}
to tell '5000' that '5001' is another node in the network.

USE localhost:5001/nodes/register with data in JSON
{
	"nodes":["http://127.0.0.1:5000"]
}
to tell '5001' that '5000' is another node in the network.

USE localhost:5000/transactions/new with data in JSON
{
	"sender": "127.0.0.1:5000",
	"recipient": "127.0.0.1:5001",
	"amount": 50
}
to create a new transaction in the current transaction pool.

USE localhost:5001/nodes/resolve to resolve the conflicts with node '5000' and know that there is a new transaction in the pool.

USE localhost:5001/mine to mine a new block

USE localhost:5000/nodes/resolve to resolve the conflicts with node '5001' and know that there is a longer valid chain in the network.

USE localhost:5000/chain, localhost:5000/pool, localhost:5000/getblocks, localhost:5001/chain, localhost:5001/pool, localhost:5001/getblocks to check the information of each node.