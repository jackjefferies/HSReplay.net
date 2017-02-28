import pytest
from uuid import uuid4
from django.core.management import call_command
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from base64 import b64encode
from hsreplaynet.cards.models import Deck, Archetype, CanonicalDeck
from hearthstone.enums import CardClass, FormatType
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def pytest_addoption(parser):
	parser.addoption(
		"--all",
		action="store_true",
		help="run slower tests not enabled by default"
	)
	parser.addoption(
		"--selenium",
		action="store_true",
		help="run selenium tests against the --host target"
	)
	parser.addoption(
		"--host",
		default="https://hsreplay.net"
	)


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
	with django_db_blocker.unblock():
		call_command("load_cards")


@pytest.mark.django_db
@pytest.yield_fixture(scope="module")
def freeze_mage_archetype():
	freeze_mage = [
		"EX1_561",
		"CS2_032",
		"EX1_295",
		"EX1_295",
		"EX1_012",
		"CS2_031",
		"CS2_031",
		"CS2_029",
		"CS2_029",
		"CS2_023",
		"CS2_023",
		"CS2_024",
		"CS2_024",
		"EX1_096",
		"EX1_096",
		"EX1_015",
		"EX1_015",
		"EX1_007",
		"EX1_007",
		"CS2_028",
		"CS2_028",
		"BRM_028",
		"NEW1_021",
		"NEW1_021",
		"CS2_026",
		"CS2_026",
		"LOE_002",
		"LOE_002",
		"EX1_289",
		"OG_082",
	]

	deck, deck_created = Deck.objects.get_or_create_from_id_list(freeze_mage)
	archetype, archetype_created = Archetype.objects.get_or_create(
		name="Freeze Mage",
		player_class=CardClass.MAGE
	)
	if archetype_created:
		CanonicalDeck.objects.create(
			archetype=archetype,
			deck=deck,
			format=FormatType.FT_STANDARD
		)
	yield archetype


@pytest.mark.django_db
@pytest.yield_fixture(scope="module")
def tempo_mage_archetype():
	tempo_mage = [
		"CS2_032",
		"KAR_076",
		"KAR_076",
		"EX1_284",
		"EX1_284",
		"CS2_029",
		"CS2_029",
		"OG_303",
		"OG_303",
		"KAR_009",
		"AT_004",
		"AT_004",
		"EX1_277",
		"EX1_277",
		"EX1_012",
		"EX1_298",
		"CS2_033",
		"CS2_033",
		"CS2_024",
		"CS2_024",
		"NEW1_012",
		"NEW1_012",
		"BRM_002",
		"BRM_002",
		"OG_207",
		"OG_207",
		"CS2_023",
		"CS2_023",
		"EX1_608",
		"EX1_608",
	]

	deck, deck_created = Deck.objects.get_or_create_from_id_list(tempo_mage)
	archetype, archetype_created = Archetype.objects.get_or_create(
		name="Tempo Mage",
		player_class=CardClass.MAGE
	)
	if archetype_created:
		CanonicalDeck.objects.create(
			archetype=archetype,
			deck=deck,
			format=FormatType.FT_STANDARD
		)
	yield archetype


@pytest.yield_fixture(scope="session")
def upload_context():
	yield None


@pytest.yield_fixture(scope="session")
def upload_event():
	yield {
		"headers": {
			"Authorization": "Token beh7141d-c437-4bfe-995e-1b3a975094b1",
		},
		"body": b64encode('{"player1_rank": 5}'.encode("utf8")).decode("ascii"),
		"source_ip": "127.0.0.1",
	}


@pytest.yield_fixture(scope="session")
def s3_create_object_event():
	yield {
		"Records": [{
			"s3": {
				"bucket": {
					"name": "hsreplaynet-raw-log-uploads",
				},
				"object": {
					"key": "raw/2016/07/20/10/37/hUHupxzE9GfBGoEE8ECQiN/power.log",
				}
			}
		}]
	}


@pytest.yield_fixture(scope="session")
def full_url():
	HOST = pytest.config.getoption("--host")

	def resolver(page_name):
		return HOST + reverse(page_name)

	yield resolver


@pytest.mark.django_db
@pytest.yield_fixture(scope="session")
def browser(full_url, django_db_blocker):
	with django_db_blocker.unblock():
		user = None
		try:
			_username = "locust_user_%s" % str(uuid4())
			_password = _username
			user = get_user_model().objects.create(username=_username)
			user.set_password(_password)
			user.is_staff = True
			user.groups.add(Group.objects.get(name="feature:billing:preview"))
			user.groups.add(Group.objects.get(name="feature:carddb:preview"))
			user.groups.add(Group.objects.get(name="feature:topcards:preview"))
			user.save()  # Save needed to record password

			browser = webdriver.Chrome('/usr/local/bin/chromedriver')
			browser.implicitly_wait(3)

			def wait_until(locator):
				return WebDriverWait(browser, 10).until(
					EC.presence_of_element_located(locator)
				)
			browser.wait_until = wait_until

			browser.get(full_url("admin:login"))
			username = browser.find_element_by_id("id_username")
			password = browser.find_element_by_id("id_password")
			username.clear()
			password.clear()
			username.send_keys(_username)
			password.send_keys(_password)
			password.submit()

			yield browser

			browser.quit()
		finally:
			user.delete()
