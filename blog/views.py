from django.shortcuts import render, get_object_or_404
from .models import BlogPost, Tag
from .forms import CommentForm
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse



def blog_list(request):
    tag_slug = request.GET.get('tag')
    posts = BlogPost.objects.all().order_by('-created_at')

    if tag_slug:
        posts = posts.filter(tags__slug=tag_slug)

    paginator = Paginator(posts, 5)  # 5 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    tags = Tag.objects.all()
    return render(request, 'blog/blog_list.html', {
        'posts': posts,
        'page_obj': page_obj,
        'tags': tags,
        'active_tag': tag_slug
    })


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    
    # Only show approved comments
    comments = post.comments.filter(is_approved=True).order_by('-created_at')

    # Comment form
    form = CommentForm()

    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }

    return render(request, 'blog/blog_detail.html', context)


@csrf_exempt
def submit_comment(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.is_approved = False  # require admin approval
            comment.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Thank you! Your comment is awaiting approval.'
            })
        return JsonResponse({'status': 'error', 'message': 'Invalid form input.'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})

