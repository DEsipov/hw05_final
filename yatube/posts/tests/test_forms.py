import shutil
import tempfile
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.conf import settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_author = User.objects.create_user(
            username='post_author',
        )
        cls.not_author = User.objects.create_user(
            username='super_user'
        )
        cls.comment_author = User.objects.create_user(
            username='batman')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.unauthorized_user = Client()
        self.authorized_user = Client()
        self.authorized_user.force_login(self.post_author)
        self.authorized_user_not_author = Client()
        self.authorized_user_not_author.force_login(self.not_author)
        self.authorized_user_comment_author = Client()
        self.authorized_user_comment_author.force_login(self.comment_author)

    def test_authorized_user_create_post(self):
        """Проверка создания записи авторизированным пользователем."""
        IMAGE_NAME = 'small.gif'
        uploaded = SimpleUploadedFile(
            name=IMAGE_NAME,
            content=self.small_gif,
            content_type='image/gif'
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста',
            'group': self.group.pk,
            'image': uploaded
        }

        response = self.authorized_user.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.post_author.username})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.latest('id')
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.post_author)
        self.assertEqual(post.group_id, form_data['group'])
        self.assertEqual(post.image, f'posts/{uploaded}')

    def test_authorized_user_author_edit_post(self):
        """Проверка редактирования записи автором."""
        IMAGE_NAME = 'small_0.gif'
        uploaded = SimpleUploadedFile(
            name=IMAGE_NAME,
            content=self.small_gif,
            content_type='image/gif'
        )

        post = Post.objects.create(
            text='Текст поста для редактирования',
            author=self.post_author,
            group=self.group,
        )
        form_data = {
            'text': 'Отредактированный текст поста',
            'group': self.group.pk,
            'image': uploaded,
        }

        response = self.authorized_user.post(
            reverse(
                'posts:post_edit',
                args=[post.id]),
            data=form_data,
            follow=True
        )

        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': post.id})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post_obj = Post.objects.latest('id')
        self.assertEqual(post_obj.text, form_data['text'])
        self.assertEqual(post_obj.pub_date, post.pub_date,)
        self.assertEqual(post_obj.author, post.author)
        self.assertEqual(post_obj.group.id, form_data['group'])
        self.assertEqual(post_obj.image, f'posts/{uploaded}')

    def test_unnauthorized_user_create_post(self):
        """Проверка создания записи неавторизированным пользователем."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста',
            'group': self.group.pk,
        }

        response = self.unauthorized_user.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        redirect = reverse('login') + '?next=' + reverse('posts:post_create')
        self.assertRedirects(response, redirect)
        self.assertEqual(Post.objects.count(), posts_count)

    def test_unauthorized_user_edit_post(self):
        """Проверка редактирования записи неавторизированным пользователем."""
        post = Post.objects.create(
            text='Текст поста для редактирования',
            author=self.post_author,
            group=self.group,
        )
        form_data = {
            'text': 'Отредактированный текст поста',
            'group': self.group.id
        }

        response = self.unauthorized_user.post(
            reverse(
                'posts:post_edit',
                args=[post.id]),
            data=form_data,
            follow=True
        )
        redirect = reverse('login') + '?next=' + reverse(
            'posts:post_edit',
            kwargs={'post_id': post.id})

        self.assertRedirects(response, redirect)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post_obj = Post.objects.latest('id')
        self.assertEqual(post_obj.text, post.text)
        self.assertEqual(post_obj.author, post.author)
        self.assertEqual(post_obj.group.id, post.group.id)

    def test_authorized_not_author_edit_post(self):
        """Проверка редактирования записи неавтором."""
        post = Post.objects.create(
            text='Текст поста для редактирования',
            author=self.post_author,
            group=self.group,
        )
        form_data = {
            'text': 'Отредактированный текст поста',
            'group': self.group.pk
        }

        response = self.authorized_user_not_author.post(
            reverse(
                'posts:post_edit',
                args=[post.id]),
            data=form_data,
            follow=True
        )

        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': post.id})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post_obj = Post.objects.latest('id')
        self.assertEqual(post_obj.text, post.text)
        self.assertEqual(post_obj.group.id, post.group.id)

    def test_create_post_without_group(self):
        """Создание поста без группы"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста',
        }

        response = self.authorized_user.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.post_author.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post_obj = Post.objects.latest('id')
        self.assertEqual(post_obj.text, form_data['text'])
        self.assertEqual(post_obj.author, self.post_author)
        self.assertTrue(post_obj.group is None)

    def test_authorized_user_create_comment(self):
        """Проверка создания комментария авторизированным пользователем."""
        comments_count = Comment.objects.count()
        post = Post.objects.create(
            text='Текст поста для редактирования',
            author=self.post_author,
            group=self.group,
        )
        form_data = {
            'text': 'Тестовый комментарий'
        }

        response = self.authorized_user_comment_author.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post.id}),
            data=form_data,
            follow=True)

        self.assertRedirects(
            response, reverse(
                'posts:post_detail',
                args={post.id})
        )
        comment = Comment.objects.latest('id')
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.comment_author)
        self.assertEqual(comment.post_id, post.id)

    def test_nonauthorized_user_create_comment(self):
        """Проверка создания комментария неавторизированным пользователем."""
        comments_count = Comment.objects.count()
        post = Post.objects.create(
            text='Текст поста для редактирования',
            author=self.post_author)
        form_data = {
            'text': 'Тестовый комментарий'
        }

        response = self.unauthorized_user.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )
        redirect = reverse('login') + '?next=' + reverse(
            'posts:add_comment', kwargs={'post_id': post.id})
        self.assertRedirects(response, redirect)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), comments_count)
