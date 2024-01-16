import json
from urllib.parse import quote

import boto3
import humanize
from boto3.session import Session
from botocore.exceptions import NoCredentialsError
from fastapi import APIRouter, Header, HTTPException, Path, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import (
    JSONResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
)
from fastapi_versioning import version

from src.config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, BUCKET_NAME
from src.config import LIMITER as limiter
from src.config import RATE_LIMIT_PER_MIN

router = APIRouter(prefix="/s3", tags=["S3"])

AWS_REGION = "us-east-1"
session = Session()
s3 = session.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)
paginator = s3.get_paginator("list_objects_v2")


@router.get("/files/")
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def list_s3_files(
    request: Request,
    folder: str = Query(default="/HDX"),
    prettify: bool = Query(
        default=False, description="Display size & date in human-readable format"
    ),
):
    bucket_name = BUCKET_NAME
    folder = folder.strip("/")
    prefix = f"{folder}/"

    try:
        # Use list_objects_v2 directly for pagination
        page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

        async def generate():
            first_item = True
            yield "["

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
                    if not first_item:
                        yield ","
                    else:
                        first_item = False
                    yield json.dumps(item_dict, default=str)

            yield "]"

        return StreamingResponse(content=generate(), media_type="application/json")

    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not available")


async def check_object_existence(bucket_name, file_path):
    """Async function to check object existence"""
    try:
        s3.head_object(Bucket=bucket_name, Key=file_path)
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not available")
    except Exception as e:
        raise HTTPException(
            status_code=404, detail=f"File or folder not found: {file_path}"
        )


async def read_meta_json(bucket_name, file_path):
    """Async function to read from meta json"""
    try:
        response = s3.get_object(Bucket=bucket_name, Key=file_path)
        content = json.loads(response["Body"].read())
        return content
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error reading meta.json: {str(e)}"
        )


@router.head("/get/{file_path:path}")
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def head_s3_file(
    request: Request,
    file_path: str = Path(..., description="The path to the file or folder in S3"),
):
    bucket_name = BUCKET_NAME
    encoded_file_path = quote(file_path.strip("/"))
    try:
        response = s3.head_object(Bucket=bucket_name, Key=encoded_file_path)
        return Response(
            status_code=200,
            headers={
                "Last-Modified": response["LastModified"].strftime(
                    "%a, %d %b %Y %H:%M:%S GMT"
                ),
                "Content-Length": str(response["ContentLength"]),
            },
        )
    except Exception as e:
        if e.response["Error"]["Code"] == "404":
            return Response(status_code=404)
        else:
            raise HTTPException(status_code=500, detail=f"AWS Error: {str(e)}")


@router.get("/get/{file_path:path}")
@limiter.limit(f"{RATE_LIMIT_PER_MIN}/minute")
@version(1)
async def get_s3_file(
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

    await check_object_existence(bucket_name, encoded_file_path)

    if read_meta and file_path.lower().endswith(".json"):
        # Read and deliver the content of meta.json
        content = await read_meta_json(bucket_name, file_path)
        return JSONResponse(content=jsonable_encoder(content))

    # If not reading meta.json, generate a presigned URL
    presigned_url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket_name, "Key": encoded_file_path},
        ExpiresIn=expiry,
    )

    return RedirectResponse(presigned_url)
