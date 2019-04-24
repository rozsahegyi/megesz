from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from . import logging, secure, app


logger = logging.getLogger(__name__)


secure.Response.cls = HttpResponse
secure.Result.default_path = 'lab/safe_request'


def direct(req, path=None):
	"""Direct access for resources (mostly for js testing)."""
	if not path: return HttpResponse('')
	ext = path.rsplit('.', 1)[1]
	if ext == 'js': ext = 'javascript'
	try:
		with open('lab/%s' % path, 'r') as f: content = f.read()
	except Exception as e:
		content = "/* Could not find %s: %r */" % (path, e.args)
	return HttpResponse(content, content_type='text/%s' % ext)


def status(req):
	"""Status of this node in json format."""
	res = {'status': 'up', 'key': str(req.node.key)}
	if req.node.is_server: res['clients'] = len(req.node.clients)
	return secure.Response(res)

def nodes(req):
	"""If a server, shows all active nodes on one page."""
	if not req.node.is_server: return home(req)
	frames = (req.node.ip,) + tuple(sorted(req.node.clients))
	# if a docker host is set, use that host:(http_port + 1, 2...) in iframes
	docker = getattr(settings.LAB, 'docker', None)
	if docker and docker.get('host'):
		frames = ('%s:%s' % (docker['host'], settings.LAB.http_port + i) for i, ip in enumerate(frames))
	data = {'frames': ['http://%s' % ip for ip in frames]}
	return render(req, 'lab/nodes.html', data)

def home(req):
	"""Start page with messages boxes, showing details about this node."""

	# if server, show all nodes in iframes (including the server)
	if req.node.is_server and not req.META.get('HTTP_REFERER'):
		return nodes(req)

	info = dict(req.node.__dict__)
	info = ['%s: %s' % (k, info[k]) for k in sorted(info.keys())]
	data = {
		'type': req.node.__class__.__name__.lower(),
		'ip': req.node.ip,
		'key': req.node.key,
		'status': '\n'.join(info),
		'clients': [],
		'content': '',
	}
	if req.node.is_server:
		data['clients'] = sorted((app.Client.str(k), k, v) for k, v in req.node.clients.items())
	elif req.node.server.ip:
		# also display the server status
		result = secure.Result(remote=(req.node.server.key, req.node.server.ip, 'lab/status'))
		data['server_id'] = app.Server.str(req.node.server.ip)
		data['server_status'] = result.content['status']
		# server_response = sorted('%s: %s' % (k, v) for k, v in result.response.__dict__.items())
		server_response = ['%s: %s' % (x, getattr(result.response, x)) for x in 'url status_code content'.split()]
		data['status'] += '\n\n-- server status --\n' + '\n'.join(server_response)

	return render(req, 'lab/home.html', data)

def send(req, *args, **kw):
	"""
	Send an encoded message to another node, then decode the results.

	Content should be json and is encrypted with the remote node's key.
	Results are expected to be json, encrypted with this node's key.
	"""
	# TODO: restrict this to login, or localhost->localhost requests
	# if req.META['REMOTE_ADDR'] != 'localhost'

	# get the message, the remote node's public key, ip, and role
	logger.debug('send: %r %r', req.GET, req.GET.items())
	ip, message = list(req.GET.items())[0] if req.node.is_server else (req.node.server.ip, req.GET['message'])
	role = ('client', 'server')[not req.node.is_server]
	remote = (req.node.remote_key(ip), ip, role)

	if not remote[0]: return secure.Response('Remote node not found!')

	# send the request, and decode results with this node's key
	params = {'from': req.node.ip, 'message': message}
	result = secure.Result(key=req.node.key, remote=remote[0:2], params=params)
	logger.debug('result dict: %r', result.__dict__)

	# add messages showing the order of requests
	remote = app.Client.str(remote[1], name=remote[2])
	shorten = lambda x: '%s... (%d chars)' % (x[0:32], len(x))

	req.node.add_messages([
		('browser', None, 'ajax request - json', message),
		(None, remote, 'http post - encoded', shorten(result.params['content'])),
		(remote, None, 'http result - encoded', shorten(result.encrypted_content)),
		(None, 'browser', 'ajax response - json', result.content['message']),
	])

	content = {}#{'method': 'log', 'content': req.META['REMOTE_ADDR']}
	return secure.Response(content)

@csrf_exempt
def safe_request(req):
	"""
	Expects an encoded post request with the 'content' parameter.

	Content should be a json string encrypted with this node's public key.
	Response should be json, encrypted with the remote node's key.
	"""

	# decode the content with our key
	content = req.GET.get('content', '')
	logger.debug('request content: GET = %r, POST = %r', req.GET, req.POST)
	result = secure.Result(content, key=req.node.key)
	logger.debug('result object: %r', result.__dict__)
	ip, message = result.content.get('from', req.META['REMOTE_ADDR']), result.content['message']

	# add messages showing the request and result
	remote = app.Client.str(ip, name='client' if req.node.is_server else 'server')
	response = {'message': 'received: "%s"' % message}
	req.node.add_messages([
		(remote, None, 'http post - encoded', message),
		(None, remote, 'http result - encoded', response['message']),
	])

	# return an encoded response
	return secure.Response(response, key=req.node.remote_key(ip))

def updates(req, id=None):
	"""For ajax polling - sends back any new messages."""
	# wait for the updates event (with a timeout), then check for new messages
	index = len(req.node.messages)
	req.node.updates.wait(300.0)
	new_messages = index < len(req.node.messages)
	data = {
		'method': 'poll',
		'content': new_messages and req.node.messages[index:],
	}
	return secure.Response(data)

