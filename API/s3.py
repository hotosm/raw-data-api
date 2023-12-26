import json
from urllib.parse import quote

import boto3
import humanize
from botocore.exceptions import NoCredentialsError
from fastapi import APIRouter, HTTPException, Path, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi_versioning import version

from src.config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, BUCKET_NAME
from src.config import LIMITER as limiter
from src.config import RATE_LIMIT_PER_MIN

router = APIRouter(prefix="/s3", tags=["S3"])


AWS_REGION = "us-east-1"

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)
paginator = s3.get_paginator("list_objects_v2")


@router.get("/files/")
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
def list_s3_files(
    request: Request,
    folder: str = Query(default="/HDX"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, le=100, description="Items per page"),
    prettify: bool = Query(
        default=False, description="Display size & date in human-readable format"
    ),
):
    bucket_name = BUCKET_NAME
    folder = folder.strip("/")
    prefix = f"{folder}/"

    result = []

    try:
        # Create a paginator for list_objects_v2
        page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

        # Paginate the results
        start_index = (page - 1) * page_size
        end_index = start_index + page_size

        for response in page_iterator:
            contents = response.get("Contents", [])

            for item in contents:
                size = item["Size"]
                last_modified = item["LastModified"].strftime("%Y-%m-%dT%H:%M:%SZ")
                if prettify:
                    last_modified = humanize.naturaldate(item["LastModified"])
                    size = humanize.naturalsize(size)

                item_dict = {
                    "Key": item["Key"],
                    "LastModified": last_modified,
                    "Size": size,
                }
                result.append(item_dict)

        paginated_result = result[start_index:end_index]

        # Calculate total number of pages
        total_pages = -(-len(result) // page_size)  # Ceiling division

        # Include pagination information in the response
        response_data = {
            "current_page": page,
            "total_pages": total_pages,
            "items_per_page": page_size,
            "items": paginated_result,
        }

        return JSONResponse(content=jsonable_encoder(response_data))

    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not available")


@router.get("/get/{file_path:path}")
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
def get_s3_file(
    request: Request,
    file_path: str = Path(..., description="The path to the file or folder in S3"),
    expiry: int = Query(
        default=3600,
        description="Expiry time for the presigned URL in seconds (default: 1 hour)",
        gt=60 * 10,
        le=3600 * 12 * 7,
    ),
    read_meta: bool = Query(
        default=True,
        description="Whether to read and deliver the content of .json file",
    ),
):
    bucket_name = BUCKET_NAME
    file_path = file_path.strip("/")
    encoded_file_path = quote(file_path)

    try:
        # Check if the file or folder exists
        s3.head_object(Bucket=bucket_name, Key=encoded_file_path)
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not available")
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=404, detail=f"File or folder not found: {file_path}"
        )

    if read_meta and file_path.lower().endswith(".json"):
        # Read and deliver the content of meta.json
        try:
            response = s3.get_object(Bucket=bucket_name, Key=file_path)
            content = json.loads(response["Body"].read())
            return JSONResponse(content=jsonable_encoder(content))
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error reading meta.json: {str(e)}"
            )

    # If not reading meta.json, generate a presigned URL
    presigned_url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket_name, "Key": file_path},
        ExpiresIn=expiry,
    )

    return JSONResponse(content=jsonable_encoder({"download_link": presigned_url}))
