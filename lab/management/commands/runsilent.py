# Silent runserver command with related classes adjusted
#
# currently silences some messages, logs uncompleted ajax request errors,
# and provides a general way for further customizations
# based on: https://djangosnippets.org/snippets/2050/
#
# modules of involved classes:
# wsgiref.simple_server, wsgiref.handlers, BaseHTTPServer, SocketServer, django.core.servers.basehttp
#
# errors:
#	10053: An established connection was aborted by the software in your host machine
#	when reloading a page while an ajax request is pending - catch and ignore

import sys
from django.conf import settings
from django.core.servers import basehttp
from django.core.management.commands import runserver
from django.utils.six.moves import socketserver

from lab import logging
logger = logging.getLogger('lab.ma.co.runsilent')
logger.setLevel(logging.INFO)

silent_urls = [
	settings.MEDIA_URL,
	settings.STATIC_URL,
	'/lab/updates',
	'/lab/status',
	'/lab/direct/',
]


# use the runserver command in core or staticfiles
BaseCommand = runserver.Command
if 'django.contrib.staticfiles' in settings.INSTALLED_APPS:
	from django.contrib.staticfiles.management.commands.runserver import Command as BaseCommand


class ServerHandler(basehttp.ServerHandler):
	def finish_response(self):
		try:
			# basehttp.ServerHandler.finish_response(self)
			super(ServerHandler, self).finish_response()
		except Exception as e:
			if hasattr(e, 'errno') and e.errno == 10053: return logger.debug(str(e))
			logger.error(str(e), exc_info=True)


class WSGIServer(basehttp.WSGIServer):
	def handle_error(self, *args, **kw):
		cls, e, trace = sys.exc_info()
		if hasattr(e, 'errno') and e.errno == 10053: return logger.debug(str(e))
		try:
			super(WSGIServer, self).handle_error(*args, **kw)
		except Exception as e:
			logger.error(str(e), exc_info=True)


class QuietWSGIRequestHandler(basehttp.WSGIRequestHandler):
	def log_message(self, format, *args):
		if [x for x in silent_urls if x and self.path.startswith(x)]: return
		return basehttp.WSGIRequestHandler.log_message(self, format, *args)

	# taken from parent, to use the customized ServerHandler
	def handle(self):
		"""Handle a single HTTP request"""

		self.raw_requestline = self.rfile.readline()
		if not self.parse_request(): # An error code has been sent, just exit
			return

		handler = ServerHandler(
			self.rfile, self.wfile, self.get_stderr(), self.get_environ()
		)
		handler.request_handler = self # backpointer for logging
		handler.run(self.server.get_app())


# taken from basehttp
def run(addr, port, wsgi_handler, ipv6=False, threading=False, *args, **options):
	server_address = (addr, port)
	if threading:
		httpd_cls = type(str('WSGIServer'), (socketserver.ThreadingMixIn, WSGIServer), {})
	else:
		httpd_cls = WSGIServer
	httpd = httpd_cls(server_address, QuietWSGIRequestHandler, ipv6=ipv6)
	httpd.set_app(wsgi_handler)
	httpd.serve_forever()


class Command(BaseCommand):
	def run(self, *args, **options):
		# save address (needed when running several nodes on one machine)
		logger.debug('server started: %s %s', self.addr, self.port)
		settings.LAB.address['addr'] = self.addr
		settings.LAB.address['port'] = self.port
		return super(Command, self).run(*args, **options)

	def handle(self, *args, **options):
		# runserver uses django.core.servers.basehttp.run as global
		runserver.run = run
		return super(Command, self).handle(*args, **options)

