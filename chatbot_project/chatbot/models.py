from django.db import models
import uuid

class TextContent(models.Model):
    url = models.URLField(max_length=2048)
    text = models.TextField()
    embedding_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ImageContent(models.Model):
    url = models.URLField(max_length=2048)
    description = models.TextField(null=True)
    description_ocr = models.TextField(null=True)
    description_cap = models.TextField(null=True)
    format = models.CharField(max_length=50, null=True)
    sibling_info = models.TextField(null=True)
    embedding_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Downloadables(models.Model):
    url = models.URLField(max_length=2048)
    filename = models.CharField(max_length=255, null=True)
    format = models.CharField(max_length=50, null=True)
    description = models.TextField(null=True)
    source_url = models.URLField(max_length=2048, null=True)
    embedding_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# class VideoContent(models.Model):
#     pass

# class TableContent(models.Model):
#     pass

# class DepartmentalData(models.Model):
#     pass
