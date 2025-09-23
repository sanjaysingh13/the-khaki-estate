"""
Gallery forms for photo upload and comment functionality.

This module contains Django forms for the Gallery feature, including:
- Photo upload form with caption
- Comment form for photo interactions
- Like/unlike functionality (handled via AJAX)
"""

from django import forms
from django.core.exceptions import ValidationError

from .models import GalleryPhoto, GalleryComment


class GalleryPhotoForm(forms.ModelForm):
    """
    Form for uploading photos to the gallery.
    
    This form handles photo uploads with captions and includes
    validation for file size and image format.
    """
    
    class Meta:
        model = GalleryPhoto
        fields = ['photo', 'caption']
        widgets = {
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'id': 'id_photo'
            }),
            'caption': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add a caption for your photo (optional)',
                'id': 'id_caption'
            })
        }
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the form with user context.
        
        Args:
            *args: Standard form arguments
            **kwargs: Additional keyword arguments
        """
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes and validation attributes
        self.fields['photo'].widget.attrs.update({
            'class': 'form-control',
            'required': True
        })
        self.fields['caption'].widget.attrs.update({
            'class': 'form-control',
            'maxlength': '500'
        })
    
    def clean_photo(self):
        """
        Validate the uploaded photo.
        
        Performs validation for:
        - File size (max 10MB)
        - Image format (JPEG, PNG, GIF, WebP)
        - File extension
        
        Returns:
            Cleaned photo file
            
        Raises:
            ValidationError: If photo doesn't meet requirements
        """
        photo = self.cleaned_data.get('photo')
        
        if not photo:
            raise ValidationError("Please select a photo to upload.")
        
        # Check file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        if photo.size > max_size:
            raise ValidationError(
                f"Photo size must be less than 10MB. "
                f"Current size: {photo.size / (1024*1024):.1f}MB"
            )
        
        # Check file extension
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        file_extension = photo.name.lower().split('.')[-1]
        if f'.{file_extension}' not in allowed_extensions:
            raise ValidationError(
                f"Invalid file format. Allowed formats: {', '.join(allowed_extensions)}"
            )
        
        return photo
    
    def clean_caption(self):
        """
        Validate and clean the caption text.
        
        Returns:
            Cleaned caption text
        """
        caption = self.cleaned_data.get('caption', '').strip()
        
        # Limit caption length
        if len(caption) > 500:
            raise ValidationError("Caption must be 500 characters or less.")
        
        return caption
    
    def save(self, commit=True):
        """
        Save the photo with the current user as author.
        
        Args:
            commit: Whether to commit to database
            
        Returns:
            GalleryPhoto instance
        """
        photo = super().save(commit=False)
        
        if self.user:
            photo.author = self.user
        
        if commit:
            photo.save()
        
        return photo


class GalleryCommentForm(forms.ModelForm):
    """
    Form for commenting on gallery photos.
    
    This form handles both top-level comments and replies to existing comments.
    """
    
    class Meta:
        model = GalleryComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Write a comment...',
                'id': 'id_comment_content'
            })
        }
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the comment form with user and photo context.
        
        Args:
            *args: Standard form arguments
            **kwargs: Additional keyword arguments
        """
        self.user = kwargs.pop('user', None)
        self.photo = kwargs.pop('photo', None)
        self.parent_comment = kwargs.pop('parent_comment', None)
        super().__init__(*args, **kwargs)
        
        # Update placeholder based on whether it's a reply
        if self.parent_comment:
            self.fields['content'].widget.attrs['placeholder'] = f"Reply to {self.parent_comment.author.get_full_name()}..."
    
    def clean_content(self):
        """
        Validate and clean the comment content.
        
        Returns:
            Cleaned comment content
            
        Raises:
            ValidationError: If content doesn't meet requirements
        """
        content = self.cleaned_data.get('content', '').strip()
        
        if not content:
            raise ValidationError("Comment cannot be empty.")
        
        # Limit comment length
        if len(content) > 1000:
            raise ValidationError("Comment must be 1000 characters or less.")
        
        # Basic profanity filter (can be enhanced)
        inappropriate_words = ['spam', 'advertisement', 'promotion']
        content_lower = content.lower()
        for word in inappropriate_words:
            if word in content_lower:
                raise ValidationError("Please keep comments appropriate and relevant.")
        
        return content
    
    def save(self, commit=True):
        """
        Save the comment with the current user as author.
        
        Args:
            commit: Whether to commit to database
            
        Returns:
            GalleryComment instance
        """
        comment = super().save(commit=False)
        
        if self.user:
            comment.author = self.user
        
        if self.photo:
            comment.photo = self.photo
        
        if self.parent_comment:
            comment.parent = self.parent_comment
        
        if commit:
            comment.save()
        
        return comment


class GalleryPhotoEditForm(forms.ModelForm):
    """
    Form for editing existing gallery photos (caption only).
    
    This form allows users to edit the caption of their own photos.
    """
    
    class Meta:
        model = GalleryPhoto
        fields = ['caption']
        widgets = {
            'caption': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Edit caption...',
                'id': 'id_edit_caption'
            })
        }
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the edit form with user context.
        
        Args:
            *args: Standard form arguments
            **kwargs: Additional keyword arguments
        """
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_caption(self):
        """
        Validate and clean the caption text.
        
        Returns:
            Cleaned caption text
        """
        caption = self.cleaned_data.get('caption', '').strip()
        
        # Limit caption length
        if len(caption) > 500:
            raise ValidationError("Caption must be 500 characters or less.")
        
        return caption
    
    def save(self, commit=True):
        """
        Save the updated caption.
        
        Args:
            commit: Whether to commit to database
            
        Returns:
            GalleryPhoto instance
        """
        photo = super().save(commit=False)
        
        # Only allow users to edit their own photos
        if self.user and photo.author != self.user:
            raise ValidationError("You can only edit your own photos.")
        
        if commit:
            photo.save()
        
        return photo
