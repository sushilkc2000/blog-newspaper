from datetime import timedelta
from typing import Any

from django.contrib import messages
from django.db.models.query import QuerySet
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.generic import ListView, TemplateView, View, DetailView

from newspaper.forms import ContactForm
from newspaper.models import Category, Post, Tag


class HomeView(ListView):
    model = Post
    template_name = "aznews/main/home/home.html"
    context_object_name = "posts"
    queryset = Post.objects.filter(status="active", published_at__isnull=False)[:5]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["featured_post"] = (
            Post.objects.filter(status="active", published_at__isnull=False)
            .order_by("-views_count")
            .first()
        )
        context["featured_posts"] = Post.objects.filter(
            status="active", published_at__isnull=False
        ).order_by("-views_count")[
            1:4
        ]  # 1, 2, 3
        one_week_ago = timezone.now() - timedelta(days=7)
        context["weekly_top_posts"] = Post.objects.filter(
            status="active",
            published_at__isnull=False,
            published_at__gte=one_week_ago,
        ).order_by("-published_at", "-views_count")[:7]

        return context


class AboutView(TemplateView):
    template_name = "aznews/about.html"


class ContactView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "aznews/contact.html")

    def post(self, request, *args, **kwargs):
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, "Successfully submitted your query. We will contact you soon."
            )
            return redirect("contact")
        else:
            messages.error(
                request,
                "Cannot submit your query. Please make sure all fields are valid.",
            )
            return render(
                request,
                "aznews/contact.html",
                {"form": form},
            )


class PostListView(ListView):
    model = Post
    template_name = "aznews/main/list/list.html"
    context_object_name = "posts"
    queryset = Post.objects.filter(
        status="active", published_at__isnull=False
    ).order_by("-published_at")
    paginate_by = 1


class PostByCategoryView(ListView):
    model = Post
    template_name = "aznews/main/list/list.html"
    context_object_name = "posts"
    paginate_by = 1

    def get_queryset(self):
        query = super().get_queryset()
        query = query.filter(
            status="active",
            published_at__isnull=False,
            category=self.kwargs["category_id"],
        ).order_by("-published_at")
        return query


class PostByTagView(ListView):
    model = Post
    template_name = "aznews/main/list/list.html"
    context_object_name = "posts"
    paginate_by = 1

    def get_queryset(self):
        query = super().get_queryset()
        query = query.filter(
            status="active",
            published_at__isnull=False,
            tag=self.kwargs["tag_id"],
        ).order_by("-published_at")
        return query


class PostDetailView(DetailView):
    model = Post
    template_name = "aznews/main/detail/detail.html"
    context_object_name = "post"
    queryset = Post.objects.filter(status="active", published_at__isnull=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        obj = self.get_object()  # currently viewed object => 4
        obj.views_count += 1
        obj.save()

        # 4 => 1, 2, 3 => 3 ,2, 1
        context["previous_post"] = (
            Post.objects.filter(
                status="active", published_at__isnull=False, id__lt=obj.id
            )
            .order_by("-id")
            .first()
        )

        # 4 => 5, 6,7, ... => 5, 6, 7, ... => 5
        context["next_post"] = (
            Post.objects.filter(
                status="active", published_at__isnull=False, id__gt=obj.id
            )
            .order_by("id")
            .first()
        )
        return context


from newspaper.forms import CommentForm


class CommentView(View):
    def post(self, request, *args, **kwargs):
        form = CommentForm(request.POST)
        post_id = request.POST["post"]
        if form.is_valid():
            form.save()
            return redirect("post-detail", post_id)
        else:
            post = Post.objects.get(id=post_id)
            return render(
                request,
                "aznews/main/detail/detail.html",
                {"post": post, "form": form},
            )
