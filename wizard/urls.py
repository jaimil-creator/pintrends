from django.urls import path
from . import views

app_name = 'wizard'

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),
    
    # Dashboard (Home)
    path('', views.ProjectListView.as_view(), name='dashboard'),
    
    # Step 0: Create Project
    path('new/', views.ProjectCreateView.as_view(), name='project_create'),
    path('project/<int:project_id>/delete/', views.delete_project, name='delete_project'),
    
    # Step 1: Fetch Trends
    path('<int:project_id>/trends/', views.TrendFetchView.as_view(), name='trend_fetch'),
    path('<int:project_id>/trends/scrape/', views.scrape_trends_htmx, name='scrape_trends_htmx'),
    
    # Step 2: Keyword Review
    path('<int:project_id>/review/', views.KeywordReviewView.as_view(), name='keyword_review'),
    path('<int:project_id>/review/remove/<int:keyword_id>/', views.remove_keyword_htmx, name='remove_keyword'),
    
    # Step 3: Fetch Suggestions
    path('<int:project_id>/suggestions/', views.SuggestionFetchView.as_view(), name='suggestion_fetch'),
    path('<int:project_id>/suggestions/fetch/', views.fetch_suggestions_htmx, name='fetch_suggestions_htmx'),
    
    # Step 4: Keyword Expansion
    path('<int:project_id>/expand/', views.ExpansionView.as_view(), name='expansion'),
    path('<int:project_id>/expand/ai/', views.expand_keywords_htmx, name='expand_keywords_htmx'),
    path('<int:project_id>/expand/toggle/<int:keyword_id>/', views.toggle_expanded_keyword_htmx, name='toggle_expanded_keyword'),
    
    # Step 5: Content Generation
    path('<int:project_id>/content/', views.ContentGenView.as_view(), name='content_gen'),
    path('<int:project_id>/content/generate/', views.generate_content_htmx, name='generate_content_htmx'),
    
    # Content Editing
    path('article/<int:article_id>/edit/', views.edit_article_htmx, name='edit_article'),
    path('article/<int:article_id>/update/', views.update_article_htmx, name='update_article'),
    path('pin/<int:pin_id>/edit/', views.edit_pin_htmx, name='edit_pin'),
    path('pin/<int:pin_id>/update/', views.update_pin_htmx, name='update_pin'),
    
    path('<int:project_id>/export/', views.ExportView.as_view(), name='export'),
    path('<int:project_id>/export/csv/', views.export_csv, name='export_csv'),
    path('<int:project_id>/export/json/', views.export_json, name='export_json'),
    
    # Step 7: Blog Generation
    path('<int:project_id>/blog/', views.BlogGenView.as_view(), name='blog_gen'),
    path('article/<int:article_id>/generate-blog/', views.generate_blog_htmx, name='generate_blog_htmx'),
    path('blog/<int:blog_id>/regenerate/', views.regenerate_blog_htmx, name='regenerate_blog_htmx'),
    path('blog/<int:blog_id>/detail/', views.blog_detail_htmx, name='blog_detail_htmx'),
    path('blog/<int:blog_id>/edit/', views.blog_edit, name='blog_edit'),
    path('blog/<int:blog_id>/update/', views.blog_update, name='blog_update'),
    path('blog/<int:blog_id>/export/json/', views.export_blog_json, name='export_blog_json'),
    path('blog/<int:blog_id>/toggle-selection/', views.toggle_blog_selection_htmx, name='toggle_blog_selection_htmx'),
    path('<int:project_id>/project-images/', views.get_project_images_htmx, name='get_project_images_htmx'),
    path('pin/<int:pin_id>/update-image/', views.update_pin_image_htmx, name='update_pin_image_htmx'),
    
    # Blog Setup & Pin Setup (Project Sidebar)
    path('<int:project_id>/blog-setup/', views.BlogSetupView.as_view(), name='blog_setup'),
    path('<int:project_id>/blog/publish/', views.publish_blog_api, name='publish_blog_api'),
    path('<int:project_id>/pin-setup/', views.PinSetupView.as_view(), name='pin_setup'),
    path('<int:project_id>/pin-setup/generate-images/', views.generate_pin_images, name='generate_pin_images'),
    path('<int:project_id>/pin-setup/post-pinterest/', views.post_pins_pinterest, name='post_pins_pinterest'),
    
    # Analysis
    path('analysis/', views.AnalysisView.as_view(), name='analysis'),
    path('analysis/fetch/', views.fetch_analysis_data, name='analysis_fetch'),
    path('blog/<int:blog_id>/download-images/', views.download_blog_images, name='download_blog_images'),
]
