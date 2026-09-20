import csv
import json
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, BackgroundTasks
from sqlalchemy.orm import Session

from backend.db.session import get_db, SessionLocal
from backend.models.product import Product
from backend.models.sales import SalesTransaction
from backend.models.upload import UploadJob, ValidationResult
from backend.models.demand import DailyProductDemand

router = APIRouter()

def background_post_process_upload(upload_id: int):
    """Background task to aggregate new sales into daily_product_demand."""
    db: Session = SessionLocal()
    try:
        job = db.query(UploadJob).filter(UploadJob.id == upload_id).first()
        if job and job.status == "PROCESSING":
            job.status = "COMPLETED"
            job.completed_at = datetime.utcnow()
            db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()

@router.get("/test")
def upload_test():
    return {
        "message": "Upload API is working"
    }


REQUIRED_COLUMNS = {
    "date_",
    "city_name",
    "order_id",
    "cart_id",
    "dim_customer_key",
    "procured_quantity",
    "unit_selling_price",
    "total_discount_amount",
    "product_id",
    "total_weighted_landing_price",
}

IGNORED_COLUMNS = {
    "Unnamed: 0",
    "Unnamed: 0.1",
}


def parse_date(value):
    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%Y/%m/%d",
        "%d/%m/%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    return None


def parse_float(value):
    if value is None:
        return None

    value = str(value).strip()

    if value == "":
        return None

    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def get_file_size(file: UploadFile):
    try:
        current_position = file.file.tell()

        file.file.seek(0, 2)
        size = file.file.tell()

        file.file.seek(current_position)

        return size

    except Exception:
        return None


@router.post("/sales")
def upload_sales(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported.",
        )

    file_size = get_file_size(file)

    upload_job = UploadJob(
        filename=file.filename,
        file_type="sales",
        file_size_bytes=file_size,
        status="PROCESSING",
        total_rows=0,
        processed_rows=0,
    )

    db.add(upload_job)
    db.commit()
    db.refresh(upload_job)

    try:

      

        file.file.seek(0)

        content = file.file.read()

        try:
            text = content.decode("utf-8-sig")

        except UnicodeDecodeError:

            upload_job.status = "FAILED"
            upload_job.error_summary = (
                "CSV must use UTF-8 encoding."
            )

            db.commit()

            raise HTTPException(
                status_code=400,
                detail="CSV must use UTF-8 encoding.",
            )

    

        reader = csv.DictReader(
            text.splitlines()
        )

        actual_columns = set(
            reader.fieldnames or []
        )



        missing_columns = (
            REQUIRED_COLUMNS - actual_columns
        )

        if missing_columns:

            validation = ValidationResult(
                upload_id=upload_job.id,
                check_name="required_columns",
                status="FAIL",
                details=json.dumps(
                    {
                        "missing_columns": sorted(
                            missing_columns
                        )
                    }
                ),
            )

            db.add(validation)

            upload_job.status = "FAILED"

            upload_job.error_summary = (
                f"Missing required columns: "
                f"{sorted(missing_columns)}"
            )

            db.commit()

            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Missing required columns.",
                    "missing_columns": sorted(
                        missing_columns
                    ),
                },
            )

     

        product_ids = {
            product_id
            for (product_id,) in db.query(
                Product.product_id
            ).all()
        }

 

        total_rows = 0
        valid_rows = 0

        missing_dates = 0
        invalid_dates = 0

        missing_product_ids = 0
        invalid_product_ids = 0
        unmatched_product_ids = 0

        missing_quantity = 0
        invalid_quantity = 0
        negative_quantity = 0

        missing_price = 0
        invalid_price = 0
        negative_price = 0

        missing_discount = 0
        invalid_discount = 0
        negative_discount = 0

        duplicate_rows = 0

        unmatched_products = set()

        seen_rows = set()

     

        batch = []

        BATCH_SIZE = 1000

     

        for row in reader:

            total_rows += 1

         
            for column in IGNORED_COLUMNS:
                row.pop(column, None)

            errors = []

           

            date_value = (
                row.get("date_") or ""
            ).strip()

            if not date_value:

                missing_dates += 1

                errors.append(
                    "missing_date"
                )

                parsed_date = None

            else:

                parsed_date = parse_date(
                    date_value
                )

                if parsed_date is None:

                    invalid_dates += 1

                    errors.append(
                        "invalid_date"
                    )

            

            product_value = (
                row.get("product_id") or ""
            ).strip()

            if not product_value:

                missing_product_ids += 1

                errors.append(
                    "missing_product_id"
                )

                product_id = None

            else:

                try:

                    product_id = int(
                        float(product_value)
                    )

                except (ValueError, TypeError):

                    product_id = None

                    invalid_product_ids += 1

                    errors.append(
                        "invalid_product_id"
                    )


            if product_id is not None:

                if product_id not in product_ids:

                    unmatched_product_ids += 1

                    unmatched_products.add(
                        product_id
                    )

                    errors.append(
                        "unmatched_product_id"
                    )


            quantity_value = (
                row.get("procured_quantity") or ""
            ).strip()

            if not quantity_value:

                missing_quantity += 1

                errors.append(
                    "missing_quantity"
                )

                quantity = None

            else:

                quantity = parse_float(
                    quantity_value
                )

                if quantity is None:

                    invalid_quantity += 1

                    errors.append(
                        "invalid_quantity"
                    )

                elif quantity < 0:

                    negative_quantity += 1

                    errors.append(
                        "negative_quantity"
                    )


            price_value = (
                row.get("unit_selling_price") or ""
            ).strip()

            if not price_value:

                missing_price += 1

                errors.append(
                    "missing_price"
                )

                price = None

            else:

                price = parse_float(
                    price_value
                )

                if price is None:

                    invalid_price += 1

                    errors.append(
                        "invalid_price"
                    )

                elif price < 0:

                    negative_price += 1

                    errors.append(
                        "negative_price"
                    )

       

            discount_value = (
                row.get("total_discount_amount") or ""
            ).strip()

            if not discount_value:

                missing_discount += 1

                errors.append(
                    "missing_discount"
                )

                discount = None

            else:

                discount = parse_float(
                    discount_value
                )

                if discount is None:

                    invalid_discount += 1

                    errors.append(
                        "invalid_discount"
                    )

                elif discount < 0:

                    negative_discount += 1

                    errors.append(
                        "negative_discount"
                    )

          

            duplicate_key = tuple(
                row.get(column)
                for column in sorted(
                    REQUIRED_COLUMNS
                )
            )

            if duplicate_key in seen_rows:

                duplicate_rows += 1

                errors.append(
                    "duplicate_row"
                )

            else:

                seen_rows.add(
                    duplicate_key
                )

          

            if not errors:

                transaction = SalesTransaction(

                    upload_id=upload_job.id,

                    date_=parsed_date,

                    city_name=row.get(
                        "city_name"
                    ),

                    order_id=row.get(
                        "order_id"
                    ),

                    cart_id=row.get(
                        "cart_id"
                    ),

                    dim_customer_key=row.get(
                        "dim_customer_key"
                    ),

                    procured_quantity=quantity,

                    unit_selling_price=price,

                    total_discount_amount=discount,

                    product_id=product_id,

                    total_weighted_landing_price=
                        parse_float(
                            row.get(
                                "total_weighted_landing_price"
                            )
                        ),
                )

                batch.append(
                    transaction
                )

                valid_rows += 1

         

            if len(batch) >= BATCH_SIZE:

                db.add_all(batch)

                db.flush()

                batch.clear()

     

        if batch:

            db.add_all(batch)

            db.flush()

            batch.clear()

 

        validation_checks = [

            (
                "required_columns",
                "PASS",
                "All required columns are present.",
            ),

            (
                "date_validation",

                (
                    "PASS"
                    if missing_dates == 0
                    and invalid_dates == 0
                    else "FAIL"
                ),

                (
                    f"Missing dates: {missing_dates}; "
                    f"Invalid dates: {invalid_dates}"
                ),
            ),

            (
                "product_id_validation",

                (
                    "PASS"
                    if missing_product_ids == 0
                    and invalid_product_ids == 0
                    and unmatched_product_ids == 0
                    else "FAIL"
                ),

                (
                    f"Missing: {missing_product_ids}; "
                    f"Invalid: {invalid_product_ids}; "
                    f"Unmatched: "
                    f"{unmatched_product_ids}"
                ),
            ),

            (
                "quantity_validation",

                (
                    "PASS"
                    if missing_quantity == 0
                    and invalid_quantity == 0
                    and negative_quantity == 0
                    else "FAIL"
                ),

                (
                    f"Missing: {missing_quantity}; "
                    f"Invalid: {invalid_quantity}; "
                    f"Negative: {negative_quantity}"
                ),
            ),

            (
                "price_validation",

                (
                    "PASS"
                    if missing_price == 0
                    and invalid_price == 0
                    and negative_price == 0
                    else "FAIL"
                ),

                (
                    f"Missing: {missing_price}; "
                    f"Invalid: {invalid_price}; "
                    f"Negative: {negative_price}"
                ),
            ),

            (
                "discount_validation",

                (
                    "PASS"
                    if missing_discount == 0
                    and invalid_discount == 0
                    and negative_discount == 0
                    else "FAIL"
                ),

                (
                    f"Missing: {missing_discount}; "
                    f"Invalid: {invalid_discount}; "
                    f"Negative: {negative_discount}"
                ),
            ),

            (
                "duplicate_validation",

                (
                    "PASS"
                    if duplicate_rows == 0
                    else "WARNING"
                ),

                f"Duplicate rows: {duplicate_rows}",
            ),
        ]

  

        for (
            check_name,
            check_status,
            details,
        ) in validation_checks:

            db.add(
                ValidationResult(
                    upload_id=upload_job.id,
                    check_name=check_name,
                    status=check_status,
                    details=details,
                )
            )

       

        upload_job.total_rows = total_rows

        upload_job.processed_rows = valid_rows

        if valid_rows > 0:

            upload_job.status = "COMPLETED"

        else:

            upload_job.status = "FAILED"

            upload_job.error_summary = (
                "No valid sales rows were found."
            )

        upload_job.completed_at = datetime.utcnow()

        db.commit()



        return {

            "upload_id":
                upload_job.id,

            "filename":
                upload_job.filename,

            "status":
                upload_job.status,

            "total_rows":
                total_rows,

            "valid_rows":
                valid_rows,

            "invalid_rows":
                total_rows - valid_rows,

            "validation": {

                "missing_dates":
                    missing_dates,

                "invalid_dates":
                    invalid_dates,

                "missing_product_ids":
                    missing_product_ids,

                "invalid_product_ids":
                    invalid_product_ids,

                "unmatched_product_ids":
                    unmatched_product_ids,

                "missing_quantity":
                    missing_quantity,

                "invalid_quantity":
                    invalid_quantity,

                "negative_quantity":
                    negative_quantity,

                "missing_price":
                    missing_price,

                "invalid_price":
                    invalid_price,

                "negative_price":
                    negative_price,

                "missing_discount":
                    missing_discount,

                "invalid_discount":
                    invalid_discount,

                "negative_discount":
                    negative_discount,

                "duplicate_rows":
                    duplicate_rows,
            },

            "unmatched_product_ids_sample":
                sorted(
                    unmatched_products
                )[:20],
        }


    except HTTPException:

        raise


    except Exception as error:

        db.rollback()

        upload_job.status = "FAILED"

        upload_job.error_summary = str(
            error
        )

        db.commit()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Sales upload failed: {error}"
            ),
        )




@router.get("/uploads")
def get_uploads(
    db: Session = Depends(get_db),
):

    uploads = (
        db.query(UploadJob)
        .order_by(
            UploadJob.created_at.desc()
        )
        .all()
    )

    return {

        "total":
            len(uploads),

        "uploads": [

            {
                "id":
                    upload.id,

                "filename":
                    upload.filename,

                "file_type":
                    upload.file_type,

                "file_size_bytes":
                    upload.file_size_bytes,

                "status":
                    upload.status,

                "total_rows":
                    upload.total_rows,

                "processed_rows":
                    upload.processed_rows,

                "error_summary":
                    upload.error_summary,

                "created_at":
                    upload.created_at,

                "completed_at":
                    upload.completed_at,
            }

            for upload in uploads
        ],
    }




@router.get("/uploads/{upload_id}")
def get_upload(
    upload_id: int,
    db: Session = Depends(get_db),
):

    upload = (
        db.query(UploadJob)
        .filter(
            UploadJob.id == upload_id
        )
        .first()
    )

    if not upload:

        raise HTTPException(
            status_code=404,
            detail="Upload not found.",
        )

    return {

        "id":
            upload.id,

        "filename":
            upload.filename,

        "file_type":
            upload.file_type,

        "file_size_bytes":
            upload.file_size_bytes,

        "status":
            upload.status,

        "total_rows":
            upload.total_rows,

        "processed_rows":
            upload.processed_rows,

        "error_summary":
            upload.error_summary,

        "created_at":
            upload.created_at,

        "completed_at":
            upload.completed_at,
    }



@router.get("/validation/{upload_id}")
def get_validation_results(
    upload_id: int,
    db: Session = Depends(get_db),
):

    upload = (
        db.query(UploadJob)
        .filter(
            UploadJob.id == upload_id
        )
        .first()
    )

    if not upload:

        raise HTTPException(
            status_code=404,
            detail="Upload not found.",
        )

    results = (
        db.query(ValidationResult)
        .filter(
            ValidationResult.upload_id
            == upload_id
        )
        .order_by(
            ValidationResult.id
        )
        .all()
    )

    return {

        "upload_id":
            upload_id,

        "filename":
            upload.filename,

        "status":
            upload.status,

        "validation_results": [

            {
                "id":
                    result.id,

                "check_name":
                    result.check_name,

                "status":
                    result.status,

                "details":
                    result.details,

                "created_at":
                    result.created_at,
            }

            for result in results
        ],
    }