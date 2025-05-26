import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ScrapeRequestSerializer
from .tasks import scrape_portal_data
from celery.result import AsyncResult
from datetime import datetime

logger = logging.getLogger(__name__)

class ScrapePersonAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ScrapeRequestSerializer(data=request.data)
        if serializer.is_valid():
            identifier = serializer.validated_data['identifier']
            search_filter = serializer.validated_data.get('search_filter')

            logger.info(f"API received request for identifier: {identifier}, filter: {search_filter}")

            task = scrape_portal_data.delay(identifier, search_filter)
            
            logger.info(f"Celery task {task.id} dispatched for {identifier}.")

            try:
                task_result = task.get(timeout=180)

                if task.state == 'SUCCESS':
                    logger.info(f"Task {task.id} completed successfully. Result: {task_result}")
                    return Response(
                        {"task_id": task.id, "timestamp": datetime.now().isoformat(), "result": task_result},
                        status=status.HTTP_200_OK
                    )
                else:
                    logger.error(f"Task {task.id} failed or had an unexpected state: {task.state}. Result: {task_result}")
                    return Response(
                        {"error": "Task did not complete successfully", "task_id": task.id, "status": task.state, "details": task_result},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            except TimeoutError:
                logger.warning(f"Timeout waiting for Celery task {task.id} to complete.")
                return Response(
                    {"error": "Request timed out waiting for scraping to complete.", "task_id": task.id},
                    status=status.HTTP_408_REQUEST_TIMEOUT
                )
            except Exception as e:
                logger.error(f"An error occurred while processing task {task.id}: {e}", exc_info=True)
                return Response(
                    {"error": "An unexpected error occurred.", "task_id": task.id, "details": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        logger.warning(f"Invalid request data: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
