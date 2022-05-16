from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        self.assertEqual(str(group), group.title)

        post = PostModelTest.post
        self.assertEqual(str(post), post.text[:15])

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post

        # Словарь для удобства проверки пачкой.
        field_verbose_name = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации1',
            'author': 'Автор',
            'group': 'Группа',
        }

        # Обходим словарь, в value помещается названиея полея,
        # в expected  - ожидаемое значение.
        for value, expected in field_verbose_name.items():

            # Выводим, чтобы посмотреть, как это работает.
            print(value, expected)

            # with - это менеджер контекста. На данном этапе просто примите,
            # как должное или можно почитать в ин-те,
            # если есть свободное место  в голове.

            # subTest. Это шутка создает минитест при каждом вызове.
            # Используется для облегчения отладки.
            # Если в каком-то кейсе тест провалится, то subTest покажет,
            # где именно и при каких обстоятельствах.
            # И не остановится на этой ошибкке и продолжит выполнять
            # остальные тесты.
            with self.subTest(value=value):
                # Получаем объект поля модели.
                field = post._meta.get_field(value)
                print(type(field))

                self.assertEqual(field.verbose_name, expected)
