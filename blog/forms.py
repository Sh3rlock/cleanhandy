from django import forms
from .models import BlogPost, Comment, Tag

class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'content', 'featured_image', 'tags']
        widgets = {
            'tags': forms.CheckboxSelectMultiple()
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['name', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3}),
        }

