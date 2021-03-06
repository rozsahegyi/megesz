# provides mixins for basic udp and network functions

import socket, threading, json
from django.conf import settings
from . import logging


logger = logging.getLogger(__name__)


class mapping(dict):
	"""Dict with attribute access. Accepts dict-like objects or tuple list."""
	def __init__(self, content=None, *args, **kw):
		content = content.items() if hasattr(content, 'items') else content or []
		if content:
			content = ((k, mapping(v) if isinstance(v, dict) else v) for k, v in content if k and k[0] != '_')
		super(mapping, self).__init__(content, *args, **kw)
		self.__dict__ = self
	def __getattr__(self, key):
		return None


class SimpleUdp(object):
	"""Basic udp mixin with listen/broadcast/receive functions."""

	ip = None
	bufsize = 65536

	@property
	def udp_port(self):
		return getattr(settings.LAB, 'local', None) and int(settings.LAB.address.get('port')) or settings.LAB.http_port

	def broadcast_udp(self, data, target=None):
		"""Broadcast json data or send it to a specific target."""

		data = json.dumps(data)

		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		if target:
			target = target.split(':') + [self.udp_port]
			target, port = target[0], int(target[1])
		else:
			target, port = '<broadcast>', self.udp_port
			s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

		# if nodes run on the same host, send to localhost
		if getattr(settings.LAB, 'local', None):
			logger.debug('sending udp to localhost:%s+%s', settings.LAB.http_port, settings.LAB.local)
			for i in range(settings.LAB.local + 1):
				s.sendto(data, ('', settings.LAB.http_port + i))
		else:
			logger.debug('sending udp to %s:%s', target, port)
			s.sendto(data.encode('utf8'), (target, port))
		s.close()

	def listen_udp(self):
		"""Runs a thread, listening and calling received_udp() repeatedly."""
		def listen():
			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			logger.info('listening on %s', self.udp_port)
			s.bind(('', self.udp_port))
			try:
				while 1: self.received_udp(*s.recvfrom(self.bufsize))
			finally:
				s.close()
		threading.Thread(target=listen).start()

	def received_udp(self, data, addr):
		"""Expects at most bufsize data in json, passing it to handle_udp()."""
		try:
			data = mapping(json.loads(data))
		except ValueError as e:
			logger.error('received_udp() unable to parse data from %s: %r', addr, data, exc_info=True)
		if (hasattr(self, 'ips') and data.ip in self.ips) or \
			data.ip.rsplit('.', 1)[0] in settings.LAB.ignore_subnets:
			return
		if hasattr(self, 'ip') and data.ip == self.ip: return
		logger.debug('received from %s: %s', data.ip, data)
		self.handle_udp(data)

	def handle_udp(self, data):
		pass


class Node(object):
	"""Network node mixin. Provides the key and ips attributes."""

	key = None
	_ips = None

	def __new__(cls, config=None, key=None):
		ob = super(Node, cls).__new__(cls)
		if not config: config = {}
		if key: config['key'] = key
		ob.__dict__.update(config)
		return ob

	@property
	def ips(self):
		"""Provide a filtered ip list, selecting/ignoring some (see settings)."""
		if self._ips is None:
			subnet = lambda ip: ip.rsplit('.', 1)[0]
			preferred = lambda ip: subnet(ip) == settings.LAB.prefer_subnet
			available = lambda ip: subnet(ip) not in settings.LAB.ignore_subnets
			try:
				import netifaces
				info = (netifaces.ifaddresses(x) for x in netifaces.interfaces())
				ips = [x[netifaces.AF_INET][0]['addr'] for x in info if x.get(netifaces.AF_INET)]
				logger.debug('netifaces ips: %r', ips)
			except ImportError:
				# fallback to a simple ip list of the hostname
				ips = socket.gethostbyname_ex(socket.gethostname())[2]
				logger.debug('fallback ips: %r', ips)
			self._ips = list(filter(preferred, ips)) or sorted(filter(available, ips))
		return self._ips

