from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse

from posts.models import User, Group, Post


class StaticURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.authorized_client = Client()

    def setUp(self):
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(slug='slg', title='some-group')
        self.post = Post.objects.create(text='sometext', group=self.group,
                                        author=self.user)

    def test_pages(self):

        url_list = (
            # Первый параметр это viewname, который указываем в urls.py
            reverse('posts:index'),
            # Второй параметр, словарь с именованными переменными, которые
            # тоже в urls.py можно посмотреть.
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
        )

        # Посмотри, что выведет.
        for test_url in url_list:
            print(test_url)
            # Дальше проверку делай.

        cases = (
            # url, auth_required, template_name
            ('/', False, 'posts/index.html'),
            (f'/group/{self.group.slug}/', False, 'posts/group_list.html'),
            (f'/profile/{self.user.username}/', False, 'posts/profile.html'),
            (f'/posts/{self.post.pk}/', False, 'posts/post_detail.html'),
            (f'/posts/{self.post.pk}/edit/', True, 'posts/create_post.html'),
            (f'/create/', True, 'posts/create_post.html'),
        )

        for case in cases:
            url, auth_required, template = case

            with self.subTest(url):
                r = self.guest_client.get(url)

                if auth_required:
                    self.assertEqual(r.status_code, HTTPStatus.FOUND)
                    resp = self.authorized_client.get(url)
                    self.assertEqual(resp.status_code, HTTPStatus.OK)
                    self.assertTemplateUsed(resp, template)
                else:
                    self.assertEqual(r.status_code, HTTPStatus.OK)
                    self.assertTemplateUsed(r, template)

    def test_not_found(self):
        url = '/unexist_page/'

        r = self.guest_client.get(url)

        self.assertEqual(r.status_code, HTTPStatus.NOT_FOUND)
