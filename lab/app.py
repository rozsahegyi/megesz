
# provides a custom wsgi application which determines how a host should act
#
# several machines would run django, communicating on lan via udp and http
# machines (nodes) either act as a Server or a Client
#	if a valid server key is provided, the app will create a Server node
#	otherwise a Client is made, which broadcasts a public key via udp
#	the Server receives these, stores client ip/keys, and sends its public key
#	Servers/Clients validate keys, communication is ecnrypted both ways after
# client machines act as thin clients, and serve pages only locally
# in views, the Server or Client instance is available under request.node

import os, time, re, threading, collections
from django.core.handlers.wsgi import WSGIHandler, WSGIRequest
from django.conf import settings
import secure, network
from . import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

Message = collections.namedtuple('Message', 'owner target via content')


class Client(network.Node, network.SimpleUdp):
	"""Clients try to find the server node via udp, and store it's ip/key."""

	def __init__(self, config={}, key=None):
		if not self.ips:
			return logger.info("No local networks detected - stopping.")
		self.ip = self.__dict__.get('ip', self.ips[0])
		self.logger = logger.getChild(str(self))

		if getattr(settings.LAB, 'local', None):
			port = settings.LAB.address.get('port')
			if not port:
				self.logger.error('webserver port not found (needed for local mode)')
			else:
				self.ip += ':%s' % port
				self.logger = logger.getChild(str(self))
				self.logger.debug('set ip to %s (local mode)', self.ip)

		self.server = network.mapping({'ip': '', 'key': None})
		self.messages = []
		self.updates = threading.Event()
		self.updates.counter = 0
		self.listen_udp()
		threading.Thread(target=self.broadcast_info).start()

	@classmethod
	def str(cls, ip, name=None):
		if not name: name = cls.__name__.lower()
		if ip: ip = ip.split('.')[-1].split(':')[-1]
		return '%s #%s' % (name, ip or '?')

	def __str__(self):
		return self.__class__.str(getattr(self, 'ip', None))

	@property
	def role(self):
		return self.__class__.__name__.lower()

	@property
	def is_server(self):
		return self.role == 'server'

	def broadcast_info(self, target=None):
		"""Thread; sends to a target ip, or broadcasts and asks for responses."""
		if target: target = target.split(':')[0]
		data = {
			'role': self.role,
			'ip': self.ip,
			'key': self.key.export(),
			'signature': self.key.sign(self.ip),
			'respond': not target,
		}
		self.broadcast_udp(data, target)

	def handle_udp(self, data):
		if data.ip == self.ip: return
		if data.get('key'): self.exchange_keys(data)

	def exchange_keys(self, data):
		"""Called when a key is received. Sends info back if requested."""
		if data.role == self.role: return
		self.logger.debug('new key from: %s %s', data.role, data.ip)
		if not self.verify_key(data): return
		self.received_key(data)
		if data.get('respond'): self.broadcast_info(data.ip)

	def verify_key(self, data, digest=None):
		"""Check key signature. Clients also match digest vs server_digest."""
		# clients check the key's digest against the server_digest setting
		if not digest and not self.is_server:
			digest = settings.LAB.server_digest
		try:
			key = secure.Key(data.key)
			verified = key.verify(data.ip, data.signature)
			matched = not digest or key.match_digest(data.key, digest)
			return verified and matched
		except Exception as e:
			self.logger.error('verify_key failed: %s', e.args)

	def received_key(self, data):
		key = secure.Key(data.key)
		if self.server.ip != data.ip or self.server.key.public.key.n != key.public.key.n:
			self.logger.info('server %s: %s %s', 'updated' if self.server.ip else 'found', data.ip, key)
		self.server.ip = data.ip
		self.server.key = key

	def remote_key(self, req=None):
		return self.server.key

	def update(self):
		"""Any polling requests waiting for this event are activated."""
		self.updates.counter += 1
		self.updates.set()
		self.updates.clear()

	def add_message(self, owner, target, via, content):
		if not owner: owner = str(self)
		if not target: target = str(self)
		self.messages.append(Message(owner, target, via, content))

	def add_messages(self, messages):
		for m in messages: self.add_message(*m)
		self.update()

	def test_updates(self):
		def run():
			for i in range(2):
				time.sleep(5)
				self.update()
		threading.Thread(target=run).start()


class Server(Client):
	"""Maintains and communicates content for client nodes."""

	def __init__(self, *args, **kw):
		super(Server, self).__init__(*args, **kw)
		self.clients = {}

	def received_key(self, data):
		if self.clients.get(data.ip):
			return self.logger.debug('already have a client %s.', data.ip)
		self.clients[data.ip] = secure.Key(data.key)
		self.logger.info('new client: %s %s', data.ip, self.clients[data.ip])

	def remote_key(self, ip):
		return self.clients.get(ip)


class CustomRequest(WSGIRequest):
	"""Class to maintain an active Client/Server instance."""
	node = None


class Application(WSGIHandler):
	"""
	Customized wsgi application.
	Creates a Client or Server instance (if a valid server key is found),
	accessible in self.node, and also in request.node when in views.
	"""

	node = None
	request_class = CustomRequest

	def __init__(self, *args, **kw):
		super(Application, self).__init__(*args, **kw)
		config, key, verified, message = self.load_config()
		cls = Server if verified else Client
		self.node = cls(config, key)
		CustomRequest.node = self.node
		logger.info('Running %s on %s (%s)' % (cls.__name__, self.node.ip, message))

	def load_config(self):
		"""
		Try loading the config, and verify the key or export a new one.
		If a key is valid and matches the server_digest, run in server mode.
		"""

		key = verified = message = None
		keyfile = settings.LAB.keyfile
		config = {}
		try:
			import config as conf
			config = network.mapping(vars(conf))
		except Exception as e:
			raise

		# passphrase in config but no keyfile? generate a key, and export it
		if config.get('phrase') and not os.path.exists(keyfile):
			self.export_key(config.phrase, update_config=settings.LAB.update_settings)

		# check if there is an exported key, matching settings.LAB.server_digest
		try:
			with open(keyfile, 'r') as f: exported = f.read()
			key = secure.Key(exported, config.get('phrase'))
			verified = key.match_digest(key.export(), settings.LAB.server_digest)
			message = 'valid server key' if verified else 'unverified key'
			if not verified: config = {}
		except Exception as e:
			message = str(e)
		return config, key, verified, message

	def export_key(self, phrase, update_config=False):
		"""Export a key, and if needed, update server_digest in lab/settings."""
		if os.path.exists(settings.LAB.keyfile): return
		k = secure.Key()
		exported = k.export(phrase)
		with open(settings.LAB.keyfile, 'w') as f: f.write(exported)
		if update_config:
			digest = k.digest(k.export())
			self.update_config(settings.LAB.__file__, 'server_digest', digest)
			reload(settings.LAB)
		logger.info('Added new key%s.' % (' and updated config' if update_config else ''))

	def update_config(self, filename, key, value):
		"""Change a setting in a python config file."""
		filename = filename.rstrip('c')
		compiled = filename + 'c'
		pattern = r'(?<=%s = ).+(?=\s*\n)' % key
		if isinstance(value, (str, unicode)): value = "'%s'" % value
		with open(filename, 'r') as f: content = f.read()
		content = re.sub(pattern, value, content)
		with open(filename, 'w') as f: f.write(content)
		if os.path.exists(compiled): os.remove(compiled)

