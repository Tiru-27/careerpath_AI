"""Initial persistent CareerPath schema."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("email", sa.String(320), nullable=False), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("display_name", sa.String(120)), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("resumes", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("file_name", sa.String(255), nullable=False), sa.Column("raw_text", sa.Text(), nullable=False), sa.Column("version", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"])
    op.create_table("skill_profiles", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("resume_id", sa.Integer(), sa.ForeignKey("resumes.id"), nullable=False), sa.Column("skill_name", sa.String(120), nullable=False), sa.Column("confidence", sa.Float(), nullable=False), sa.Column("source", sa.String(40), nullable=False))
    op.create_index("ix_skill_profiles_resume_id", "skill_profiles", ["resume_id"])
    op.create_index("ix_skill_profiles_skill_name", "skill_profiles", ["skill_name"])
    op.create_table("career_matches", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("resume_id", sa.Integer(), sa.ForeignKey("resumes.id"), nullable=False), sa.Column("role_slug", sa.String(100), nullable=False), sa.Column("score", sa.Float(), nullable=False), sa.Column("readiness", sa.Float(), nullable=False), sa.Column("explanation", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_career_matches_resume_id", "career_matches", ["resume_id"])
    op.create_index("ix_career_matches_role_slug", "career_matches", ["role_slug"])
    op.create_table("roadmaps", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("resume_id", sa.Integer(), sa.ForeignKey("resumes.id"), nullable=False), sa.Column("role_slug", sa.String(100), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_roadmaps_user_id", "roadmaps", ["user_id"])
    op.create_index("ix_roadmaps_resume_id", "roadmaps", ["resume_id"])
    op.create_table("roadmap_items", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("roadmap_id", sa.Integer(), sa.ForeignKey("roadmaps.id"), nullable=False), sa.Column("position", sa.Integer(), nullable=False), sa.Column("phase", sa.String(120), nullable=False), sa.Column("focus", sa.String(160), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("project_outcome", sa.Text(), nullable=False), sa.Column("completed", sa.Boolean(), nullable=False), sa.Column("completed_at", sa.DateTime()))
    op.create_index("ix_roadmap_items_roadmap_id", "roadmap_items", ["roadmap_id"])


def downgrade() -> None:
    op.drop_table("roadmap_items")
    op.drop_table("roadmaps")
    op.drop_table("career_matches")
    op.drop_table("skill_profiles")
    op.drop_table("resumes")
    op.drop_table("users")
