""" Category model
"""


from django.db import models
from django_extensions.db.fields import AutoSlugField
from mptt.models import MPTTModel, TreeForeignKey

from core_main_app.commons import exceptions as exceptions


class Category(MPTTModel):
    parent = TreeForeignKey('self', null=True, on_delete=models.CASCADE, blank=True,
                            related_name='children')
    name = models.CharField(max_length=50)
    slug = AutoSlugField(max_length=50, overwrite=True, populate_from='name')
    path = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    refinement = models.ForeignKey('Refinement', on_delete=models.CASCADE)

    class MPTTMeta(object):
        verbose_name_plural = "categories"
        unique_together = (("name", "slug", "parent"), )
        ordering = ("tree_id", "lft")

    @staticmethod
    def get_all_filtered_by_refinement_id(refinement_id):
        """ Get all categories filtered by refinement id.

        Parameters:
                refinement_id:

        Returns: Category collection

        """
        return Category.objects.all().filter(refinement=refinement_id)

    @staticmethod
    def create_and_save(name, path, value, parent, refinement):
        """ Create and save a category.

        Args:
            name:
            path:
            value:
            parent:
            refinement:

        Returns:

        """
        return Category.objects.create(name=name, path=path, value=value, parent=parent,
                                       refinement=refinement)

    @staticmethod
    def get_by_id(category_id):
        """ Get category by its id.

        Parameters:
            category_id:

        Returns:
            Category object

        """
        try:
            return Category.objects.get(pk=category_id)
        except Category.DoesNotExist as e:
            raise exceptions.DoesNotExist(str(e))
        except Exception as ex:
            raise exceptions.ModelError(str(ex))

    @staticmethod
    def get_all_categories_by_parent_slug_and_refinement_id(parent_slug, refinement_id):
        """ Get all categories by parent_slug and refinement.

        Args:
            parent_slug:
            refinement_id:

        Returns:

        """
        try:
            return Category.objects.get(slug__startswith=parent_slug,
                                        refinement_id=refinement_id).get_family()
        except Category.DoesNotExist as e:
            raise exceptions.DoesNotExist(str(e))
        except Exception as ex:
            raise exceptions.ModelError(str(ex))

    @staticmethod
    def get_all():
        """ Get all categories.

        Returns: Category collection

        """
        return Category.objects.all()
