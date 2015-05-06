
# general config for all nodes (supposed to be packaged)

# enable changing the server_digest in this file when a new key is generated
update_settings = False
update_settings = True # !!!! TODO: should be False in releases or compiled versions

keyfile = 'node.key'
server_digest = 'dd7c36be38d994b99b84d7ab9d63959bb21dd55b9a83375782e12fde0737273d'

http_port = 8000
prefer_subnet = '192.168.10'
ignore_subnets = {
	'127.0.0': 1,	# ignore localhost
	'10.0.2': 1,	# virtualbox nat adapter
}

address = {}		# webserver addr and port gets set after it starts
