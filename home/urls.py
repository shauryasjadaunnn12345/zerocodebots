from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    home, features, services, about, contact,
    create_project_view, edit_project_view, import_from_website,
    project_analytics_dashboard, chatbot_view, embed_chatbot,
    project_summary_view, robots_txt, sitemap_xml, export_project_csv,
    blog_list, blog_detail, create_blog, edit_blog, delete_blog,
    my_blogs, my_projects, subscribe_newsletter,privacy_policy,terms_of_service
)

urlpatterns = [
    # Home & General
    path('', home, name='home'),
    path('features/', features, name='features'),
    path('about/', about, name='about'),
    path('contact/', contact, name='contact'),
    path('services/', services, name='services'),
    
    # Projects
    path('create-project/', create_project_view, name='create_project'),
    path('project/<int:pk>/edit/', edit_project_view, name='edit_project'),
    path('project/<int:pk>/import-website/', import_from_website, name='import_from_website'),
    path('project/<int:pk>/analytics/', project_analytics_dashboard, name='project_analytics_dashboard'),
    path('project/<int:pk>/summary/', project_summary_view, name='project_summary'),
    path('project/<int:pk>/export/', export_project_csv, name='export_project'),
    path('chatbot/<int:project_id>/', chatbot_view, name='chatbot'),
    path('embed-chatbot/', embed_chatbot, name='embed_chatbot'),
    path('my-projects/', my_projects, name='my_projects'),
    
    # Blog URLs
     path('blog/', blog_list, name='blog_list'),

    # ✅ STATIC routes first
    path('blog/create/', create_blog, name='create_blog'),
    path('my-blogs/', my_blogs, name='my_blogs'),

    # ✅ ID-based routes next
    path('blog/<int:pk>/edit/', edit_blog, name='edit_blog'),
    path('blog/<int:pk>/delete/', delete_blog, name='delete_blog'),

    # ✅ SLUG route LAST (always last)
    path('blog/<slug:slug>/', blog_detail, name='blog_detail'),
    
    # Newsletter
    path('api/newsletter/subscribe/', subscribe_newsletter, name='subscribe_newsletter'),
    
    # SEO
    path('robots.txt', robots_txt, name='robots'),
    path('sitemap.xml', sitemap_xml, name='sitemap'),
    path('privacy-policy/', privacy_policy, name='privacy_policy'),
    path('terms-of-service/', terms_of_service, name='terms_of_service'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)