
(function(window) {

if (!String.prototype.format)
	String.prototype.format = function() {
		var args = arguments,
			replacer = function(match, number) {
				return typeof args[number] != 'undefined' ? args[number] : match;
			};
		return this.replace(/{(\d+)}/g, replacer);
	};

function Lab() {
	var lab = this;

	this.init = function() {
		this.poll_id = window.location.hash.slice(1);
		if (!this.disable_polling) this.poll();
	}

	this.log = function(res) { console.log('logged:', res); }

	this.poll = function(res) {
		// console.log('polling for messages...');
		if (res) this.add_messages(res);
		this.ajax.get("/lab/updates/" + this.poll_id, null, null, 'poll');
	}

	this.add_messages = function(res) {
		var message = "<div><b class='{0}'>{0}</b><i>&#187; {2} &#187;</i><b class='{1}'>{1}</b>{3}</div>";
		$('.history').empty();
		$(res).each(function(i, a) {
			setTimeout(function() {
				$('.history').append(message.format.apply(message, a));
			}, i * 150);
		});
	}

	this.complete = function(res, status, url, callback) {
		var result = res.responseJSON || {};
		console.log(window.location.href, 'ajax', url, status, result);
		if (result.method || callback) this[result.method || callback](result.content);
	}

	this.ajax = function(method, url, data, settings, callback) {
		if (!settings) settings = {};
		settings.method = method.toUpperCase();
		settings.data = data;
		settings.complete = function() { lab.complete.call(lab, arguments[0], arguments[1], url, callback); };
		return $.ajax(url, settings) || null;
	}
	this.ajax.get = function() { return this.apply(this, $.merge(['get'], arguments)); }
	this.ajax.post = function() { return this.apply(this, $.merge(['post'], arguments)); }

	this.serialize = function(list) {
		if (!list || !list.each) return [];
		var result = {},
			collect = function(index, elem) {
				var key = elem.name;
				if (result[key] == undefined) result[key] = elem.value;
				else if (result[key].push) result[key].push(elem.value);
				else result[key] = [result[key], elem.value];
			};
		list.each(collect);
		return result;
	}

	this.submit = function(url, data, event, method) {
		if (event) event.preventDefault();
		if (!url) return;
		if (!method) method = 'get';
		switch (data && data.tagName) {
			case "FORM": data = this.serialize($.serializeArray(data)); break;
			case "INPUT": var temp = {}; temp[data.name] = data.value; data = temp; break;
			default: break;
		}
		return this.ajax(method, url, data);
	}

	var init = function() { lab.init.apply(lab); };
	if (window.lab) window.setTimeout(init, 200);
	else window.document && window.document.addEventListener('DOMContentLoaded', init);

	return this;
}

return window.lab = new Lab();

})(window);
