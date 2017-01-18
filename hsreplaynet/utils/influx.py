"""Utils for interacting with Influx"""
import resource
import time
from contextlib import contextmanager
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.timezone import now
from . import log


_influx_clients = {}


def create_influx_client(dbdict):
	from influxdb import InfluxDBClient

	kwargs = {
		"host": dbdict["HOST"],
		"port": dbdict.get("PORT", 8086),
		"username": dbdict["USER"],
		"password": dbdict["PASSWORD"],
		"database": dbdict["NAME"],
		"ssl": dbdict.get("SSL", False),
		"timeout": dbdict.get("TIMEOUT", 2)
	}

	udp_port = dbdict.get("UDP_PORT", 0)
	if udp_port:
		kwargs["use_udp"] = True
		kwargs["udp_port"] = udp_port

	return InfluxDBClient(**kwargs)


def get_influx_client(name):
	if name not in _influx_clients:
		dbs = getattr(settings, "INFLUX_DATABASES", None)
		if not dbs or name not in dbs:
			raise ImproperlyConfigured("INFLUX_DATABASES[%r] setting is not set" % (name))
		_influx_clients[name] = create_influx_client(dbs[name])

	return _influx_clients[name]


if settings.INFLUX_ENABLED:
	influx = get_influx_client("hsreplaynet")
else:
	influx = None


def influx_write_payload(payload, client=influx):
	if client is None:
		return

	try:
		result = client.write_points(payload)
		if not result:
			log.warn("Influx write failure")
	except Exception as e:
		log.exception("Exception while writing to influx.")
		result = None


def influx_metric(measure, fields, timestamp=None, **kwargs):
	if timestamp is None:
		timestamp = now()

	payload = {
		"measurement": measure,
		"tags": kwargs,
		"fields": fields,
		"time": timestamp.isoformat()
	}
	influx_write_payload([payload])


@contextmanager
def influx_timer(measure, timestamp=None, cloudwatch_url=None, **kwargs):
	"""
	Reports the duration of the context manager.
	Additional kwargs are passed to InfluxDB as tags.
	"""
	start_time = time.clock()
	exception_raised = False
	if timestamp is None:
		timestamp = now()
	try:
		yield
	except Exception:
		exception_raised = True
		raise
	finally:
		stop_time = time.clock()
		duration = (stop_time - start_time) * 10000
		mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

		tags = kwargs
		tags["exception_thrown"] = exception_raised
		payload = {
			"fields": {
				"value": duration,
				"mem": mem,
			},
			"measurement": measure,
			"tags": tags,
			"time": timestamp.isoformat(),
		}

		if exception_raised and cloudwatch_url:
			payload["fields"]["cloudwatch"] = cloudwatch_url
		influx_write_payload([payload])


def get_avg_upload_processing_seconds():
	ms = get_current_lambda_average_duration_millis("process_replay_upload_stream_handler")
	return round(ms / 1000.0, 1)


def get_current_lambda_average_duration_millis(lambda_name, lookback_hours=1):
	metric_name = "%s_duration_ms" % (lambda_name)
	raw_query = """
		select mean(value) from %s
		where exception_thrown = 'False'
		and time > now() - %sh
	"""
	full_query = raw_query % (metric_name, lookback_hours)
	result = influx.query(full_query).raw
	return round(result["series"][0]["values"][0][1])


def get_redshift_query_average_duration_seconds(query_name, lookback_hours=1):
	try:
		raw_query = """
			select mean(value) from redshift_query_duration
			where exception_thrown = 'False'
			and query = '%s'
			and time > now() - %sh
		"""
		full_query = raw_query % (query_name, lookback_hours)

		result = influx.query(full_query).raw
		if "series" in result:
			return round(result["series"][0]["values"][0][1], 2)
		else:
			# This could fail if the series doesn't exist yet, e.g. the first time the query is run
			return None
	except:
		# Don't let Influx being down ever bring down analytics serving
		return None
