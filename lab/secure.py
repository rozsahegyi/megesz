import hashlib, unittest, requests, json
from base64 import b64encode, b64decode
from Crypto import Random
from Crypto.Hash import MD5
from Crypto.PublicKey import RSA
from django.conf import settings
from network import mapping


KEY_LENGTH = 1024
KEY_EXPONENT = long(65537)

content_types = mapping({
	'json': 'application/json',
	'encrypted': 'text/encrypted',
})


class Key(object):
	"""RSA key class with extra/simplified methods."""

	def __init__(self, exported=None, phrase=None):
		if exported:
			key = RSA.importKey(exported, phrase)
		else:
			random = Random.new().read
			key = RSA.generate(KEY_LENGTH, random, e=KEY_EXPONENT)
		self.phrase = phrase
		self.private, self.public = (key, key.publickey()) if key.has_private() else (None, key)

	def export(self, phrase=None):
		if phrase is True: phrase = self.phrase or None
		key = phrase and self.private or self.public
		return key.exportKey('PEM', phrase, 1)

	def sign(self, message):
		return self.private and self.private.sign(self.hashed(message), '')

	def verify(self, message, signature):
		return self.public.verify(self.hashed(message), signature)

	def encrypt(self, text):
		return b64encode(self.public.encrypt(text, 32)[0])

	def decrypt(self, text):
		return self.private and self.private.decrypt(b64decode(text))

	def hashed(self, text):
		return MD5.new(text).digest()

	def digest(self, text):
		return hashlib.sha256(text).hexdigest()

	def match_digest(self, text, digest):
		return self.digest(text) == digest

	def __repr__(self):
		return "Key#%s" % str(self.public.key.n)[0:8]


class TestKey(unittest.TestCase):
	def setUp(self):
		self.key = Key()
		exported = self.key.export()
		self.public_key = Key(exported)
		self.message = 'some random message'

	def test_encryption(self):
		secret = self.public_key.encrypt(self.message)
		assert self.message == self.key.decrypt(secret)

	def test_signature(self):
		signature = self.key.sign(self.message)
		assert self.key.private.has_private()
		assert not self.key.public.has_private()
		assert self.public_key.verify(self.message, signature)


class Response(object):
	"""Custom response; converts content to json and optionally encrypts it."""
	cls = None

	def __new__(this, content = '', key=None, *args, **kw):
		if not this.cls: return None
		content = json.dumps(content)
		if key: content = key.encrypt(content)
		content_type = content_types.encrypted if key else content_types.json
		return this.cls(content=content, content_type=content_type, *args, **kw)


class Result(object):
	"""Loads results from an url, decrypting and json-loading it."""
	default_path = ''

	def __init__(self, content='', key=None, remote=None, params=None):
		if remote:
			remote = mapping(zip(('key', 'address', 'path'), remote + (self.__class__.default_path,)))
		self.content = content
		self.key = key
		self.remote = remote
		self.params = params
		self.response = None
		self.encrypted_content = ''
		if remote: self.content = self.load()
		if not self.content: return
		if key and (not self.response or self.response.encrypted):
			self.encrypted_content = self.content
			self.content = key.decrypt(self.content)
		try:
			self.content = json.loads(self.content)
		except ValueError:
			raise Exception(repr(self.response.__dict__))

	def load(self):
		if self.params:
			self.params = {'content': self.remote.key.encrypt(json.dumps(self.params))}
		port = ':%s' % settings.LAB.http_port if self.remote.address.find(':') < 0 else ''
		url = 'http://%s%s/%s' % (self.remote.address, port, self.remote.path)
		method = requests.post if self.params else requests.get
		self.response = method(url, params=self.params)
		self.response.encrypted = self.response.headers['content-type'] == content_types.encrypted
		return self.response.content if self.response.status_code == 200 else None

	def __str__(self):
		return self.content

