""" REST views for the registry Data API
"""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core_main_app.commons import exceptions
from core_main_app.components.data import api as data_api
from core_main_app.rest.data.views import DataDetail
from core_main_app.utils.access_control.exceptions import AccessControlError
from core_main_registry_app.components.data import api as registry_data_api


@api_view(['PATCH'])
def publish_data(request, pk):
    """ Publish a data

    Args:

        request: HTTP request
        pk: ObjectId

    Returns:

        - code: 200
          content: Publication succeed
        - code: 403
          content: Authentication error
        - code: 404
          content: Object was not found
        - code: 500
          content: Internal server error
    """
    try:
        # Get data
        data_object = data_api.get_by_id(pk, request.user)

        # Publish
        registry_data_api.publish(data_object, request.user)

        # Return response
        return Response(status=status.HTTP_200_OK)
    except exceptions.DoesNotExist:
        content = {'message': 'Data not found.'}
        return Response(content, status=status.HTTP_404_NOT_FOUND)
    except AccessControlError as ace:
        content = {'message': str(ace)}
        return Response(content, status=status.HTTP_403_FORBIDDEN)
    except Exception as api_exception:
        content = {'message': str(api_exception)}
        return Response(content, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DataDetailRegistry(DataDetail):
    """ Retrieve or update a data
    """

    def delete(self, request, pk):
        """ Data cannot be deleted

        Args:

            request: HTTP request
            pk: ObjectId

        Returns:

            - code: 403
              content: Data cannot be deleted
        """
        content = {'message': 'Data cannot be deleted.'}
        return Response(content, status=status.HTTP_403_FORBIDDEN)

    def patch(self, request, pk):
        """ Data cannot be updated

        Args:

            request: HTTP request
            pk: ObjectId

        Returns:

            - code: 403
              content: Data cannot be updated
        """
        content = {'message': 'Data cannot be updated.'}
        return Response(content, status=status.HTTP_403_FORBIDDEN)
