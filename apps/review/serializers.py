from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.review.models import UnifiedReviewComment
from apps.contrib.serializers import MetaInformationSerializerMixin

NOT_ALLOWED_TO_REVIEW = _('You are not allowed to review this entry.')


class UnifiedReviewCommentSerializer(MetaInformationSerializerMixin, serializers.ModelSerializer):
    """
    Class: UnifiedReviewCommentSerializer

    This class is used to serialize and validate UnifiedReviewComment instances.

    Inherits From:
    - MetaInformationSerializerMixin
    - serializers.ModelSerializer

    Attributes:
    - model: The model that the serializer is based on (UnifiedReviewComment)
    - fields: The fields that should be serialized (event, geo_location, figure, field, comment_type, geo_location, comment)

    Methods:
    1. validate_comment(comment: str) -> str:
       - Validates and sanitizes the comment input
       - Parameters:
         - comment (str): The comment input to be validated
       - Returns:
         - str: The validated comment

    2. _validate_comment_without_reviews(attrs: dict) -> None:
       - Validates that the comment is not empty if the comment type is not "GREEN"
       - Raises:
         - serializers.ValidationError: If the comment is empty and the comment type is not "GREEN"
       - Parameters:
         - attrs (dict): The attributes dictionary containing the comment and comment_type

    3. validate(attrs: dict) -> dict:
       - Validates the attributes of the serializer
       - Calls _validate_comment_without_reviews(attrs) method to validate the comment
       - Returns the validated attributes
       - Parameters:
         - attrs (dict): The attributes dictionary to be validated
       - Returns:
         - dict: The validated attributes
    """
    class Meta:
        model = UnifiedReviewComment
        fields = (
            'event', 'geo_location', 'figure', 'field', 'comment_type', 'geo_location', 'comment',
        )

    def validate_comment(self, comment: str):
        # we will store null for empty bodies
        if not comment or not comment.strip():
            return None
        return comment

    def _validate_comment_without_reviews(self, attrs):
        comment = attrs.get('comment')
        comment_type = attrs.get('comment_type')
        if (not comment or not comment.strip()) and comment_type != UnifiedReviewComment.REVIEW_COMMENT_TYPE.GREEN:
            raise serializers.ValidationError(dict(comment=_('Comment is empty.')))

    def validate(self, attrs) -> dict:
        self._validate_comment_without_reviews(attrs)
        return super().validate(attrs)
