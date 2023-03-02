from django.contrib.auth import get_user_model
from django.test import TestCase
from django.conf import settings

from .. models import Comment, Follow, Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            text='Тестовый текст больше 15 символов для проверки...',
            author=cls.user,
        )
        cls.group = Group.objects.create(
            title='Little Dodo',
            slug='Dodo',
            description='Тестовое описание'
        )

    def test_post_str(self):
        """Проверка __str__ у post."""
        self.assertEqual(
            self.post.text[:settings.CHARS_LENGTH],
            str(self.post)
        )

    def test_post_verbose_name(self):
        """Проверка verbose_name у post."""
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа', }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                verbose_name = self.post._meta.get_field(value).verbose_name
                self.assertEqual(verbose_name, expected)

    def test_help_text_name(self):
        post = PostModelTest.post
        field_help_text = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост'
        }
        for value, expected in field_help_text.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)

    def test_models_have_correct_object_names(self):
        post = PostModelTest.post
        group = PostModelTest.group
        field_str = {
            post.text[:settings.CHARS_LENGTH]: str(post),
            group.title: str(group)
        }
        for expected, value in field_str.items():
            with self.subTest(vatue=value):
                self.assertEqual(expected, value)


class FollowModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='test_user')
        cls.another_user = User.objects.create_user(
            username='test_another_user')
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.another_user,
        )

    def test_follow_str(self):
        """Проверка __str__ у follow."""
        self.assertEqual(
            f'{self.follow.user} подписался на {self.follow.author}',
            str(self.follow))

    def test_follow_verbose_name(self):
        """Проверка verbose_name у follow."""
        field_verboses = {
            'user': 'Пользователь',
            'author': 'Автор',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                verbose_name = self.follow._meta.get_field(value).verbose_name
                self.assertEqual(verbose_name, expected)


class CommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='auth'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
        )
        cls.comment = Comment.objects.create(
            text='Комментарий для поста',
            author=cls.user,
            post=cls.post,
        )

    def test_сomment_str(self):
        """Проверка __str__ у сomment."""
        self.assertEqual(
            self.comment.text[:settings.CHARS_LENGTH],
            str(self.comment)
        )

    def test_сomment_verbose_name(self):
        """Проверка verbose_name у сomment."""
        field_verboses = {
            'post': 'Пост',
            'author': 'Автор',
            'text': 'Комментарий',
            'created': 'Дата создания',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                verbose_name = self.comment._meta.get_field(value).verbose_name
                self.assertEqual(verbose_name, expected)
