from .models import TextContent 

def fetch_and_concatenate_text(embedding_ids):
    texts = TextContent.objects.filter(embedding_id__in=embedding_ids).values_list('text', flat=True)
    concatenated_text = " ".join(texts)
    return concatenated_text 