from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
poem = Table('poem', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('author', VARCHAR),
    Column('title', VARCHAR),
    Column('body', TEXT),
    Column('slug', VARCHAR),
    Column('writing_type', VARCHAR(length=32)),
    Column('votes', INTEGER),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['poem'].drop()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['poem'].create()
