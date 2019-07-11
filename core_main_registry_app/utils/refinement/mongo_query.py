"""
Mongo query creation for the refinements.
"""

import logging
import operator
from functools import reduce

from django.db.models import Q

from core_main_app.commons import exceptions as exceptions
from core_main_registry_app.commons.constants import DataStatus
from core_main_registry_app.components.category import api as category_api
from core_main_registry_app.components.refinement import api as refinement_api
from core_main_registry_app.components.template import api as template_registry_api
from core_main_registry_app.constants import PATH_STATUS

logger = logging.getLogger("core_main_registry_app.utils.refinement.mongo_query")


def build_refinements_query(refinements):
    """ Build the refinements query.

    Args:
        refinements:

    Returns:

    """
    or_queries = []
    and_query = {}

    try:
        # transform the refinement in mongo query
        for refinement in refinements:
            queries = dict()
            in_queries = {}
            # For each category in the refinement
            for category_id in refinement:
                try:
                    # Get category
                    category = category_api.get_by_id(category_id)
                    dot_notation = category.path
                    value = category.value
                    # If dot notation already exists, append to the dict
                    if dot_notation in queries:
                        queries[dot_notation].append(value)
                    # Create a dict with the dot notation as the key
                    else:
                        queries[dot_notation] = [value]
                except (exceptions.DoesNotExist, Exception) as e:
                    logger.warning("Impossible to find the category ({0}): {1}."
                                   .format(str(len(category_id)), str(e)))

            for query in queries:
                # Create the query with $in
                key = query
                values = ({'$in': queries[query]})
                in_queries[key] = values
                # Case of the element has attributes
                in_queries[key + ".#text"] = values

            if len(in_queries) > 0:
                # $or between categories belonging to the same refinement
                or_queries.append({'$or': [{x: in_queries[x]} for x in in_queries]})

        if len(or_queries) > 0:
            # $and between refinements
            and_query = {'$and': or_queries}

        return and_query
    except Exception as e:
        logger.error("Something went wrong during the creation of the refinement query. Search "
                     "won't be refined: {0}.".format(str(e)))
        return {}


def get_refinement_selected_values_from_query(query):
    """ get the refinement selected values from a json query

    Args:
        query:

    Returns:
        {
            refinement_name: [cat_id, cat_id ,cat_id],
            refinement_name: [cat_id, cat_id ,cat_id],
            refinement_name: [cat_id, cat_id ,cat_id],
        }

    """
    # create a list of key (category), value_list (selected values)
    category_values_list = {}
    # if the query have the key '$and', there is refinement selected
    if '$and' in query:
        for element_or in query['$and']:
            # go through all '$or' => where refinement are
            for element in element_or['$or']:
                for key, value in list(element.items()):
                    # we only want path which does not contain '#text' at the end of it
                    if not key.endswith('#text'):
                        for selected_value in value['$in']:
                            # then we build our list and we don't want categories ending with '__category'
                            if not selected_value.endswith('__category'):
                                if key in category_values_list:
                                    category_values_list[key].append(selected_value)
                                else:
                                    category_values_list.update({key: [selected_value]})

    # get global template.
    template = template_registry_api.get_current_registry_template()
    # get refinements.
    refinements = refinement_api.get_all_filtered_by_template_hash(template.hash)
    refinements_ids = [x.id for x in refinements]
    # get all category.
    q_list = []
    for key, values in list(category_values_list.items()):
        # prepare the query
        q_list.append(Q(path=key) & Q(refinement_id__in=refinements_ids) & Q(value__in=values))

    return_value = {}
    # if refinement are found, we build the structure
    if len(q_list) > 0:
        categories = category_api.get_all().filter((reduce(operator.or_, q_list)))
        # now we have to build a list of {refinement name: category ids, }
        for category in categories:
            key = category.refinement.slug
            display_name = category.refinement.name
            if key in return_value:
                return_value[key][display_name].append({"id": category.id, "value": category.value})
            else:
                return_value.update({key: {display_name: [{"id": category.id, "value": category.value}]}})
    # return the structure
    return return_value


def add_not_deleted_status_criteria():
    """Adds a criteria on status. Status should not be deleted.

        Returns:
            Criteria

    """
    return {PATH_STATUS: {'$ne': DataStatus.DELETED}}
