template_content = '''{% if trends %}
<p class="mb-2">Found {{ trends|length }} trends. Select keywords to proceed:</p>
<div class="list-group shadow-sm" style="max-height: 400px; overflow-y: auto;">
{% for trend in trends %}
<label class="list-group-item d-flex gap-3">
<input class="form-check-input" type="checkbox" name="selected_trends" value="{{ trend.id }}"{% if trend.selected %} checked{% endif %}>
<span class="pt-1"><strong>{{ trend.keyword }}</strong></span>
</label>
{% endfor %}
</div>
{% else %}
<div class="text-center py-5 text-muted"><p>No trends found yet. Click Fetch Trends above.</p></div>
{% endif %}
'''

with open('wizard/templates/wizard/partials/trend_list.html', 'w', encoding='utf-8') as f:
    f.write(template_content)

print("Template written successfully!")
