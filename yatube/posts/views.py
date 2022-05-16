from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import cache_page

from posts.forms import PostForm, CommentForm
from posts.models import Post, Group, Follow
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect

User = get_user_model()

PAGE_COUNT = 10


# @cache_page(60 * 15)
def index(request):
    post_list = Post.objects.order_by('-pub_date')
    paginator = Paginator(post_list, PAGE_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Отдаем в словаре контекста
    context = {
        'title': 'Последние обновления на сайте',
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


# View-функция для страницы сообщества:
def group_posts(request, slug):
    group: Group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.filter(group=group).order_by('-pub_date')

    paginator = Paginator(post_list, PAGE_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'title': f'Записи сообщества {group.title}',
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=author).order_by('-pub_date')

    paginator = Paginator(post_list, PAGE_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    flw = Follow.objects.filter(user=author).exists()

    context = {
        'page_obj': page_obj,
        'page_count': post_list.count(),
        'author': author,
        'following': flw

    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    context = {
        'post': post,
        'page_count': post.author.posts.count(),
        'form': CommentForm(),
        'comments': post.comments.all(),
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    # Если тип запроса POST, т.е. нажали на кнопку формы.
    if request.POST:
        # Создаем объекты PostForm на основе данных переданных из запроса и
        # и файла картинки.
        form = PostForm(request.POST, files=request.FILES or None)

        # Если форма валидная.
        if form.is_valid():
            # Мы сохраняем форму и она возвращает инстанс поста.
            # но не сохраняет в БД. из-за флага commit
            post = form.save(commit=False)
            # Добавляем в инстанс пользователя.
            post.author = request.user
            # И тут при вызове метода save объект сохраняется в БД
            post.save()
            # Перенаправляем на страницу профиля.
            return redirect('posts:profile', username=request.user.username)
    else:
        # Если тип запроса GET, то мы создаем пустую форму.
        form = PostForm()

    # Добавляем форму в контекст и она отобразится в шаблоне.
    context = {
        'form': form,
        'action': reverse('posts:post_create')
    }

    # Метод в шаблон передает контекст и формирует html, который браузер
    # отобразит на странице.
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if request.POST:
        # Создаешь форму, передав в нее объект Post.
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post)

        # Валидируешь форму.
        if form.is_valid():
            # При сохранении формы, она возвращает объект post.
            # Если указан флаг commit=False, то данные не записываются в БД.
            post = form.save(commit=False)
            # Добавляешь в пост автора.
            post.author = request.user
            # Сохраняешь объект пост, и в этот момент,
            # данные записываются в БД.
            post.save()
            return redirect('posts:post_detail', post_id=post.pk)
    else:
        form = PostForm(instance=post)

    context = {
        'form': form,
        'is_edit': True,
        'action': reverse('posts:post_edit', kwargs={'post_id': post.pk})
    }

    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    # Получите пост
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()

    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    # информация о текущем пользователе доступна в переменной request.user
    authors_ids = Follow.objects.filter(user=request.user).values_list(
        'author', flat=True)

    posts = Post.objects.filter(author__in=authors_ids).order_by('-pub_date')

    paginator = Paginator(posts, PAGE_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }

    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.create(user=request.user, author=author)
    return redirect(reverse('posts:profile', kwargs={'username': username}))


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect(reverse('posts:index'))
