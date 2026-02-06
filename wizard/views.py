from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, TemplateView, View
from django.urls import reverse
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from .models import Project, TrendKeyword, Suggestion, ExpandedKeyword, Content, ArticleIdea, PinIdea

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
            return redirect('wizard:export', project_id=project_id)
        
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
