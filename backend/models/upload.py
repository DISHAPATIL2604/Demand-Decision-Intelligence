from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.db.session import Base

class UploadJob(Base):
    __tablename__ = "upload_jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False, default="sales")  # sales, product, inventory
    file_size_bytes = Column(BigInteger, nullable=True)
    status = Column(String(50), nullable=False, default="PENDING", index=True)  # PENDING, VALIDATING, PROCESSING, COMPLETED, FAILED
    total_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    error_summary = Column(Text, nullable=True)
    uploaded_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="upload_jobs")
    validation_results = relationship("ValidationResult", back_populates="upload_job", cascade="all, delete-orphan")
    sales_transactions = relationship("SalesTransaction", back_populates="upload_job")

class ValidationResult(Base):
    __tablename__ = "validation_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    upload_id = Column(Integer, ForeignKey("upload_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    check_name = Column(String(150), nullable=False)
    status = Column(String(50), nullable=False)  # PASS, WARNING, FAIL
    details = Column(Text, nullable=True)  # JSON or descriptive text
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    upload_job = relationship("UploadJob", back_populates="validation_results")
