from http import HTTPStatus

from django.test import TestCase, Client


class StaticURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()

    def test_pages(self):
        url = '/about/author/'
        template = 'about/author.html'

        r = self.guest_client.get(url)

        self.assertEqual(r.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(r, template)
