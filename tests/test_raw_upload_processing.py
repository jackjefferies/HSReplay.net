import json
import os
from io import BytesIO

import pytest
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from moto import mock_dynamodb2, mock_s3
from storages.backends.s3boto3 import S3Boto3Storage

from hearthsim.identity.accounts.models import AuthToken
from hearthsim.identity.api.models import APIKey
from hsreplaynet.games.models.dynamodb import GameReplay as DynamoDBGameReplay
from hsreplaynet.lambdas.uploads import process_raw_upload
from hsreplaynet.uploads.models import UploadEvent, UploadEventStatus, _generate_upload_key

from .conftest import LOG_DATA_DIR, UPLOAD_SUITE


@pytest.fixture
def game_replay_dynamodb_table(mocker):
	mocker.patch.multiple(
		"hsreplaynet.games.models.dynamodb.GameReplay.Meta",
		host=None,
		aws_access_key_id="test",
		aws_secret_access_key="test",
	)
	with mock_dynamodb2():
		DynamoDBGameReplay.create_table(wait=True)
		yield
		DynamoDBGameReplay.delete_table()


@pytest.fixture(scope="module")
def multi_db():
	from django.test import TestCase
	TestCase.multi_db = True
	yield
	TestCase.multi_db = False


class MockRawUpload(object):
	def __init__(self, path, storage=None):
		from datetime import datetime

		self._descriptor_path = os.path.join(path, "descriptor.json")
		with open(self._descriptor_path, "r") as f:
			self.descriptor_json = f.read()
		self._descriptor = json.loads(self.descriptor_json)

		self._powerlog_path = os.path.join(path, "power.log")
		with open(self._powerlog_path, "rb") as f:
			self._log = f.read()

		api_key_str = self._descriptor["event"]["headers"]["X-Api-Key"]
		self._api_key = APIKey.objects.get_or_create(api_key=api_key_str, defaults={
			"full_name": "Test Client",
			"email": "test@example.org",
			"website": "https://example.org",
		})[0]

		auth_token_str = self._descriptor["event"]["headers"]["Authorization"].split()[1]
		self._auth_token = AuthToken.objects.get_or_create(
			key=auth_token_str,
			creation_apikey=self._api_key
		)[0]
		self._auth_token.create_fake_user(save=True)
		self._api_key.tokens.add(self._auth_token)

		timestamp_str = self._descriptor["upload_metadata"]["match_start"][0:16]
		self._timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M")

		self._shortid = self._descriptor["shortid"]

		if storage:
			key = _generate_upload_key(self._timestamp, self._shortid)
			storage.save(key, BytesIO(self._log))

		self._reason = None
		self._delete_was_called = False

	@property
	def log(self):
		return self._log

	@property
	def descriptor(self):
		return self._descriptor

	@property
	def api_key(self):
		return self._api_key

	@property
	def auth_token(self):
		return self._auth_token

	@property
	def shortid(self):
		return self._shortid

	@property
	def timestamp(self):
		return self._timestamp

	def player(self, number):
		key = "player%s" % number
		if key in self.descriptor:
			return self.descriptor[key]

		return None

	# Stubs to abstract S3 interactions
	@property
	def bucket(self):
		return "BUCKET"

	@property
	def log_key(self):
		return "LOG_KEY"

	@property
	def upload_http_method(self):
		return "put"

	def prepare_upload_event_log_location(self, bucket, key, descriptor=None):
		pass

	def make_failed(self, reason):
		self._reason = reason

	def delete(self):
		self._delete_was_called = True


@pytest.mark.django_db
@pytest.mark.usefixtures("multi_db")
def test_upload_regression_suite(db):
	for shortid in os.listdir(UPLOAD_SUITE):
		raw_upload = MockRawUpload(os.path.join(UPLOAD_SUITE, shortid), default_storage)

		# Run first as a create
		do_process_raw_upload(raw_upload, is_reprocessing=False)

		# Then run as a reprocess
		do_process_raw_upload(raw_upload, is_reprocessing=True)


def do_process_raw_upload(raw_upload, is_reprocessing):
	process_raw_upload(raw_upload, is_reprocessing)

	# Begin asserting correctness
	created_upload_event = UploadEvent.objects.get(shortid=raw_upload.shortid)
	assert str(created_upload_event.token_uuid) == str(raw_upload.auth_token.key)
	source_ip = raw_upload.descriptor["event"]["requestContext"]["identity"]["sourceIp"]
	assert created_upload_event.upload_ip == source_ip

	replay = created_upload_event.game
	assert replay.opponent_revealed_deck is not None
	assert replay.opponent_revealed_deck.size > 0
	validate_fuzzy_date_match(raw_upload.timestamp, replay.global_game.match_start)
	validate_player_data(raw_upload, replay, 1)
	validate_player_data(raw_upload, replay, 2)

	for player_id in (1, 2):
		for card in replay.global_game.players.get(player_id=player_id).deck_list:
			assert card.collectible


@mock_s3
@pytest.mark.django_db
@pytest.mark.usefixtures("multi_db")
def test_process_raw_upload_corrupt(mocker):
	moto_s3_storage = S3Boto3Storage(
		access_key="test",
		auto_create_bucket=True,
		bucket="hsreplaynet-replays",
		gzip_content_types=(),
		secret_key="test"
	)

	mocker.patch("django.core.files.storage.default_storage._wrapped", moto_s3_storage)
	mocker.patch(
		"storages.backends.s3boto3.mimetypes.guess_type",
		lambda name: (None, "gzip")
	)

	raw_upload = MockRawUpload(os.path.join(
		LOG_DATA_DIR,
		"hsreplaynet-tests",
		"uploads-invalid",
		"gzip-corrupt"
	), moto_s3_storage)

	with pytest.raises(ValidationError):
		process_raw_upload(raw_upload, False)

	upload_event = UploadEvent.objects.get(shortid=raw_upload.shortid)

	assert upload_event.status == UploadEventStatus.VALIDATION_ERROR
	assert upload_event.error is not None


@mock_s3
@pytest.mark.django_db
@pytest.mark.usefixtures("multi_db")
def test_process_raw_upload_timeout(mocker):
	moto_s3_storage = S3Boto3Storage(
		access_key="test",
		auto_create_bucket=True,
		bucket="hsreplaynet-replays",
		secret_key="test"
	)

	mocker.patch("django.core.files.storage.default_storage._wrapped", moto_s3_storage)

	raw_upload = MockRawUpload(os.path.join(
		LOG_DATA_DIR,
		"hsreplaynet-tests",
		"uploads",
		"2hwp7nDJMyWvrHQGBYTvVM"
	), moto_s3_storage)

	from botocore.vendored.requests.packages.urllib3.exceptions import ReadTimeoutError

	mocker.patch.object(S3Boto3Storage, "open")
	S3Boto3Storage.open.side_effect = ReadTimeoutError(None, None, "Read timed out.")

	with pytest.raises(ValidationError):
		process_raw_upload(raw_upload, False)

	upload_event = UploadEvent.objects.get(shortid=raw_upload.shortid)

	assert upload_event.status == UploadEventStatus.VALIDATION_ERROR
	assert upload_event.error is not None
	assert S3Boto3Storage.open.call_count == 2


def validate_fuzzy_date_match(upload_date, replay_date):
	assert upload_date.year == replay_date.year
	assert upload_date.month == replay_date.month
	assert upload_date.day == replay_date.day


def validate_player_data(raw_upload, replay, number):
	upload_player = raw_upload.player(number)
	if upload_player:
		replay_player = replay.player(number)
		if "rank" in upload_player:
			assert upload_player["rank"] == replay_player.rank

		if "deck" in upload_player:
			assert replay_player.deck_list is not None
			assert len(upload_player["deck"]) == replay_player.deck_list.size()


def test_validate_upload_date():
	"""
	Verifies the upload date / match start validation algorithm.
	The match start is never supposed to be any later than the upload date, so
	if it is, the match start is set to the upload date -- but the timezone
	remains untouched.
	"""

	from aniso8601 import parse_datetime
	from hsreplaynet.games.processing import get_valid_match_start

	values = ((
		# MS greater than UD, same timezone, expecting UD
		"2016-01-01T10:00:00Z",  # Match start
		"2016-01-01T01:01:01Z",  # Upload date
		"2016-01-01T01:01:01Z",  # Expected result
	), (
		# MS lesser than UD, expecting MS
		"2016-01-01T10:00:00+0200",
		"2016-01-01T10:00:00+0100",
		"2016-01-01T10:00:00+0200"
	), (
		# MS greater than UD, different timezone, expecting modified UD
		"2016-01-01T10:00:00+0300",
		"2016-01-01T10:00:00+0400",
		"2016-01-01T09:00:00+0300"
	), (
		# MS greater than UD, different timezone, expecting modified UD
		"2018-01-01T10:00:00-0500",
		"2016-01-01T10:00:00+0500",
		"2016-01-01T00:00:00-0500"
	))

	for match_start, upload_date, expected in values:
		match_start = parse_datetime(match_start)
		upload_date = parse_datetime(upload_date)
		expected = parse_datetime(expected)

		ret = get_valid_match_start(match_start, upload_date)
		# assert expected.tzinfo == match_start.tzinfo
		assert ret.tzinfo == match_start.tzinfo
		assert ret == expected


@pytest.mark.django_db
@pytest.mark.usefixtures("multi_db", "game_replay_dynamodb_table")
def test_process_raw_upload_to_dynamodb(mocker, settings):
	mocker.patch("hsreplaynet.games.processing.update_player_class_distribution")
	mocker.patch("hsreplaynet.games.processing.update_replay_feed")
	mocker.patch("hsreplaynet.games.processing.update_game_counter")
	settings.LOAD_REPLAYS_INTO_DYNAMODB = True
	settings.FULL_DECK_PREDICTION_ENABLED = False
	settings.REDSHIFT_LOADING_ENABLED = False

	raw_upload = MockRawUpload(os.path.join(
		LOG_DATA_DIR,
		"hsreplaynet-tests",
		"uploads",
		"u4HUJnBGVpytdFVWgNumfU"
	), default_storage)

	process_raw_upload(raw_upload)

	user = raw_upload.auth_token.user
	user_id = int(user.id)
	rows = DynamoDBGameReplay.query(user_id)
	replay = rows.next()

	assert replay.user_id == user_id
	assert replay.match_start == 1534252613613
	assert replay.short_id == raw_upload.shortid

	assert replay.game_type_match_start == "2:1534252613613"

	assert replay.ladder_season == 58
	assert replay.brawl_season is None
	assert replay.scenario_id == 2
	assert replay.num_turns == 33

	assert replay.opponent_predicted_deck is None
