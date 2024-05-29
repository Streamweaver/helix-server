from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ReportGeneration


@receiver(post_save, sender=ReportGeneration)
def update_report_reviewer_status(sender, instance, created, **kwargs):
    """
    Updates the reviewer status of a report after it is generated or updated.

    Parameters:
    - sender: The sender of the signal.
    - instance: The instance of the ReportGeneration model that triggered the signal.
    - created: A boolean indicating whether the instance is newly created.
    - **kwargs: Additional keyword arguments.

    Returns:
    None
    """
    if created:
        instance.report.is_signed_off = False
        instance.report.is_signed_off_by = None
        instance.report.save(update_fields=['is_signed_off', 'is_signed_off_by'])
    else:
        if instance.is_signed_off:
            instance.report.is_signed_off = True
            instance.report.is_signed_off_by = instance.is_signed_off_by
            instance.report.save(update_fields=['is_signed_off', 'is_signed_off_by'])
