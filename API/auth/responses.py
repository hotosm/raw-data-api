from fastapi import HTTPException
from pydantic import BaseModel

# Define common error responses
common_error_responses = {
    403: {"description": "Forbidden", "model": HTTPException},
    404: {"description": "Not Found", "model": HTTPException},
    500: {"description": "Internal Server Error", "model": HTTPException},
}

# Define shared error response models
class ErrorResponse(BaseModel):
    detail: str

# Add a default response model for error responses
for status_code in common_error_responses:
    if "model" not in common_error_responses[status_code]:
        common_error_responses[status_code]["model"] = ErrorResponse

error_responses_with_examples = {
    403: {"content": {"application/json": {"example": {"message": "Access forbidden"}}}},
    404: {"content": {"application/json": {"example": {"error": "Not Found"}}}},
    500: {"content": {"application/json": {"example": {"error": "Internal Server Error"}}}},
}
