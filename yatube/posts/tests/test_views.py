# Здесь импорт необходимых библиотек для тестов.
import tempfile
from http import HTTPStatus

from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from posts.models import User, Group, Post, Follow


class PostIndexViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.authorized_client = Client()

    def setUp(self) -> None:
        for x in range(13):
            Post.objects.create(text=f'text_{x}', author=self.user)

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        response = self.client.get(reverse('posts:index'), data={'page': 2})
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_cache(self):
        text = 'abracadabrabra'
        Post.objects.create(text=text, author=self.user)
        # Делаем запрос, чтобы закэшировать html.
        self.client.get(reverse('posts:index'))
        # Удаляем посты, но они должны остаться в кэше.
        Post.objects.all().delete()

        response = self.client.get(reverse('posts:index'))

        self.assertIn(text, str(response.content))


class PostViewsTestCase(TestCase):

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

    def test_post_create_success(self):
        """Прил. Posts: Шаблон post_create сформирован с правильным конт-ом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Прил. Posts: Шаблон post_edit сформирован с правильным конт-ом."""

        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        )

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


class CreatePostViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.authorized_client = Client()
        cls.url = reverse('posts:post_create')
        # Создаем временную директорию.
        cls.tmp_media_root = tempfile.mkdtemp(suffix='test_media')

    def setUp(self) -> None:
        super().setUp()
        self.authorized_client.force_login(user=self.user)
        self.group = Group.objects.create(title='gr', slug='grslug')

    def test_get_unauth(self):
        r = self.guest_client.get(self.url)
        self.assertEqual(r.status_code, HTTPStatus.FOUND)

    def test_get_success(self):
        cases = (
            ('text', forms.CharField, 'Текст'),
            ('group', forms.ModelChoiceField, 'Группа'),
        )

        r = self.authorized_client.get(self.url)

        self.assertEqual(r.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(r, 'posts/create_post.html')
        for case in cases:
            field_name, field_type, label = case
            field = r.context.get('form').fields.get(field_name)
            self.assertIsInstance(field, field_type)
            self.assertEqual(field.label, label)

    def test_post_success(self):
        """Тест создания поста с картинкой."""
        text = 'bada'
        # Данные картинки, байт-код.
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        # Спец. django-штука, чтобы создавать файлы для тестов, проще.
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        # Менедежер контекста. Все, что внутри блока with, подчиняется
        # правилам менедежера. Т.е. внутри него место для хранения
        # медиафайлов будет не settings.MEDIA_ROOT, а self.tmp_media_root.
        with override_settings(MEDIA_ROOT=self.tmp_media_root):
            r = self.authorized_client.post(
                self.url,
                data={
                    'text': text,
                    'group': self.group.pk,
                    'image': uploaded
                }
            )

        self.assertEqual(r.status_code, HTTPStatus.FOUND)
        self.assertEqual(1, Post.objects.count())
        post = Post.objects.last()
        self.assertEqual(post.text, text)
        self.assertEqual(post.group, self.group)
        # Сравниваем картинки.
        self.assertEqual(str(post.image), 'posts/small.gif')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Удаляем временную директорию, для порядка, так сказать.
        tempfile._rmtree(cls.tmp_media_root)


class EditPostViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.authorized_client = Client()

    def setUp(self) -> None:
        super().setUp()
        self.authorized_client.force_login(user=self.user)
        self.post = Post.objects.create(text='badabada', author=self.user)
        self.url = reverse('posts:post_edit', kwargs={'post_id': self.post.pk})

    def test_get_success(self):
        r = self.authorized_client.get(self.url)

        self.assertEqual(r.status_code, HTTPStatus.OK)

        self.assertIsInstance(
            r.context.get('form').fields.get('text'),
            forms.CharField
        )
        self.assertIsInstance(
            r.context.get('form').fields.get('group'),
            forms.ModelChoiceField
        )
        self.assertEqual(r.context.get('form').instance, self.post)

    def test_post_success(self):
        text = 'newtext'
        group = Group.objects.create(title='title group', slug='gr')

        r = self.authorized_client.post(
            self.url,
            data={'text': text, 'group': group.pk}
        )

        self.assertEqual(r.status_code, HTTPStatus.FOUND)
        self.assertTrue(Post.objects.filter(text=text, group=group).exists())

    def test_post_error(self):
        pass


class PostDetailViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.authorized_client = Client()

    def setUp(self) -> None:
        super().setUp()
        self.authorized_client.force_login(user=self.user)
        self.post = Post.objects.create(text='badabada', author=self.user)
        self.url = reverse('posts:post_detail', kwargs={'post_id': self.post.pk})

    def test_get_success(self):
        r = self.authorized_client.get(self.url)

        self.assertEqual(r.status_code, HTTPStatus.OK)

        exp_post = r.context.get('post')
        self.assertEqual(exp_post, self.post)


class FollowViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.author = User.objects.create_user(username='author')

        cls.guest_client = Client()
        cls.authorized_client = Client()

    def setUp(self) -> None:
        super().setUp()
        self.authorized_client.force_login(user=self.user)
        self.post = Post.objects.create(text='badabada', author=self.author)
        self.url = reverse('posts:profile_follow',
                           kwargs={'username': self.author.username})

    def test_get_success(self):
        print(self.url)

        r = self.authorized_client.get(self.url)

        self.assertEqual(r.status_code, HTTPStatus.FOUND)
        self.assertEqual(Follow.objects.count(), 1)
