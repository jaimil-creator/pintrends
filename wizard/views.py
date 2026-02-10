from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, TemplateView, View
from django.urls import reverse
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from .models import Project, TrendKeyword, Suggestion, ExpandedKeyword, Content, ArticleIdea, PinIdea, BlogPost, BlogSection

# ... (rest of imports)

def generate_content_htmx(request, project_id):
    """HTMX endpoint - Generates Articles and Pins based on user inputs."""
    from .services.content_generator import ContentGeneratorService
    
    project = get_object_or_404(Project, pk=project_id)
    
    # Parse inputs
    try:
        article_count = int(request.GET.get('article_count', 5))
        pin_count = int(request.GET.get('pin_count', 5))
    except ValueError:
        article_count = 5
        pin_count = 5

    # Clear existing content to allow fresh regeneration
    ArticleIdea.objects.filter(project=project).delete()
    PinIdea.objects.filter(project=project).delete()
    
    generator = ContentGeneratorService()

    try:
        # Fetch all expanded keywords
        expanded_keywords = ExpandedKeyword.objects.filter(project=project, selected=True)
        
        if not expanded_keywords.exists():
            return render(request, 'wizard/partials/error.html', {'error': 'No expanded keywords found. Go back and selected some phrases.'})
        
        # Pre-fetch suggestions
        all_suggestions = list(Suggestion.objects.filter(project=project))
        suggestions_map = {}
        for s in all_suggestions:
            if s.base_keyword not in suggestions_map:
                suggestions_map[s.base_keyword] = []
            suggestions_map[s.base_keyword].append(s.suggestion)
            
        generated_count = 0
        
        for kw_obj in expanded_keywords:
            # 1. Generate Articles
            articles = generator.generate_article_titles(
                keyword=kw_obj.keyword,
                count=article_count
            )
            
            # Save Articles
            saved_articles = []
            for a in articles:
                saved_articles.append(ArticleIdea(
                    project=project,
                    expanded_keyword=kw_obj,
                    title=a.get('title', ''),
                    hook=a.get('hook', '')
                ))
            ArticleIdea.objects.bulk_create(saved_articles)

            # 2. Generate Pins (Use first article title as context if avail, else keyword)
            context_title = articles[0]['title'] if articles else kw_obj.keyword
            context_suggestions = suggestions_map.get(kw_obj.base_keyword, [])
            
            pins = generator.generate_pin_ideas(
                keyword=kw_obj.keyword,
                article_title=context_title,
                suggestions=context_suggestions,
                count=pin_count
            )
            
            # Save Pins
            saved_pins = []
            for p in pins:
                saved_pins.append(PinIdea(
                    project=project,
                    expanded_keyword=kw_obj,
                    title=p.get('title', ''),
                    description=p.get('description', '')
                ))
            PinIdea.objects.bulk_create(saved_pins)
            
            generated_count += 1
        
        # Fetch results with prefetch for display
        keywords_with_content = ExpandedKeyword.objects.filter(
            project=project, selected=True
        ).prefetch_related('article_ideas', 'pin_ideas')
        
        return render(request, 'wizard/partials/content_list.html', {
            'keywords_with_content': keywords_with_content,
            'total_generated': generated_count,
            'article_count': article_count,
            'pin_count': pin_count
        })
        
    except Exception as e:
        return render(request, 'wizard/partials/error.html', {'error': str(e)})
import asyncio
from asgiref.sync import sync_to_async, async_to_sync
from django import forms
import csv
import json

def health_check(request):
    """Simple debug view to test if server is responding."""
    return HttpResponse("Django OK", content_type="text/plain")

# ============= DASHBOARD: Project List =============
class ProjectListView(TemplateView):
    template_name = 'wizard/project_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        projects = Project.objects.all().order_by('-created_at')
        
        # Add stats to each project
        projects_with_stats = []
        for project in projects:
            projects_with_stats.append({
                'project': project,
                'stats': project.get_stats(),
                'stage': project.get_stage_display(),
                'resume_url': project.get_resume_url()
            })
        
        context['projects_with_stats'] = projects_with_stats
        return context

# ============= STEP 0: Create Project =============
class ProjectCreateView(CreateView):
    model = Project
    fields = ['name', 'niche']
    template_name = 'wizard/project_create.html'
    
    def get_success_url(self):
        return reverse('wizard:trend_fetch', kwargs={'project_id': self.object.id})

# ============= STEP 1: Fetch Trends =============
class TrendFetchView(TemplateView):
    template_name = 'wizard/trend_fetch.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_id = self.kwargs['project_id']
        context['project'] = get_object_or_404(Project, pk=project_id)
        context['trends'] = TrendKeyword.objects.filter(project_id=project_id)
        return context
    
    def post(self, request, *args, **kwargs):
        project_id = self.kwargs['project_id']
        selected_ids = request.POST.getlist('selected_trends')
        
        project = get_object_or_404(Project, pk=project_id)
        project.trends.update(selected=False)
        project.trends.filter(id__in=selected_ids).update(selected=True)
        
        return redirect('wizard:keyword_review', project_id=project_id)

def scrape_trends_htmx(request, project_id):
    """HTMX triggered view to run scraper and return HTML partial of trends."""
    from .services.pinterest_scraper import PinterestScraperService
    
    # Parse filter parameters
    country = request.GET.get('country', 'US')
    trend_type = request.GET.get('type', '3')
    age = request.GET.get('age', '')  # e.g., '18-24'
    gender = request.GET.get('gender', '')  # e.g., 'female'
    
    # Interests are multi-select, join with %7C (URL-encoded |)
    interests = request.GET.getlist('interests')  # List of interest IDs
    interests_str = '%7C'.join(interests) if interests else ''
    
    scraper = PinterestScraperService()
    try:
        trends = async_to_sync(scraper.get_top_trends)(
            country=country, 
            trend_type=trend_type,
            interests=interests_str,
            age=age,
            gender=gender
        )
        
        project = get_object_or_404(Project, pk=project_id)
        
        # Clear ALL existing trends before adding new ones
        project.trends.all().delete()
        
        for t in trends:
            kw = t['keyword']
            TrendKeyword.objects.create(
                project=project,
                keyword=kw,
                trend_score=0
            )
                
        all_trends = project.trends.all()
        return render(request, 'wizard/partials/trend_list.html', {
            'trends': all_trends,
            'country': country,
            'trend_type': trend_type
        })
        
    except Exception as e:
        return render(request, 'wizard/partials/error.html', {'error': str(e)})

# ============= STEP 2: Keyword Review =============
class KeywordReviewView(TemplateView):
    template_name = 'wizard/keyword_review.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_id = self.kwargs['project_id']
        context['project'] = get_object_or_404(Project, pk=project_id)
        context['selected_keywords'] = TrendKeyword.objects.filter(
            project_id=project_id, selected=True
        )
        return context
    
    def post(self, request, *args, **kwargs):
        project_id = self.kwargs['project_id']
        project = get_object_or_404(Project, pk=project_id)
        
        # Handle adding manual keyword
        manual_keyword = request.POST.get('manual_keyword', '').strip()
        if manual_keyword:
            TrendKeyword.objects.get_or_create(
                project=project,
                keyword=manual_keyword,
                defaults={'selected': True, 'trend_score': 0}
            )
            return redirect('wizard:keyword_review', project_id=project_id)
        
        # Handle proceed to next step
        if 'proceed' in request.POST:
            return redirect('wizard:suggestion_fetch', project_id=project_id)
        
        return redirect('wizard:keyword_review', project_id=project_id)

def remove_keyword_htmx(request, project_id, keyword_id):
    """HTMX endpoint to remove a keyword."""
    keyword = get_object_or_404(TrendKeyword, pk=keyword_id, project_id=project_id)
    keyword.selected = False
    keyword.save()
    return HttpResponse("")  # Empty response removes the element

# ============= STEP 3: Fetch Suggestions =============
class SuggestionFetchView(TemplateView):
    template_name = 'wizard/suggestion_fetch.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_id = self.kwargs['project_id']
        context['project'] = get_object_or_404(Project, pk=project_id)
        context['base_keywords'] = TrendKeyword.objects.filter(
            project_id=project_id, selected=True
        )
        context['suggestions'] = Suggestion.objects.filter(project_id=project_id)
        return context
    
    def post(self, request, *args, **kwargs):
        project_id = self.kwargs['project_id']
        
        # Handle proceed to expansion
        if 'proceed' in request.POST:
            return redirect('wizard:expansion', project_id=project_id)
        
        return redirect('wizard:suggestion_fetch', project_id=project_id)

def fetch_suggestions_htmx(request, project_id):
    """HTMX endpoint to fetch suggestions for all selected keywords."""
    from .services.pinterest_scraper import PinterestScraperService
    
    project = get_object_or_404(Project, pk=project_id)
    base_keywords = TrendKeyword.objects.filter(project=project, selected=True)
    
    # Clear existing suggestions to prevent stale data
    Suggestion.objects.filter(project=project).delete()
    
    scraper = PinterestScraperService()
    results = []
    
    for kw in base_keywords:
        try:
            suggestions = async_to_sync(scraper.get_suggestions)(kw.keyword)
            for s in suggestions:
                Suggestion.objects.get_or_create(
                    project=project,
                    base_keyword=kw.keyword,
                    suggestion=s
                )
            results.append({'keyword': kw.keyword, 'count': len(suggestions), 'status': 'success'})
        except Exception as e:
            results.append({'keyword': kw.keyword, 'count': 0, 'status': 'error', 'error': str(e)})
    
    suggestions = Suggestion.objects.filter(project=project)
    return render(request, 'wizard/partials/suggestion_list.html', {
        'project': project,
        'suggestions': suggestions,
        'results': results
    })

# ============= STEP 4: Keyword Expansion =============
class ExpansionView(TemplateView):
    template_name = 'wizard/expansion.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_id = self.kwargs['project_id']
        project = get_object_or_404(Project, pk=project_id)
        context['project'] = project
        
        # Get expanded keywords, ordered by base_keyword for regrouping
        context['expanded_keywords'] = ExpandedKeyword.objects.filter(project=project).order_by('base_keyword')
        
        # Source data for display
        context['base_keywords'] = TrendKeyword.objects.filter(project=project, selected=True)
        context['suggestions'] = Suggestion.objects.filter(project=project)
        
        return context
    
    def post(self, request, *args, **kwargs):
        project_id = self.kwargs['project_id']
        
        if 'proceed' in request.POST:
            return redirect('wizard:content_gen', project_id=project_id)
        
        return redirect('wizard:expansion', project_id=project_id)

def expand_keywords_htmx(request, project_id):
    """HTMX endpoint to expand keywords using AI."""
    from .services.content_generator import ContentGeneratorService
    
    project = get_object_or_404(Project, pk=project_id)
    
    # Get source data
    base_keywords = list(TrendKeyword.objects.filter(
        project=project, selected=True
    ).values_list('keyword', flat=True))
    
    # Clear old expanded keywords
    ExpandedKeyword.objects.filter(project=project).delete()

    # Prepare items for grouped processing
    items_to_process = []
    
    for kw in base_keywords:
        kw_suggestions = list(Suggestion.objects.filter(
            project=project,
            base_keyword=kw
        ).values_list('suggestion', flat=True))
        
        items_to_process.append({
            'keyword': kw,
            'suggestions': kw_suggestions
        })
    
    try:
        generator = ContentGeneratorService()
        expanded = generator.expand_keywords_with_ai(
            items=items_to_process,
            niche=project.niche or ""
        )
        
        # Save to database
        for item in expanded:
            ExpandedKeyword.objects.create(
                project=project,
                keyword=item.get('keyword', ''),
                base_keyword=item.get('base', base_keywords[0] if base_keywords else ''),
                intent=item.get('intent', 'ideas'),
                score=item.get('score', 75)
            )
        
        all_expanded = ExpandedKeyword.objects.filter(project=project).order_by('base_keyword')
        return render(request, 'wizard/partials/expanded_list.html', {
            'project': project,
            'expanded_keywords': all_expanded,
            'success': True
        })
        
    except Exception as e:
        return render(request, 'wizard/partials/error.html', {'error': str(e)})

def toggle_expanded_keyword_htmx(request, project_id, keyword_id):
    """HTMX endpoint to toggle selection of an expanded keyword."""
    kw = get_object_or_404(ExpandedKeyword, pk=keyword_id, project_id=project_id)
    kw.selected = not kw.selected
    kw.save()
    
    # Return a button/icon state or just the updated card class (optional)
    # For now, we'll simpler return a 200 OK and handle visual toggle in client or re-render a tiny part
    # But to make it robust, let's return a simple icon swap or just an OK status and let client class toggle
    return HttpResponse("")


# ============= STEP 5: Content Generation =============
class ContentGenView(TemplateView):
    template_name = 'wizard/content_gen.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_id = self.kwargs['project_id']
        project = get_object_or_404(Project, pk=project_id)
        context['project'] = project
        context['keywords'] = ExpandedKeyword.objects.filter(project=project)
        
        # STRUCTURED VIEW: Group by Keyword
        context['keywords_with_content'] = ExpandedKeyword.objects.filter(
            project=project, selected=True
        ).prefetch_related('article_ideas', 'pin_ideas')
        
        # Calculate stats
        context['generated_count'] = ArticleIdea.objects.filter(project=project).count() + PinIdea.objects.filter(project=project).count()
        return context
    
    def post(self, request, *args, **kwargs):
        project_id = self.kwargs['project_id']
        
        if 'proceed' in request.POST:
            return redirect('wizard:blog_gen', project_id=project_id)
        
        return redirect('wizard:content_gen', project_id=project_id)

def generate_content_htmx(request, project_id):
    """HTMX endpoint - Generates Articles and Pins based on user inputs."""
    from .services.content_generator import ContentGeneratorService
    
    project = get_object_or_404(Project, pk=project_id)
    
    # Parse inputs
    try:
        article_count = int(request.GET.get('article_count', 5))
        pin_count = int(request.GET.get('pin_count', 5))
    except ValueError:
        article_count = 5
        pin_count = 5

    # Clear existing content to allow fresh regeneration
    ArticleIdea.objects.filter(project=project).delete()
    PinIdea.objects.filter(project=project).delete()
    
    generator = ContentGeneratorService()

    try:
        # Fetch all expanded keywords
        expanded_keywords = ExpandedKeyword.objects.filter(project=project, selected=True)
        
        if not expanded_keywords.exists():
            return render(request, 'wizard/partials/error.html', {'error': 'No expanded keywords found. Go back and select some phrases.'})
        
        # Pre-fetch suggestions
        all_suggestions = list(Suggestion.objects.filter(project=project))
        suggestions_map = {}
        for s in all_suggestions:
            if s.base_keyword not in suggestions_map:
                suggestions_map[s.base_keyword] = []
            suggestions_map[s.base_keyword].append(s.suggestion)
            
        generated_count = 0
        
        for kw_obj in expanded_keywords:
            # 1. Generate Articles
            articles = generator.generate_article_titles(
                keyword=kw_obj.keyword,
                count=article_count
            )
            
            # Save Articles
            saved_articles = []
            for a in articles:
                saved_articles.append(ArticleIdea(
                    project=project,
                    expanded_keyword=kw_obj,
                    title=a.get('title', ''),
                    hook=a.get('hook', '')
                ))
            ArticleIdea.objects.bulk_create(saved_articles)

            # 2. Generate Pins (Use first article title as context if avail, else keyword)
            context_title = articles[0]['title'] if articles else kw_obj.keyword
            context_suggestions = suggestions_map.get(kw_obj.base_keyword, [])
            
            pins = generator.generate_pin_ideas(
                keyword=kw_obj.keyword,
                article_title=context_title,
                suggestions=context_suggestions,
                count=pin_count
            )
            
            # Save Pins
            saved_pins = []
            for p in pins:
                saved_pins.append(PinIdea(
                    project=project,
                    expanded_keyword=kw_obj,
                    title=p.get('title', ''),
                    description=p.get('description', '')
                ))
            PinIdea.objects.bulk_create(saved_pins)
            
            generated_count += 1
        
        # Fetch results with prefetch for display
        keywords_with_content = ExpandedKeyword.objects.filter(
            project=project, selected=True
        ).prefetch_related('article_ideas', 'pin_ideas')
        
        return render(request, 'wizard/partials/content_list.html', {
            'project': project,
            'keywords_with_content': keywords_with_content,
            'total_generated': generated_count,
            'article_count': article_count,
            'pin_count': pin_count
        })
        
    except Exception as e:
        return render(request, 'wizard/partials/error.html', {'error': str(e)})

# ============= STEP 6: Export =============
class ExportView(TemplateView):
    template_name = 'wizard/export.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_id = self.kwargs['project_id']
        project = get_object_or_404(Project, pk=project_id)
        context['project'] = project
        context['keywords_with_content'] = ExpandedKeyword.objects.filter(
            project=project, selected=True
        ).prefetch_related('article_ideas', 'pin_ideas')
        return context

def export_csv(request, project_id):
    """Export all content as CSV."""
    import csv
    project = get_object_or_404(Project, pk=project_id)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{project.name}_content.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Keyword', 'Type', 'Title', 'Details (Hook/Description)'])
    
    keywords = ExpandedKeyword.objects.filter(project=project, selected=True).prefetch_related('article_ideas', 'pin_ideas')
    
    for kw in keywords:
        for article in kw.article_ideas.all():
            writer.writerow([kw.keyword, 'Article', article.title, article.hook])
        for pin in kw.pin_ideas.all():
            writer.writerow([kw.keyword, 'Pin', pin.title, pin.description])
    
    return response

def export_json(request, project_id):
    """Export all content as JSON."""
    import json
    project = get_object_or_404(Project, pk=project_id)
    
    keywords = ExpandedKeyword.objects.filter(project=project, selected=True).prefetch_related('article_ideas', 'pin_ideas')
    
    content_data = []
    for kw in keywords:
        content_data.append({
            'keyword': kw.keyword,
            'articles': [{'title': a.title, 'hook': a.hook} for a in kw.article_ideas.all()],
            'pins': [{'title': p.title, 'description': p.description} for p in kw.pin_ideas.all()]
        })
    
    data = {
        'project': project.name,
        'niche': project.niche,
        'content': content_data
    }
    
    response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="{project.name}_content.json"'
    return response

# ============= Edit Content Endpoints =============
def edit_article_htmx(request, article_id):
    """HTMX endpoint - Returns edit form for an article."""
    article = get_object_or_404(ArticleIdea, pk=article_id)
    return render(request, 'wizard/partials/edit_article.html', {
        'article': article
    })

def update_article_htmx(request, article_id):
    """HTMX endpoint - Updates an article and returns refreshed content list."""
    article = get_object_or_404(ArticleIdea, pk=article_id)
    
    if request.method == 'POST':
        article.title = request.POST.get('title', article.title)
        article.hook = request.POST.get('hook', article.hook)
        article.save()
        
        # Return refreshed content list
        project = article.project
        keywords_with_content = ExpandedKeyword.objects.filter(
            project=project, selected=True
        ).prefetch_related('article_ideas', 'pin_ideas')
        
        return render(request, 'wizard/partials/content_list.html', {
            'project': project,
            'keywords_with_content': keywords_with_content
        })
    
    return HttpResponse(status=400)

def edit_pin_htmx(request, pin_id):
    """HTMX endpoint - Returns edit form for a pin."""
    pin = get_object_or_404(PinIdea, pk=pin_id)
    return render(request, 'wizard/partials/edit_pin.html', {
        'pin': pin
    })

def update_pin_htmx(request, pin_id):
    """HTMX endpoint - Updates a pin and returns refreshed content list."""
    pin = get_object_or_404(PinIdea, pk=pin_id)
    
    if request.method == 'POST':
        pin.title = request.POST.get('title', pin.title)
        pin.description = request.POST.get('description', pin.description)
        pin.save()
        
        # Return refreshed content list
        project = pin.project
        keywords_with_content = ExpandedKeyword.objects.filter(
            project=project, selected=True
        ).prefetch_related('article_ideas', 'pin_ideas')
        
        return render(request, 'wizard/partials/content_list.html', {
            'project': project,
            'keywords_with_content': keywords_with_content
        })
    
    return HttpResponse(status=400)


# ============= STEP 7: Blog Generation =============
class BlogGenView(TemplateView):
    template_name = 'wizard/blog_gen.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_id = self.kwargs['project_id']
        project = get_object_or_404(Project, pk=project_id)
        context['project'] = project
        
        # Get all article ideas with their blog generation status
        context['article_ideas'] = ArticleIdea.objects.filter(
            project=project
        ).prefetch_related('blog_posts')
        
        # Get all generated blogs
        context['blog_posts'] = BlogPost.objects.filter(
            project=project
        ).prefetch_related('sections').order_by('-created_at')
        
        return context
    
    def post(self, request, *args, **kwargs):
        project_id = self.kwargs['project_id']
        
        if 'proceed' in request.POST:
            return redirect('wizard:export', project_id=project_id)
        
        return redirect('wizard:blog_gen', project_id=project_id)

def generate_blog_htmx(request, article_id):
    """HTMX endpoint - Generate a complete blog from an article idea."""
    from django.core.files.base import ContentFile
    from .services.blog_generator import BlogGeneratorService
    import json as json_module
    import traceback
    
    article = get_object_or_404(ArticleIdea, pk=article_id)
    project = article.project
    
    # Create blog post record
    blog_post = BlogPost.objects.create(
        project=project,
        article_idea=article,
        topic=article.title,
        intro="",
        conclusion="",
        generation_status='generating'
    )
    
    try:
        generator = BlogGeneratorService()
        
        # Step 1: Generate blog content
        print(f"Generating blog content for: {article.title}")
        blog_content = generator.generate_blog_content(article.title)
        
        # Step 2: Parse content
        intro, items, conclusion = generator.parse_blog_content(blog_content)
        
        if not items:
            raise Exception("No blog sections generated")
        
        # Update blog post with text content
        blog_post.intro = intro
        blog_post.conclusion = conclusion
        blog_post.save()
        
        # Step 3: Generate image prompts
        print("Generating image prompts...")
        thumbnail_prompt = generator.generate_image_prompt(
            title=article.title,
            description=intro,
            prompt_type="thumbnail"
        )
        
        blog_post.thumbnail_prompt = thumbnail_prompt
        blog_post.save()
        
        item_prompts = {}
        for i, item in enumerate(items):
            prompt = generator.generate_image_prompt(
                title=item['title'],
                description=item['description'],
                prompt_type="image",
                blog_topic=article.title
            )
            item_prompts[f'item_{i}'] = prompt
        
        # Step 4: Generate all images in parallel
        print("Generating images in parallel...")
        all_prompts = {'thumbnail': thumbnail_prompt}
        all_prompts.update(item_prompts)
        
        images = generator.generate_all_images_parallel(all_prompts)
        
        # Update thumbnail URL
        blog_post.thumbnail_url = images.get('thumbnail', '')
        blog_post.save()
        
        # Step 5: Create blog sections with images
        for i, item in enumerate(items):
            BlogSection.objects.create(
                blog_post=blog_post,
                order=i + 1,
                title=item['title'],
                description=item['description'],
                image_url=images.get(f'item_{i}', ''),
                image_prompt=item_prompts.get(f'item_{i}', '')
            )
        
        # Step 6: Generate export files
        print("Generating export files...")
        blog_data = {
            'topic': blog_post.topic,
            'intro': blog_post.intro,
            'conclusion': blog_post.conclusion,
            'thumbnail_url': blog_post.thumbnail_url,
            'sections': [
                {
                    'title': section.title,
                    'description': section.description,
                    'image_url': section.image_url
                }
                for section in blog_post.sections.all()
            ]
        }
        
        # Generate DOCX
        docx_stream = generator.create_docx(blog_data)
        blog_post.docx_file.save(
            f'blog_{blog_post.id}.docx',
            ContentFile(docx_stream.read()),
            save=False
        )
        
        # Generate JSON
        json_data = generator.create_pinterest_json(blog_data)
        blog_post.json_file.save(
            f'blog_{blog_post.id}.json',
            ContentFile(json_module.dumps(json_data, indent=2)),
            save=False
        )
        
        # Mark as completed
        blog_post.generation_status = 'completed'
        blog_post.save()
        
        print(f"✓ Blog generation completed for: {article.title}")
        
        # Return success partial
        return render(request, 'wizard/partials/blog_success.html', {
            'blog_post': blog_post,
            'project': project
        })
        
    except Exception as e:
        print(f"✗ Blog generation failed: {e}")
        traceback.print_exc()
        
        blog_post.generation_status = 'failed'
        blog_post.error_message = str(e)
        blog_post.save()
        
        return render(request, 'wizard/partials/error.html', {
            'error': f'Blog generation failed: {str(e)}'
        })

def blog_detail_htmx(request, blog_id):
    """HTMX endpoint - Show blog preview."""
    blog_post = get_object_or_404(BlogPost, pk=blog_id)
    
    return render(request, 'wizard/partials/blog_preview.html', {
        'blog_post': blog_post,
        'sections': blog_post.sections.all()
    })

def regenerate_blog_htmx(request, blog_id):
    """HTMX endpoint - Regenerate a blog post with new AI content."""
    from django.core.files.base import ContentFile
    from .services.blog_generator import BlogGeneratorService
    import json as json_module
    import traceback
    
    blog_post = get_object_or_404(BlogPost, pk=blog_id)
    project = blog_post.project
    article = blog_post.article_idea
    
    # Delete old sections
    blog_post.sections.all().delete()
    
    # Reset blog post
    blog_post.intro = ""
    blog_post.conclusion = ""
    blog_post.thumbnail_url = ""
    blog_post.thumbnail_prompt = ""
    blog_post.generation_status = 'generating'
    blog_post.error_message = ""
    blog_post.save()
    
    try:
        generator = BlogGeneratorService()
        
        # Step 1: Generate blog content
        print(f"Regenerating blog content for: {article.title}")
        blog_content = generator.generate_blog_content(article.title)
        
        # Step 2: Parse content
        intro, items, conclusion = generator.parse_blog_content(blog_content)
        
        if not items:
            raise Exception("No blog sections generated")
        
        # Update blog post with text content
        blog_post.intro = intro
        blog_post.conclusion = conclusion
        blog_post.save()
        
        # Step 3: Generate image prompts
        print("Generating image prompts...")
        thumbnail_prompt = generator.generate_image_prompt(
            title=article.title,
            description=intro,
            prompt_type="thumbnail"
        )
        
        blog_post.thumbnail_prompt = thumbnail_prompt
        blog_post.save()
        
        item_prompts = {}
        for i, item in enumerate(items):
            prompt = generator.generate_image_prompt(
                title=item['title'],
                description=item['description'],
                prompt_type="image",
                blog_topic=article.title
            )
            item_prompts[f'item_{i}'] = prompt
        
        # Step 4: Generate all images in parallel
        print("Generating images in parallel...")
        all_prompts = {'thumbnail': thumbnail_prompt}
        all_prompts.update(item_prompts)
        
        images = generator.generate_all_images_parallel(all_prompts)
        
        # Update thumbnail URL
        blog_post.thumbnail_url = images.get('thumbnail', '')
        blog_post.save()
        
        # Step 5: Create blog sections with images
        for i, item in enumerate(items):
            BlogSection.objects.create(
                blog_post=blog_post,
                order=i + 1,
                title=item['title'],
                description=item['description'],
                image_url=images.get(f'item_{i}', ''),
                image_prompt=item_prompts.get(f'item_{i}', '')
            )
        
        # Step 6: Generate export files
        print("Generating export files...")
        blog_data = {
            'topic': blog_post.topic,
            'intro': blog_post.intro,
            'conclusion': blog_post.conclusion,
            'thumbnail_url': blog_post.thumbnail_url,
            'sections': [
                {
                    'title': section.title,
                    'description': section.description,
                    'image_url': section.image_url
                }
                for section in blog_post.sections.all()
            ]
        }
        
        # Generate DOCX
        docx_stream = generator.create_docx(blog_data)
        blog_post.docx_file.save(
            f'blog_{blog_post.id}.docx',
            ContentFile(docx_stream.read()),
            save=False
        )
        
        # Generate JSON
        json_data = generator.create_pinterest_json(blog_data)
        blog_post.json_file.save(
            f'blog_{blog_post.id}.json',
            ContentFile(json_module.dumps(json_data, indent=2)),
            save=False
        )
        
        # Mark as completed
        blog_post.generation_status = 'completed'
        blog_post.save()
        
        print(f"✓ Blog regeneration completed for: {article.title}")
        
        # Render success content
        response = render(request, 'wizard/partials/blog_success.html', {
            'blog_post': blog_post,
            'project': project
        })
        
        # Render toast notification (OOB swap)
        toast = render(request, 'wizard/partials/toast_success.html')
        
        # Combine responses
        return HttpResponse(response.content + toast.content)
        
    except Exception as e:
        print(f"✗ Blog regeneration failed: {e}")
        traceback.print_exc()
        
        blog_post.generation_status = 'failed'
        blog_post.error_message = str(e)
        blog_post.save()
        
        return render(request, 'wizard/partials/error.html', {
            'error': f'Blog regeneration failed: {str(e)}'
        })

def blog_edit(request, blog_id):
    """Full page endpoint - Show blog edit form."""
    import json as json_module
    from .services.blog_generator import BlogGeneratorService
    
    blog_post = get_object_or_404(BlogPost, pk=blog_id)
    
    # Use stored structured_content for preview
    if blog_post.structured_content:
        json_preview = json_module.dumps(blog_post.structured_content, indent=2)
    else:
        # Fallback if empty (shouldn't happen with migration, but safe)
        generator = BlogGeneratorService()
        blog_data = {
            'topic': blog_post.topic,
            'intro': blog_post.intro,
            'conclusion': blog_post.conclusion,
            'thumbnail_url': blog_post.thumbnail_url,
            'sections': [
                {
                    'title': section.title,
                    'description': section.description,
                    'image_url': section.image_url
                }
                for section in blog_post.sections.all()
            ]
        }
        json_preview_data = generator.create_pinterest_json(blog_data)
        json_preview = json_module.dumps(json_preview_data, indent=2)
    
    return render(request, 'wizard/blog_edit.html', {
        'blog_post': blog_post,
        'sections': blog_post.sections.all(),
        'json_preview': json_preview
    })

def blog_update(request, blog_id):
    """Full page endpoint - Update blog post and sections."""
    from django.core.files.base import ContentFile
    from .services.blog_generator import BlogGeneratorService
    import json as json_module
    
    blog_post = get_object_or_404(BlogPost, pk=blog_id)
    
    if request.method == 'POST':
        # Update Main Blog Fields
        blog_post.topic = request.POST.get('topic', blog_post.topic)
        blog_post.intro = request.POST.get('intro', blog_post.intro)
        blog_post.conclusion = request.POST.get('conclusion', blog_post.conclusion)
        blog_post.save()
        
        # Update Sections
        section_ids = request.POST.getlist('section_ids')
        for sec_id in section_ids:
            try:
                section = BlogSection.objects.get(pk=sec_id, blog_post=blog_post)
                section.title = request.POST.get(f'section_title_{sec_id}', section.title)
                section.description = request.POST.get(f'section_description_{sec_id}', section.description)
                section.save()
            except BlogSection.DoesNotExist:
                continue

        # Sync to structured_content JSON
        try:
            import uuid
            import json as json_module
            
            # Construct JSON structure matching requirement
            features = []
            for section in blog_post.sections.all().order_by('order'):
                feature = {
                    "title": section.title,
                    "image_url": section.image_url,
                    "button_text": "Try Now",
                    "button_url": "https://www.dressr.ai/clothes-swap",
                    "description": [section.description],
                    "order": section.order 
                }
                features.append(feature)
            
            # Preserve existing ID if possible, or generate new
            existing_id = blog_post.structured_content.get("id") if blog_post.structured_content else f"pinterest-blog-{uuid.uuid4().hex[:8]}"
            
            json_data = {
                "id": existing_id,
                "title": blog_post.topic,
                "thumbnail_url": blog_post.thumbnail_url,
                "alt": f"{blog_post.topic} thumbnail",
                "description": [blog_post.intro],
                "metadata": {
                    "title": blog_post.topic,
                    "description": [blog_post.intro]
                },
                "features": features,
                "conclusion": [blog_post.conclusion],
                "publish_button_text": "Publish"
            }
            
            blog_post.structured_content = json_data
            blog_post.save()
            
        except Exception as e:
            print(f"Error syncing structured_content: {e}")
        
        # No need to regenerate exports (DOCX/JSON) on save
        # They are now generated on-demand when downloading
        
        # Determine redirect URL based on project stage or default
        return redirect('wizard:blog_gen', project_id=blog_post.project.id)

    return HttpResponse(status=400)

def export_blog_docx(request, blog_id):
    """Download blog as DOCX file (Generated on-demand)."""
    from django.http import FileResponse
    from django.core.files.base import ContentFile
    from .services.blog_generator import BlogGeneratorService
    
    blog_post = get_object_or_404(BlogPost, pk=blog_id)
    
    try:
        # Generate DOCX on the fly
        generator = BlogGeneratorService()
        
        # Helper to get description string from list or string
        def get_desc(d):
            if isinstance(d, list):
                return d[0] if d else ""
            return str(d)

        # Construct blog_data from structured_content if available
        if blog_post.structured_content:
            sc = blog_post.structured_content
            blog_data = {
                'topic': sc.get('title', blog_post.topic),
                'intro': get_desc(sc.get('description', [blog_post.intro])),
                'conclusion': get_desc(sc.get('conclusion', [blog_post.conclusion])),
                'thumbnail_url': sc.get('thumbnail_url', blog_post.thumbnail_url),
                'sections': [
                    {
                        'title': f.get('title'),
                        'description': get_desc(f.get('description', [''])),
                        'image_url': f.get('image_url')
                    }
                    for f in sc.get('features', [])
                ]
            }
        else:
            # Fallback to DB relational data
            blog_data = {
                'topic': blog_post.topic,
                'intro': blog_post.intro,
                'conclusion': blog_post.conclusion,
                'thumbnail_url': blog_post.thumbnail_url,
                'sections': [
                    {
                        'title': section.title,
                        'description': section.description,
                        'image_url': section.image_url
                    }
                    for section in blog_post.sections.all()
                ]
            }
        
        docx_stream = generator.create_docx(blog_data)
        
        # Serve stream directly
        response = FileResponse(
            docx_stream,
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = f'attachment; filename="blog_{blog_post.id}.docx"'
        return response
        
    except Exception as e:
        print(f"Error generating DOCX export: {e}")
        return HttpResponse(f"Error generating DOCX: {str(e)}", status=500)

def export_blog_json(request, blog_id):
    """Download blog as Pinterest JSON (Generated on-demand)."""
    import json as json_module
    from .services.blog_generator import BlogGeneratorService
    
    blog_post = get_object_or_404(BlogPost, pk=blog_id)
    
    try:
        # Use stored structured_content if available
        if blog_post.structured_content:
            json_data = blog_post.structured_content
        else:
            # Fallback re-generation (shouldn't be needed after migration)
            generator = BlogGeneratorService()
            blog_data = {
                'topic': blog_post.topic,
                'intro': blog_post.intro,
                'conclusion': blog_post.conclusion,
                'thumbnail_url': blog_post.thumbnail_url,
                'sections': [
                    {
                        'title': section.title,
                        'description': section.description,
                        'image_url': section.image_url
                    }
                    for section in blog_post.sections.all()
                ]
            }
            json_data = generator.create_pinterest_json(blog_data)
        
        # Serve JSON directly
        response = HttpResponse(
            json_module.dumps(json_data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="blog_{blog_post.id}.json"'
        return response
        
    except Exception as e:
        print(f"Error serving JSON export: {e}")
        return HttpResponse(f"Error serving JSON: {str(e)}", status=500)
