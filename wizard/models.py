from django.db import models

class Project(models.Model):
    name = models.CharField(max_length=200)
    niche = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def get_current_stage(self):
        """Returns the current stage of the project workflow."""
        if self.article_ideas.exists() or self.pin_ideas.exists():
            return 'export'
        elif self.expanded_keywords.exists():
            return 'content'
        elif self.suggestions.exists():
            return 'expansion'
        elif self.trends.filter(selected=True).exists():
            return 'suggestions'
        elif self.trends.exists():
            return 'review'
        else:
            return 'trends'
    
    def get_stage_display(self):
        """Returns a human-readable stage name."""
        stage = self.get_current_stage()
        stages = {
            'trends': 'Fetch Trends',
            'review': 'Review Keywords',
            'suggestions': 'Fetch Suggestions',
            'expansion': 'Expand Keywords',
            'content': 'Generate Content',
            'export': 'Export Ready'
        }
        return stages.get(stage, 'Unknown')
    
    def get_resume_url(self):
        """Returns the URL to resume work on this project."""
        from django.urls import reverse
        stage = self.get_current_stage()
        url_names = {
            'trends': 'wizard:trend_fetch',
            'review': 'wizard:keyword_review',
            'suggestions': 'wizard:suggestion_fetch',
            'expansion': 'wizard:expansion',
            'content': 'wizard:content_gen',
            'export': 'wizard:export'
        }
        url_name = url_names.get(stage, 'wizard:trend_fetch')
        return reverse(url_name, kwargs={'project_id': self.id})
    
    def get_stats(self):
        """Returns project statistics."""
        return {
            'trends_count': self.trends.count(),
            'selected_keywords': self.trends.filter(selected=True).count(),
            'suggestions_count': self.suggestions.count(),
            'expanded_count': self.expanded_keywords.count(),
            'articles_count': self.article_ideas.count(),
            'pins_count': self.pin_ideas.count(),
            'total_content': self.article_ideas.count() + self.pin_ideas.count()
        }

class TrendKeyword(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='trends')
    keyword = models.CharField(max_length=255)
    trend_score = models.IntegerField(default=0)
    selected = models.BooleanField(default=False)
    
    # Metadata from scrape (optional)
    volume = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"{self.keyword} ({self.project.name})"

class Suggestion(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='suggestions')
    base_keyword = models.CharField(max_length=255) # The trend keyword this came from
    suggestion = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.base_keyword} -> {self.suggestion}"

class ExpandedKeyword(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='expanded_keywords')
    base_keyword = models.CharField(max_length=255)
    keyword = models.CharField(max_length=255) # The combined/final keyword
    intent = models.CharField(max_length=50, blank=True) # Ideas, Shopping, etc.
    score = models.IntegerField(default=0)
    selected = models.BooleanField(default=True)

    def __str__(self):
        return self.keyword

class Content(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='content')
    keyword = models.CharField(max_length=255)
    article_title = models.CharField(max_length=255, default="", blank=True)
    title = models.CharField(max_length=255) # Pin Title
    description = models.TextField(blank=True) # Pin Description
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class ArticleIdea(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='article_ideas')
    expanded_keyword = models.ForeignKey(ExpandedKeyword, on_delete=models.CASCADE, related_name='article_ideas')
    title = models.CharField(max_length=500)
    hook = models.CharField(max_length=500, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class PinIdea(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='pin_ideas')
    expanded_keyword = models.ForeignKey(ExpandedKeyword, on_delete=models.CASCADE, related_name='pin_ideas')
    title = models.CharField(max_length=500)
    description = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
