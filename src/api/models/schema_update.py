# Add these imports and modifications to your existing schema.py

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

# In JobApplication class, add:
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="job_applications")

# In ResumeVersion class, add:
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="resume_versions")

# In Company class, add:
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="companies")

# In ApplicationNote class, add:
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
