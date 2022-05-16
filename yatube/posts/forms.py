#!-*-coding:utf-8-*-
from django import forms

from posts.models import Post, Comment


class PostForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea, required=True, label='Текст')

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'group': 'Группа'
        }


class CommentForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea, required=True, label='Текст')

    class Meta:
        model = Comment
        fields = ('text', )
