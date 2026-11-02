"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_get_account(self):
        """Read returns the stored account and missing IDs return 404."""
        account = self._create_accounts(1)[0]
        response = self.client.get(f"{BASE_URL}/{account.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, account.serialize())
        self.assertEqual(self.client.get(f"{BASE_URL}/999999").status_code, 404)

    def test_list_accounts(self):
        """Listing returns an empty array or all persisted accounts."""
        self.assertEqual(self.client.get(BASE_URL).json, [])
        self._create_accounts(3)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 3)

    def test_update_account(self):
        """PUT persists changes without replacing the resource identity."""
        account = self._create_accounts(1)[0]
        payload = account.serialize()
        payload.update(name="Updated customer", email="updated@example.com", id=99999)
        response = self.client.put(f"{BASE_URL}/{account.id}", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["id"], account.id)
        self.assertEqual(self.client.get(f"{BASE_URL}/{account.id}").json["name"], "Updated customer")

    def test_update_errors(self):
        """PUT rejects missing resources, invalid bodies and wrong media."""
        account = self._create_accounts(1)[0]
        endpoint = f"{BASE_URL}/{account.id}"
        self.assertEqual(self.client.put(f"{BASE_URL}/999999", json=account.serialize()).status_code, 404)
        self.assertEqual(self.client.put(endpoint, json={"name": "Incomplete"}).status_code, 400)
        self.assertEqual(self.client.put(endpoint, data="invalid", content_type="text/plain").status_code, 415)

    def test_delete_account(self):
        """DELETE removes an account and is idempotent."""
        account = self._create_accounts(1)[0]
        endpoint = f"{BASE_URL}/{account.id}"
        self.assertEqual(self.client.delete(endpoint).status_code, 204)
        self.assertEqual(self.client.get(endpoint).status_code, 404)
        self.assertEqual(self.client.delete(endpoint).status_code, 204)
        self.assertEqual(self.client.get(BASE_URL).json, [])
